# File: client_tracker.py
# This script runs on client computers to track keyboard and mouse activity

import time
import socket
import json
import datetime
import platform
import threading
import queue
from pynput import keyboard, mouse
import requests

class ActivityTracker:
    def __init__(self, server_url, user_id, device_id, flush_interval=60):
        self.server_url = server_url
        self.user_id = user_id
        self.device_id = device_id
        self.flush_interval = flush_interval
        
        # Setup data structures
        self.event_queue = queue.Queue()
        self.key_count = 0
        self.click_count = 0
        self.last_activity = time.time()
        
        # Setup system info
        self.system_info = {
            "os": platform.system(),
            "os_version": platform.version(),
            "hostname": socket.gethostname(),
            "device_id": device_id,
            "user_id": user_id
        }
        
        # Setup listeners
        self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
        
        # For data sending
        self.running = False
        self.sender_thread = None
    
    def on_key_press(self, key):
        """Callback for keyboard press events"""
        self.key_count += 1
        self.last_activity = time.time()
        
        # Enqueue event
        event = {
            "type": "keyboard",
            "timestamp": datetime.datetime.now().isoformat(),
            "data": {
                "count": 1
            }
        }
        self.event_queue.put(event)
    
    def on_mouse_click(self, x, y, button, pressed):
        """Callback for mouse click events"""
        if pressed:
            self.click_count += 1
            self.last_activity = time.time()
            
            # Enqueue event
            event = {
                "type": "mouse",
                "timestamp": datetime.datetime.now().isoformat(),
                "data": {
                    "count": 1,
                    "position": {"x": x, "y": y},
                    "button": str(button)
                }
            }
            self.event_queue.put(event)
    
    def send_data(self):
        """Send collected data to server"""
        while self.running:
            events = []
            # Collect all events from queue
            try:
                while len(events) < 100:  # Limit batch size
                    event = self.event_queue.get(block=True, timeout=self.flush_interval)
                    events.append(event)
            except queue.Empty:
                pass  # Timeout occurred, send what we have
            
            # If we have events to send
            if events:
                payload = {
                    "system_info": self.system_info,
                    "timestamp": datetime.datetime.now().isoformat(),
                    "events": events,
                    "summary": {
                        "key_count": self.key_count,
                        "click_count": self.click_count,
                        "last_activity": datetime.datetime.fromtimestamp(self.last_activity).isoformat()
                    }
                }
                
                try:
                    response = requests.post(
                        f"{self.server_url}/api/activity",
                        json=payload,
                        headers={"Content-Type": "application/json"}
                    )
                    if response.status_code != 200:
                        print(f"Error sending data: {response.status_code}")
                        # Put events back in queue
                        for event in events:
                            self.event_queue.put(event)
                except Exception as e:
                    print(f"Exception sending data: {e}")
                    # Put events back in queue
                    for event in events:
                        self.event_queue.put(event)
    
    def start(self):
        """Start the tracking"""
        if self.running:
            return
        
        self.running = True
        
        # Start listeners
        self.keyboard_listener.start()
        self.mouse_listener.start()
        
        # Start sender thread
        self.sender_thread = threading.Thread(target=self.send_data)
        self.sender_thread.daemon = True
        self.sender_thread.start()
        
        print("Activity tracking started")
    
    def stop(self):
        """Stop the tracking"""
        if not self.running:
            return
        
        self.running = False
        
        # Stop listeners
        self.keyboard_listener.stop()
        self.mouse_listener.stop()
        
        # Wait for sender thread to finish
        if self.sender_thread:
            self.sender_thread.join(timeout=5)
        
        print("Activity tracking stopped")

if __name__ == "__main__":
    import configparser
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Activity Tracker Client')
    parser.add_argument('--config', type=str, default='config.ini', help='Path to config file')
    parser.add_argument('--server', type=str, help='Server URL')
    parser.add_argument('--user', type=str, help='User ID')
    parser.add_argument('--device', type=str, help='Device ID')
    args = parser.parse_args()
    
    # Load config
    config = configparser.ConfigParser()
    try:
        config.read(args.config)
    except:
        print(f"Warning: Could not read config file {args.config}")
    
    # Set parameters with priority: command line > config file > defaults
    server_url = args.server or config.get('Server', 'url', fallback='http://localhost:5000')
    user_id = args.user or config.get('Client', 'user_id', fallback=f'user_{socket.gethostname()}')
    device_id = args.device or config.get('Client', 'device_id', fallback=socket.gethostname())
    
    # Create and start tracker
    tracker = ActivityTracker(server_url, user_id, device_id)
    try:
        tracker.start()
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
        tracker.stop()
