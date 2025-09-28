from flask import Flask, request, jsonify
import os
import requests
import tempfile
import feedparser
import time
import datetime
import shutil
import wave
from bs4 import BeautifulSoup
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

app = Flask(__name__)

DROPBOX_TOKEN = os.getenv("DROPBOX_TOKEN")
PIXABAY_KEY = os.getenv("PIXABAY_KEY")

CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "3600"))  # default 1h
CLIP_DURATION = int(os.getenv("CLIP_DURATION", "3"))     # default 3s per image

# ------------------------
# Utility: Download file (with headers + silent audio fallback)
# ------------------------
def download_file(url, filename):
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Referer": "https://pixabay.com/"
    }

    try:
        if url.startswith("http://") or url.startswith("https://"):
            r = requests.get(url, headers=headers, stream=True, timeout=15)
            r.raise_for_status()
            with open(filename, "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
        else:
            if not os.path.exists(url):
                raise ValueError(f"Local file not found: {url}")
            shutil.copy(url, filename)
    except Exception as e:
        if filename.endswith(".wav"):
            with wave.open(filename, "w") as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(44100)
                wf.writeframes(b'\x00\x00' * 44100)  # 1s silence
            print(f"[WARN] Audio download failed ({url}) → using silent fallback")
        else:
            raise ValueError(f"Failed to download {url} ({str(e)})")

# ------------------------
# Utility: Upload to Dropbox
# ------------------------
def upload_to_dropbox(local_path, dropbox_filename):
    if not DROPBOX_TOKEN:
        raise ValueError("Missing Dropbox token")

    with open(local_path, "rb") as f:
        headers = {
            "Authorization": f"Bearer {DROPBOX_TOKEN}",
            "Content-Type": "application/octet-stream",
            "Dropbox-API-Arg": str(
                {"path": f"/{dropbox_filename}", "mode": "overwrite"}
            ).replace("'", '"')
        }
        r = requests.post(
            "https://content.dropboxapi.com/2/files/upload",
            headers=headers,
            data=f
        )
        r.raise_for_status()

    link_headers = {
        "Authorization": f"Bearer {DROPBOX_TOKEN}",
        "Content-Type": "application/json"
    }
    res = requests.post(
        "https://api.dropboxapi.com/2/sharing/create_shared_link_with_settings",
        headers=link_headers,
        json={"path": f"/{dropbox_filename}"}
    )
    res.raise_for_status()
    return res.json()["url"]

# ------------------------
# Endpoint: Health Check
# ------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "success", "data": {"message": "ok"}}), 200

# ------------------------
# Scrape News with caching
# ------------------------
news_cache = {}

def get_sources():
    sources = []
    if os.getenv("ENABLE_NASA", "true").lower() == "true":
        sources.append(("NASA", "https://www.nasa.gov/rss/dyn/breaking_news.rss", True))
    if os.getenv("ENABLE_SPACECOM", "true").lower() == "true":
        sources.append(("Space.com", "https://www.space.com/feeds/all", True))
    if os.getenv("ENABLE_ESA", "true").lower() == "true":
        sources.append(("ESA", "https://www.esa.int/rssfeed/Our_Activities", True))
    if os.getenv("ENABLE_SPACEX", "true").lower() == "true":
        sources.append(("SpaceX", "https://www.spacex.com/updates/", False))
    if os.getenv("ENABLE_CNN", "true").lower() == "true":
        sources.append(("CNN", "http://rss.cnn.com/rss/edition_space.rss", True))
    return sources

@app.route("/scrape-news", methods=["GET"])
def scrape_news():
    sources = get_sources()
    results = {}
    browser_headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
    }

    refresh = request.args.get("refresh", "false").lower() == "true"
    now = datetime.datetime.now()

    for source, url, is_rss in sources:
        source_headlines = []

        if not refresh and source in news_cache:
            cached = news_cache[source]
            if (now - cached["timestamp"]).seconds < CACHE_TTL:
                results[source] = cached["headlines"]
                continue

        try:
            if is_rss:
                feed = feedparser.parse(url)
                if getattr(feed, "bozo", False) and not feed.entries:
                    raise ValueError("Could not parse RSS feed")
                for entry in feed.entries[:5]:
                    link = getattr(entry, "link", None)
                    if not link and getattr(entry, "links", None):
                        link = entry.links[0].href
                    source_headlines.append({
                        "title": getattr(entry, "title", "No title"),
                        "url": link or url
                    })
            else:
                r = requests.get(url, headers=browser_headers, timeout=10)
                r.raise_for_status()
                soup = BeautifulSoup(r.text, "lxml")
                if source == "SpaceX":
                    for h2 in soup.find_all("h2")[:5]:
                        a = h2.find("a")
                        if a and a.text.strip():
                            source_headlines.append({
                                "title": a.text.strip(),
                                "url": a["href"] if a.has_attr("href") else url
                            })
                if not source_headlines:
                    title_tag = soup.find("title")
                    title = title_tag.text.strip() if title_tag else f"Fetched page: {url}"
                    source_headlines.append({"title": title, "url": url})

        except Exception as e:
            source_headlines.append({"title": f"Error: {str(e)}", "url": url})

        while len(source_headlines) < 5:
            source_headlines.append({"title": "No data", "url": url})
        source_headlines = source_headlines[:5]

        news_cache[source] = {"timestamp": now, "headlines": source_headlines}
        results[source] = source_headlines
        time.sleep(1)

    return jsonify({"status": "success", "data": results})

