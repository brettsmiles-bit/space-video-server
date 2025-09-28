import os
import io
import requests
import feedparser
from flask import Flask, request, jsonify
from moviepy import ImageClip, VideoFileClip, AudioFileClip, concatenate_videoclips

app = Flask(__name__)

# ------------------------------
# Utility: download a file with headers + fallback
# ------------------------------
def download_file(url, dest_path, headers=None):
    try:
        headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        r = requests.get(url, headers=headers, stream=True, timeout=15)
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    except Exception as e:
        raise RuntimeError(f"Failed to download {url} ({e})")

# ------------------------------
# Routes
# ------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "success", "data": {"message": "ok"}}), 200


@app.route("/scrape-news", methods=["GET"])
def scrape_news():
    sources = {
        "NASA": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "ESA": "https://www.esa.int/rssfeed/Our_Activities",
        "Space.com": "https://www.space.com/feeds/all",
        "CNN": "http://rss.cnn.com/rss/edition_space.rss",
        "SpaceX": "https://www.spacex.com/updates/feed/rss.xml"
    }

    results = {}
    for name, url in sources.items():
        try:
            feed = feedparser.parse(url)
            entries = [
                {"title": e.title, "url": e.link}
                for e in feed.entries[:5]
            ]
            results[name] = entries
        except Exception as e:
            results[name] = [{"title": f"Error: {e}", "url": url}]
    return jsonify({"status": "success", "data": results}), 200


@app.route("/process", methods=["POST"])
def process():
    data = request.get_json(force=True)
    audio_url = data.get("audio_url")
    media_urls = data.get("media_urls", [])

    if not audio_url or not media_urls:
        return jsonify({"status": "error", "error": "audio_url and media_urls are required"}), 400

    # Download audio
    audio_path = "/tmp/audio.wav"
    try:
        download_file(audio_url, audio_path)
    except Exception as e:
        return jsonify({"status": "error", "error": f"Failed to download audio: {e}"}), 400

    # Download media (images/videos)
    clips = []
    for i, url in enumerate(media_urls):
        dest = f"/tmp/media_{i}.jpg"
        try:
            download_file(url, dest)
            clip = ImageClip(dest).set_duration(5)
            clips.append(clip)
        except Exception as e:
            return jsonify({"status": "error", "error": f"Failed to download/process media: {url} ({e})"}), 400

    # Concatenate video
    try:
        video = concatenate_videoclips(clips, method="compose")
        audio = AudioFileClip(audio_path)
        video = video.set_audio(audio)

        output_path = "/tmp/output.mp4"
        video.write_videofile(output_path, codec="libx264", audio_codec="aac", fps=24)

        return jsonify({"status": "success", "data": {"message": "Video processed successfully", "output": "/tmp/output.mp4"}}), 200
    except Exception as e:
        return jsonify({"status": "error", "error": f"Failed to process video: {e}"}), 500


# ------------------------------
# Main entrypoint for Render
# ------------------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
