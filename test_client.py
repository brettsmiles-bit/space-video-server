import requests
import json

BASE_URL = "http://localhost:5000"

def pretty_print(title, resp):
    print(f"\n=== {title} ===")
    print(f"Status: {resp.status_code}")
    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print("Raw response:")
        print(resp.text)
    print("=" * 50 + "\n")

def main():
    # 1. Health check
    r = requests.get(f"{BASE_URL}/health")
    pretty_print("Health Check", r)

    # 2. Search for images on Pixabay
    r = requests.get(f"{BASE_URL}/search-images?query=space&count=10")
    pretty_print("Search Images", r)

    if r.status_code != 200:
        print("❌ Could not fetch images, stopping.")
        return

    images = r.json().get("data", [])
    if not images:
        print("❌ No images returned, stopping.")
        return

    # 3. Process video with images + audio
    payload = {
        "audio_url": "https://www2.cs.uic.edu/~i101/SoundFiles/gettysburg10.wav",
        "media_urls": images
    }
    r = requests.post(f"{BASE_URL}/process", json=payload, headers={"Content-Type": "application/json"})
    pretty_print("Process Video", r)

    # 4. Show Dropbox video link
    if r.status_code == 200:
        data = r.json().get("data", {})
        video_url = data.get("video_url")
        if video_url:
            print(f"🎬 Your video is ready: {video_url}")

if __name__ == "__main__":
    main()
