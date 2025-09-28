import os
import requests
import feedparser
from flask import Flask, jsonify
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from dotenv import load_dotenv
from dateutil import parser as date_parser

load_dotenv()

app = Flask(__name__)

# ---------- Helper function for RSS scraping ----------
def scrape_rss_feed(url, source):
    try:
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries[:5]:  # limit to latest 5
            results.append({
                "headline_title": entry.get("title", "No title"),
                "published": entry.get("published", ""),
                "source": source,
                "url": entry.get("link", "")
            })
        return results
    except Exception as e:
        return [{
            "headline_title": f"Error: {str(e)}",
            "published": "",
            "source": source,
            "url": url
        }]

# ---------- Routes ----------
@app.route("/")
def home():
    return jsonify({"status": "success", "data": {"message": "Server is running"}})

@app.route("/health")
def health():
    return jsonify({"status": "success", "data": {"message": "ok"}})

@app.route("/scrape-news")
def scrape_news():
    feeds = {
        "CNN": "https://rss.cnn.com/rss/cnn_space.rss",
        "NASA": "https://www.nasa.gov/rss/dyn/breaking_news.rss",
        "ESA": "https://www.esa.int/rssfeed/Our_Activities",
        "Space.com": "https://www.space.com/feeds/all"
    }

    results = []
    for source, url in feeds.items():
        results.extend(scrape_rss_feed(url, source))

    # Sort by date if available
    def parse_date(entry):
        try:
            return date_parser.parse(entry["published"])
        except Exception:
            return None

    results = sorted(
        results,
        key=lambda x: parse_date(x) or "",
        reverse=True
    )

    return jsonify({"status": "success", "data": results})

# ---------- Main ----------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
