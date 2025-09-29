#!/usr/bin/env node

import SpacePipeline from './pipeline.js';
import fs from 'fs';

class VideoScheduler {
  constructor() {
    this.lastRunFile = 'last_run.json';
  }

  saveLastRun(results) {
    const runInfo = {
      timestamp: new Date().toISOString(),
      status: results.status,
      duration: results.total_duration_seconds,
      video_url: results.final_outputs?.video_url
    };
    
    fs.writeFileSync(this.lastRunFile, JSON.stringify(runInfo, null, 2));
  }

  getLastRunInfo() {
    try {
      const data = fs.readFileSync(this.lastRunFile, 'utf8');
      return JSON.parse(data);
    } catch (error) {
      return null;
    }
  }

  shouldRunNow() {
    const lastRun = this.getLastRunInfo();
    if (!lastRun) return true;
    
    const lastRunTime = new Date(lastRun.timestamp);
    const timeSinceLast = Date.now() - lastRunTime.getTime();
    const twoHours = 2 * 60 * 60 * 1000; // 2 hours in milliseconds
    
    if (timeSinceLast < twoHours && lastRun.status === 'completed') {
      console.log(`Skipping run - last successful run was ${Math.round(timeSinceLast / (60 * 1000))} minutes ago`);
      return false;
    }
    
    return true;
  }

  async runScheduledVideoGeneration() {
    console.log('🕐 Scheduled video generation starting...');
    
    if (!this.shouldRunNow()) {
      return;
    }
    
    try {
      const pipeline = new SpacePipeline();
      const results = await pipeline.runPipeline();
      
      this.saveLastRun(results);
      
      if (results.status === 'completed') {
        const videoUrl = results.final_outputs?.video_url;
        console.log('✅ Scheduled video generation completed successfully!');
        if (videoUrl) {
          console.log(`🎬 Video URL: ${videoUrl}`);
        }
      } else {
        console.error('❌ Scheduled video generation failed');
      }
      
    } catch (error) {
      console.error(`Scheduled run failed: ${error.message}`);
    }
  }

  async startScheduler() {
    console.log('🚀 Video generation scheduler started');
    console.log('Running every 4 hours...');
    
    // Run immediately if no recent run
    if (!this.getLastRunInfo()) {
      console.log('No previous runs found, running immediately...');
      await this.runScheduledVideoGeneration();
    }
    
    // Schedule to run every 4 hours (14400000 ms)
    setInterval(async () => {
      await this.runScheduledVideoGeneration();
    }, 4 * 60 * 60 * 1000);
    
    console.log('Scheduler is running. Press Ctrl+C to stop.');
  }
}

async function main() {
  const scheduler = new VideoScheduler();
  await scheduler.startScheduler();
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}

export default VideoScheduler;