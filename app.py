import os
from flask import Flask, request, jsonify
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
import requests
import tempfile

app = Flask(__name__)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "success", "data": {"message": "ok"}})

@app.route("/process", methods=["POST"])
def process():
    data = request.get_json(force=True)
    audio_url = data.get("audio_url")
    media_urls = data.get("media_urls", [])

    if not media_urls:
        return jsonify({"status": "error", "error": "No media URLs provided"}), 400

    try:
        # Download audio
        audio_path = download_file(audio_url, suffix=".wav")

        # Download images
        clips = []
        for url in media_urls:
            img_path = download_file(url, suffix=".jpg")
            clip = ImageClip(img_path).set_duration(3)
            clips.append(clip)

        video = concatenate_videoclips(clips, method="compose")

        # Add audio
        if audio_path:
            audio = AudioFileClip(audio_path)
            video = video.set_audio(audio)

        # Save to temp file
        tmp_video = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        tmp_video_path = tmp_video.name
        tmp_video.close()

        video.write_videofile(tmp_video_path, codec="libx264", audio_codec="aac")

        return jsonify({"status": "success", "data": {"video_path": tmp_video_path}})

    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

def download_file(url, suffix=""):
    """Download a file from URL and return the local path."""
    if not url:
        return None

    resp = requests.get(url, stream=True, timeout=30, headers={
        "User-Agent": "Mozilla/5.0"
    })
    resp.raise_for_status()

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    with open(tmp.name, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    return tmp.name

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))  # ✅ Render uses $PORT
    app.run(host="0.0.0.0", port=port)
