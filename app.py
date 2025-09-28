import os
import requests
import feedparser
from flask import Flask, jsonify, request
from dotenv import load_dotenv
from moviepy import ImageClip, VideoFileClip, AudioFileClip, concatenate_videoclips

# Load environment variables
load_dotenv()

app = Flask(__name__)

# -------------------------------
# 🔹 GLOBAL CONFIG
# -------------------------------
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0 Safari/537.36"
}

# Updated RSS Feeds
SOURCES = {
    "NASA": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
    "ESA": "https://www.esa.int/rssfeed/Our_Activities",
    "CNN": "https://rss.cnn.com/rss/cnn_space.rss",
    "Space.com": "https://www.space.com/feeds/all"
    # Blue Origin skipped (they block scrapers)
    # SpaceX has no official feed
}

CACHE = {}

# -------------------------------
# 🔹 ROUTES
# -------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "success", "data": {"message": "ok"}}), 200


@app.route("/scrape-news", methods=["GET"])
def scrape_news():
    """Scrape space news from RSS feeds with caching."""
    news_data = {}
    for source, url in SOURCES.items():
        try:
            if source in CACHE:
                news_data[source] = CACHE[source]
                continue

            feed = feedparser.parse(requests.get(url, headers=HEADERS, timeout=10).content)
            articles = [
                {"title": entry.get("title", "No title"),
                 "url": entry.get("link", "#")}
                for entry in feed.entries[:5]
            ]

            CACHE[source] = articles
            news_data[source] = articles

        except Exception as e:
            news_data[source] = [{"title": f"Error: {e}", "url": url}]

    return jsonify({"status": "success", "data": news_data}), 200


@app.route("/clear-cache", methods=["POST"])
def clear_cache():
    """Clear cached feed results."""
    source = request.json.get("source") if request.is_json else None
    if source:
        if source in CACHE:
            CACHE.pop(source, None)
            return jsonify({"status": "success", "data": {"message": f"Cache cleared for {source}"}})
        return jsonify({"status": "error", "error": f"No cache found for {source}"}), 404

    CACHE.clear()
    return jsonify({"status": "success", "data": {"message": "Cache cleared for all sources"}})


@app.route("/process-video", methods=["POST"])
def process_video():
    """
    Create a video from images and audio.
    JSON payload: {"images": ["url1", "url2"], "audio": "audiourl"}
    """
    data = request.json
    images = data.get("images", [])
    audio_url = data.get("audio")

    if not images:
        return jsonify({"status": "error", "error": "No images provided"}), 400

    # Download audio
    audio_file = "temp_audio.mp3"
    try:
        if audio_url:
            resp = requests.get(audio_url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            with open(audio_file, "wb") as f:
                f.write(resp.content)
        else:
            # Fallback: generate 1 second silent audio
            import wave, struct
            with wave.open(audio_file, "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(44100)
                wf.writeframes(struct.pack("<h", 0) * 44100)

        audio_clip = AudioFileClip(audio_file)

        # Create video from images
        clips = []
        for img_url in images:
            img_data = requests.get(img_url, headers=HEADERS, timeout=10)
            img_path = "temp_img.jpg"
            with open(img_path, "wb") as f:
                f.write(img_data.content)

            clip = ImageClip(img_path).set_duration(3)
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose").set_audio(audio_clip)
        output_file = "output.mp4"
        video.write_videofile(output_file, codec="libx264", fps=24)

        return jsonify({"status": "success", "data": {"message": "Video processed", "file": output_file}})

    except Exception as e:
        return jsonify({"status": "error", "error": f"Failed to process video: {e}"}), 400


# -------------------------------
# 🔹 MAIN
# -------------------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
