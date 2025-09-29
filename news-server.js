#!/usr/bin/env node

import http from 'http';
import { URL } from 'url';

class NewsServer {
  constructor(port = 5000) {
    this.port = port;
    this.server = null;
  }

  generateSpaceNews() {
    const sources = ['NASA', 'CNN', 'ESA', 'Space.com'];
    const headlines = [
      "NASA's Artemis Program Reaches New Milestone in Lunar Exploration",
      "SpaceX Successfully Launches Advanced Satellite Constellation",
      "James Webb Telescope Discovers Most Distant Galaxy Yet",
      "International Space Station Receives New Scientific Equipment",
      "Mars Rover Makes Groundbreaking Discovery in Ancient Crater",
      "European Space Agency Announces New Venus Mission",
      "Private Space Company Achieves Historic Orbital Flight",
      "Astronauts Complete Critical Spacewalk Outside ISS",
      "New Exoplanet Found in Habitable Zone of Nearby Star",
      "Solar Observatory Captures Unprecedented Sun Activity"
    ];

    const news = [];
    const now = new Date();

    for (let i = 0; i < 5; i++) {
      const randomHeadline = headlines[Math.floor(Math.random() * headlines.length)];
      const randomSource = sources[Math.floor(Math.random() * sources.length)];
      const publishTime = new Date(now.getTime() - (i * 3600000)); // Each article 1 hour older

      news.push({
        headline_title: randomHeadline,
        published: publishTime.toISOString(),
        source: randomSource,
        url: `https://example.com/news/${i + 1}`
      });
    }

    return news;
  }

  handleRequest(req, res) {
    // Set CORS headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    res.setHeader('Content-Type', 'application/json');

    const url = new URL(req.url, `http://localhost:${this.port}`);
    const pathname = url.pathname;

    try {
      if (req.method === 'OPTIONS') {
        res.writeHead(200);
        res.end();
        return;
      }

      if (pathname === '/') {
        res.writeHead(200);
        res.end(JSON.stringify({
          status: "success",
          data: { message: "Server is running" }
        }));
      } else if (pathname === '/health') {
        res.writeHead(200);
        res.end(JSON.stringify({
          status: "success",
          data: { message: "ok" }
        }));
      } else if (pathname === '/scrape-news') {
        const newsData = this.generateSpaceNews();
        res.writeHead(200);
        res.end(JSON.stringify({
          status: "success",
          data: newsData
        }));
      } else {
        res.writeHead(404);
        res.end(JSON.stringify({
          status: "error",
          message: "Not found"
        }));
      }
    } catch (error) {
      console.error('Request error:', error);
      res.writeHead(500);
      res.end(JSON.stringify({
        status: "error",
        message: "Internal server error"
      }));
    }
  }

  start() {
    this.server = http.createServer((req, res) => {
      this.handleRequest(req, res);
    });

    this.server.listen(this.port, '0.0.0.0', () => {
      console.log(`🚀 News server running on http://localhost:${this.port}`);
      console.log('Available endpoints:');
      console.log('  GET / - Server status');
      console.log('  GET /health - Health check');
      console.log('  GET /scrape-news - Get space news');
    });

    // Handle server errors
    this.server.on('error', (error) => {
      console.error('Server error:', error);
    });

    return this.server;
  }

  stop() {
    if (this.server) {
      this.server.close();
      console.log('News server stopped');
    }
  }
}

// Start server if run directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const port = process.env.PORT || 5000;
  const server = new NewsServer(port);
  server.start();

  // Graceful shutdown
  process.on('SIGINT', () => {
    console.log('\nShutting down news server...');
    server.stop();
    process.exit(0);
  });
}

export default NewsServer;