# ------------------------
# Cache Clear
# ------------------------
@app.route("/cache/clear", methods=["POST"])
def clear_cache():
    global news_cache
    source = request.args.get("source")

    if source:
        if source in news_cache:
            del news_cache[source]
            return jsonify({"status": "success", "data": {"message": f"Cache cleared for {source}"}}), 200
        else:
            return jsonify({"status": "error", "error": f"No cache found for {source}"}), 404
    else:
        news_cache = {}
        return jsonify({"status": "success", "data": {"message": "Cache cleared for all sources"}}), 200

# ------------------------
# Search Images (Pixabay API)
# ------------------------
@app.route("/search-images", methods=["GET"])
def search_images():
    if not PIXABAY_KEY:
        return jsonify({"status": "error", "error": "Missing PIXABAY_KEY in environment"}), 500

    query = request.args.get("query", "space")
    count = int(request.args.get("count", "5"))

    url = f"https://pixabay.com/api/?key={PIXABAY_KEY}&q={query}&image_type=photo&per_page={count}"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        results = [hit["largeImageURL"] for hit in data.get("hits", [])]
        return jsonify({"status": "success", "data": results})
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

# ------------------------
# Process Video
# ------------------------
@app.route("/process", methods=["POST"])
def process():
    try:
        data = request.get_json()
        audio_url = data.get("audio_url")
        media_urls = data.get("media_urls", [])

        if not audio_url or not media_urls:
            return jsonify({"status": "error", "error": "Missing audio_url or media_urls"}), 400

        with tempfile.TemporaryDirectory() as tmpdir:
            audio_path = os.path.join(tmpdir, "audio.wav")
            clips = []

            try:
                download_file(audio_url, audio_path)
            except Exception as e:
                return jsonify({"status": "error", "error": f"Audio handling failed: {str(e)}"}), 400

            for i, url in enumerate(media_urls):
                try:
                    filename = os.path.join(tmpdir, f"clip_{i}.jpg")
                    download_file(url, filename)
                    clip = ImageClip(filename, duration=CLIP_DURATION)
                    clips.append(clip)
                except Exception as e:
                    return jsonify({"status": "error", "error": f"Failed to download/process media: {url} ({str(e)})"}), 400

            if not clips:
                return jsonify({"status": "error", "error": "No valid media clips"}), 400

            final_video = concatenate_videoclips(clips)
            audio = AudioFileClip(audio_path)
            final_video = final_video.set_audio(audio)

            output_path = os.path.join(tmpdir, "final_video.mp4")
            final_video.write_videofile(output_path, fps=24)

            try:
                dropbox_link = upload_to_dropbox(output_path, "final_video.mp4")
            except Exception as e:
                return jsonify({"status": "error", "error": f"Dropbox upload failed: {str(e)}"}), 500

        return jsonify({"status": "success", "data": {"video_url": dropbox_link}})

    except Exception as e:
        return jsonify({"status": "error", "error": f"Unexpected error: {str(e)}"}), 500

# ------------------------
# Main entry with banner
# ------------------------
if __name__ == "__main__":
    print("🚀 Space Video API server is starting...")
    print("Available endpoints:")
    print("  ➤ GET  /health")
    print("  ➤ GET  /scrape-news?refresh=true")
    print("  ➤ GET  /search-images?query=space&count=5")
    print("  ➤ POST /cache/clear   (?source=NAME optional)")
    print("  ➤ POST /process")
    print(f"\nCache TTL: {CACHE_TTL} seconds")
    print(f"Clip duration: {CLIP_DURATION} seconds")
    print("\nEnabled sources:")
    for src, _, _ in get_sources():
        print(f"  ✔ {src}")
    if PIXABAY_KEY:
        print("  ✔ Pixabay integration enabled")
    else:
        print("  ✘ Pixabay disabled (no API key)")
    app.run(host="0.0.0.0", port=5000)
