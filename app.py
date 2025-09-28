import os
import requests
import feedparser
from flask import Flask, request, jsonify
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from dotenv import load_dotenv
import tempfile

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Pixabay & Dropbox API keys
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")

# Fake browser headers (helps with 403/429)
BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/117.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

# RSS Feeds
NEWS_SOURCES = {
    "CNN": "https://rss.cnn.com/rss/cnn_space.rss",
    "NASA": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "ESA": "https://www.esa.int/rssfeed/Our_Activities",
    "Space.com": "https://www.space.com/feeds/all",
    # "SpaceX": handled separately since no RSS feed
}


# ----------------------
# 🔹 Helpers
# ----------------------
def fetch_rss(url):
    """Fetch and parse RSS feed via feedparser."""
    try:
        feed = feedparser.parse(url)
        if feed.bozo:
            raise Exception(feed.bozo_exception)
        return [{"title": e.title, "url": e.link} for e in feed.entries[:5]]
    except Exception as e:
        return [{"title": f"Error: {e}", "url": url}]


def download_file(url, path, is_audio=False):
    """Download file with fallback for silent audio."""
    try:
        resp = requests.get(url, headers=BROWSER_HEADERS, stream=True, timeout=15)
        resp.raise_for_status()
        with open(path, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
    except Exception as e:
        if is_audio:
            # fallback: 1-second silent WAV
            from pydub import AudioSegment
            silent = AudioSegment.silent(duration=1000)
            silent.export(path, format="wav")
        else:
            raise Exception(f"Failed to download {url} ({e})")


def upload_to_dropbox(file_path, dest_path):
    """Upload a file to Dropbox."""
    with open(file_path, "rb") as f:
        resp = requests.post(
            "https://content.dropboxapi.com/2/files/upload",
            headers={
                "Authorization": f"Bearer {DROPBOX_TOKEN}",
                "Dropbox-API-Arg": f'{{"path": "{dest_path}", "mode": "overwrite"}}',
                "Content-Type": "application/octet-stream",
            },
            data=f,
        )
    resp.raise_for_status()
    return dest_path


# ----------------------
# 🔹 Routes
# ----------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "success", "data": {"message": "ok"}})


@app.route("/scrape-news", methods=["GET"])
def scrape_news():
    results = {}
    for source, url in NEWS_SOURCES.items():
        items = fetch_rss(url)
        results[source] = items

    # Add placeholder for SpaceX
    results["SpaceX"] = [{"title": "Visit SpaceX updates", "url": "https://www.spacex.com/updates/"}]
    return jsonify({"status": "success", "data": results})


@app.route("/search-images", methods=["GET"])
def search_images():
    query = request.args.get("q", "space")
    url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={query}&image_type=photo"
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        hits = resp.json().get("hits", [])
        return jsonify({"status": "success", "data": [h["largeImageURL"] for h in hits[:10]]})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/process", methods=["POST"])
def process():
    try:
        data = request.json
        image_urls = data.get("images", [])
        audio_url = data.get("audio")

        if not image_urls or not audio_url:
            return jsonify({"status": "error", "error": "Missing images or audio"}), 400

        clips = []
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = os.path.join(tmpdir, "audio.wav")
            download_file(audio_url, audio_path, is_audio=True)
            audio = AudioFileClip(audio_path)

            # Distribute audio duration across images
            img_duration = audio.duration / len(image_urls)

            for idx, img_url in enumerate(image_urls):
                img_path = os.path.join(tmpdir, f"img{idx}.jpg")
                download_file(img_url, img_path)
                clip = ImageClip(img_path).set_duration(img_duration)
                clips.append(clip)

            video = concatenate_videoclips(clips, method="compose").set_audio(audio)

            output_path = os.path.join(tmpdir, "output.mp4")
            video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")

            # Upload to Dropbox
            dropbox_path = f"/output_{os.urandom(4).hex()}.mp4"
            uploaded = upload_to_dropbox(output_path, dropbox_path)

        return jsonify({"status": "success", "data": {"dropbox_path": uploaded}})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


# ----------------------
# 🔹 Entry Point
# ----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render uses $PORT
    app.run(host="0.0.0.0", port=port)
