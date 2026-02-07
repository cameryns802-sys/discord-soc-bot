#!/usr/bin/env python3
"""
Discord SOC Bot - 24/7 Process Manager
Keeps the bot running continuously even if it crashes.
Handles automatic restarts with exponential backoff.
"""

import subprocess
import sys
import time
import os
from datetime import datetime
import signal

class BotManager:
    def __init__(self):
        self.bot_process = None
        self.restart_count = 0
        self.max_retries = 5
        self.base_delay = 5  # Start with 5 second delay
        self.running = True
        
        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, self.signal_handler)
    
    def signal_handler(self, sig, frame):
        """Handle Ctrl+C gracefully"""
        print("\n[MANAGER] Shutting down gracefully...")
        self.running = False
        if self.bot_process:
            self.bot_process.terminate()
            try:
                self.bot_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.bot_process.kill()
        sys.exit(0)
    
    def log(self, message):
        """Log with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}", flush=True)
    
    def run(self):
        """Run the bot with auto-restart"""
        self.log("🤖 Discord SOC Bot Process Manager Started")
        self.log(f"📂 Working Directory: {os.getcwd()}")
        self.log("=" * 70)
        
        while self.running:
            try:
                self.restart_count += 1
                
                if self.restart_count > 1:
                    self.log(f"🔄 Restart #{self.restart_count} (total restarts: {self.restart_count - 1})")
                else:
                    self.log(f"🚀 Starting bot (attempt #{self.restart_count})")
                
                # Start bot process
                self.bot_process = subprocess.Popen(
                    [sys.executable, "bot.py"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                # Print bot output in real-time
                for line in self.bot_process.stdout:
                    print(line.rstrip())
                
                # Wait for process to complete
                return_code = self.bot_process.wait()
                
                if return_code == 0:
                    self.log("✅ Bot exited cleanly")
                    break
                else:
                    self.log(f"⚠️ Bot crashed with code {return_code}")
                
            except KeyboardInterrupt:
                self.log("⏹️ Keyboard interrupt received")
                break
            except Exception as e:
                self.log(f"❌ Error: {e}")
            
            # Calculate delay before restart (exponential backoff)
            if self.running and self.restart_count < self.max_retries:
                delay = min(self.base_delay * (2 ** (self.restart_count - 1)), 60)
                self.log(f"⏳ Waiting {delay:.0f} seconds before restart...")
                time.sleep(delay)
            elif self.running:
                self.log("❌ Max retries exceeded. Stopping.")
                break
        
        self.log("=" * 70)
        self.log("🛑 Process Manager Stopped")

if __name__ == "__main__":
    manager = BotManager()
    manager.run()
