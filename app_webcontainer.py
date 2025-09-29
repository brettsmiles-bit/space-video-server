#!/usr/bin/env python3
"""
WebContainer-compatible Flask app that simulates space news scraping
Uses only Python standard library modules
"""
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta
import random

class SpaceNewsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == '/health':
            self.send_health_response()
        elif path == '/scrape-news':
            self.send_news_response()
        elif path == '/':
            self.send_home_response()
        else:
            self.send_error(404, "Not Found")
    
    def send_health_response(self):
        response = {
            "status": "success",
            "data": {"message": "ok"}
        }
        self.send_json_response(response)
    
    def send_home_response(self):
        response = {
            "status": "success",
            "data": {"message": "Server is running"}
        }
        self.send_json_response(response)
    
    def send_news_response(self):
        # Simulate real space news data
        news_items = [
            {
                "headline_title": "NASA's Artemis Program Reaches Critical Milestone in Lunar Mission Preparation",
                "published": (datetime.now() - timedelta(hours=2)).isoformat(),
                "source": "NASA",
                "url": "https://www.nasa.gov/artemis"
            },
            {
                "headline_title": "SpaceX Successfully Launches Advanced Starlink Satellite Constellation",
                "published": (datetime.now() - timedelta(hours=4)).isoformat(),
                "source": "SpaceX",
                "url": "https://www.spacex.com/starlink"
            },
            {
                "headline_title": "James Webb Space Telescope Discovers Potentially Habitable Exoplanet",
                "published": (datetime.now() - timedelta(hours=6)).isoformat(),
                "source": "ESA",
                "url": "https://www.esa.int/webb"
            },
            {
                "headline_title": "International Space Station Conducts Groundbreaking Microgravity Experiments",
                "published": (datetime.now() - timedelta(hours=8)).isoformat(),
                "source": "Space.com",
                "url": "https://www.space.com/iss"
            },
            {
                "headline_title": "Mars Rover Perseverance Makes Significant Discovery in Ancient River Delta",
                "published": (datetime.now() - timedelta(hours=12)).isoformat(),
                "source": "NASA",
                "url": "https://www.nasa.gov/mars"
            }
        ]
        
        # Add some randomization to make it feel more real
        selected_news = random.sample(news_items, min(4, len(news_items)))
        
        response = {
            "status": "success",
            "data": selected_news
        }
        self.send_json_response(response)
    
    def send_json_response(self, data, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        json_data = json.dumps(data, indent=2)
        self.wfile.write(json_data.encode('utf-8'))
    
    def log_message(self, format, *args):
        # Suppress default logging to keep output clean
        pass

def run_server(port=5000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, SpaceNewsHandler)
    
    print(f"🚀 Space News Server starting on port {port}")
    print(f"📡 Health check: http://localhost:{port}/health")
    print(f"📰 News endpoint: http://localhost:{port}/scrape-news")
    print("Press Ctrl+C to stop the server")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.server_close()

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    run_server(port)