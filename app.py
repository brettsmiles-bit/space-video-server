import os
import tempfile
import requests
import feedparser
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Fake browser headers (to avoid 403/429 from some servers)
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

# RSS sources
NEWS_SOURCES = {
    "CNN": "https://rss.cnn.com/rss/cnn_space.rss",
    "NASA": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "ESA": "https://www.esa.int/rssfeed/Our_Activities",
    "Space.com": "https://www.space.com/feeds/all",
    "SpaceX": "https://www.spacex.com/updates/rss.xml",
}

def download_file(url, dest):
    """Download file with headers and save to dest"""
    try:
        r = requests.get(url, headers=BROWSER_HEADERS, timeout=20, stream=True)
        r.raise_for_status()
        with open(dest, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return True
    except Exception as e:
        print(f"❌ Failed to download {url}: {e}")
        return False

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "success", "data": {"message": "ok"}}), 200

@app.route("/scrape-news", methods=["GET"])
def scrape_news():
    results = []

    for source, url in NEWS_SOURCES.items():
        if source == "Blue Origin":  # skip Blue Origin
            continue
        try:
            articles = scrape_rss_feed(url)
            for article in articles[:5]:  # collect top 5 per source
                results.append({
                    "headline_title": article.get("title", "No title"),
                    "source": source,
                    "url": article.get("url", ""),
                    "published": article.get("published", "")  # include date
                })
        except Exception as e:
            results.append({
                "headline_title": f"Error: {e}",
                "source": source,
                "url": url,
                "published": ""
            })

    # sort by published date if available
    def parse_date(item):
        from dateutil import parser
        try:
            return parser.parse(item["published"])
        except Exception:
            return None

    results = sorted(
        results,
        key=lambda x: parse_date(x) or "",
        reverse=True  # newest first
    )

    return jsonify(results)


@app.route("/process", methods=["POST"])
def process():
    data = request.get_json()
    if not data or "media_urls" not in data:
        return jsonify({"status": "error", "error": "Missing media_urls"}), 400

    audio_url = data.get("audio_url")
    media_urls = data["media_urls"]

    # Create temporary workspace
    with tempfile.TemporaryDirectory() as tmpdir:
        # Download audio
        audio_path = os.path.join(tmpdir, "audio.mp3")
        if audio_url:
            if not download_file(audio_url, audio_path):
                return jsonify({
                    "status": "error",
                    "error": f"Failed to download audio: {audio_url}"
                }), 400
        else:
            # fallback silent audio
            from moviepy import AudioClip
            silent = AudioClip(lambda t: 0, duration=5, fps=44100)
            audio_path = os.path.join(tmpdir, "silent.mp3")
            silent.write_audiofile(audio_path)

        # Download media
        clips = []
        for i, url in enumerate(media_urls):
            img_path = os.path.join(tmpdir, f"img{i}.jpg")
            if not download_file(url, img_path):
                return jsonify({
                    "status": "error",
                    "error": f"Failed to download/process media: {url}"
                }), 400
            try:
                clip = ImageClip(img_path).set_duration(5)
                clips.append(clip)
            except Exception as e:
                return jsonify({
                    "status": "error",
                    "error": f"Failed to process {url}: {e}"
                }), 400

        if not clips:
            return jsonify({"status": "error", "error": "No valid media clips"}), 400

        # Combine video
        video = concatenate_videoclips(clips, method="compose")
        video = video.set_audio(AudioFileClip(audio_path))

        out_path = os.path.join(tmpdir, "output.mp4")
        video.write_videofile(out_path, codec="libx264", fps=24)

        return jsonify({"status": "success", "data": {"message": "Video generated"}}), 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
