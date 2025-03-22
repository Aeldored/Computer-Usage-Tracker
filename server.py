# File: server.py
# This is the central server that collects data from clients and provides a dashboard

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import json
import os
import datetime
import sqlite3
import threading
import time

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)  # Enable CORS for development

# Database setup
DB_PATH = 'activity_tracker.db'

def init_db():
    """Initialize the database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create tables
    c.execute('''
    CREATE TABLE IF NOT EXISTS devices (
        device_id TEXT PRIMARY KEY,
        user_id TEXT,
        os TEXT,
        os_version TEXT,
        hostname TEXT,
        first_seen TIMESTAMP,
        last_seen TIMESTAMP
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT,
        user_id TEXT,
        timestamp TIMESTAMP,
        key_count INTEGER,
        click_count INTEGER,
        FOREIGN KEY (device_id) REFERENCES devices (device_id)
    )
    ''')
    
    c.execute('''
    CREATE TABLE IF NOT EXISTS event_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id TEXT,
        user_id TEXT,
        event_type TEXT,
        timestamp TIMESTAMP,
        event_data TEXT,
        FOREIGN KEY (device_id) REFERENCES devices (device_id)
    )
    ''')
    
    conn.commit()
    conn.close()

def update_device_info(system_info, timestamp):
    """Update device information in the database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Check if device exists
    c.execute("SELECT device_id FROM devices WHERE device_id = ?", (system_info['device_id'],))
    exists = c.fetchone()
    
    if exists:
        # Update existing device
        c.execute('''
        UPDATE devices 
        SET user_id = ?, os = ?, os_version = ?, hostname = ?, last_seen = ?
        WHERE device_id = ?
        ''', (
            system_info['user_id'],
            system_info['os'],
            system_info['os_version'],
            system_info['hostname'],
            timestamp,
            system_info['device_id']
        ))
    else:
        # Insert new device
        c.execute('''
        INSERT INTO devices (device_id, user_id, os, os_version, hostname, first_seen, last_seen)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            system_info['device_id'],
            system_info['user_id'],
            system_info['os'],
            system_info['os_version'],
            system_info['hostname'],
            timestamp,
            timestamp
        ))
    
    conn.commit()
    conn.close()

def store_activity_summary(device_id, user_id, timestamp, key_count, click_count):
    """Store activity summary in the database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
    INSERT INTO activity_logs (device_id, user_id, timestamp, key_count, click_count)
    VALUES (?, ?, ?, ?, ?)
    ''', (device_id, user_id, timestamp, key_count, click_count))
    
    conn.commit()
    conn.close()

def store_events(device_id, user_id, events):
    """Store individual events in the database"""
    if not events:
        return
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    for event in events:
        c.execute('''
        INSERT INTO event_logs (device_id, user_id, event_type, timestamp, event_data)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            device_id,
            user_id,
            event['type'],
            event['timestamp'],
            json.dumps(event['data'])
        ))
    
    conn.commit()
    conn.close()

@app.route('/')
def index():
    """Render the dashboard"""
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    """Serve static files"""
    return send_from_directory('static', path)

@app.route('/api/activity', methods=['POST'])
def receive_activity():
    """API endpoint to receive activity data from clients"""
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    try:
        # Extract data
        system_info = data.get('system_info', {})
        timestamp = data.get('timestamp', datetime.datetime.now().isoformat())
        events = data.get('events', [])
        summary = data.get('summary', {})
        
        # Update device info
        update_device_info(system_info, timestamp)
        
        # Store activity summary
        device_id = system_info.get('device_id')
        user_id = system_info.get('user_id')
        key_count = summary.get('key_count', 0)
        click_count = summary.get('click_count', 0)
        
        store_activity_summary(device_id, user_id, timestamp, key_count, click_count)
        
        # Store events
        store_events(device_id, user_id, events)
        
        return jsonify({"status": "success"}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/devices', methods=['GET'])
def get_devices():
    """Get all devices"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute('''
    SELECT device_id, user_id, os, hostname, first_seen, last_seen 
    FROM devices
    ORDER BY last_seen DESC
    ''')
    
    rows = c.fetchall()
    devices = [dict(row) for row in rows]
    
    conn.close()
    return jsonify(devices)

@app.route('/api/activity/<device_id>', methods=['GET'])
def get_device_activity(device_id):
    """Get activity for a specific device"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get daily activity for the last 7 days
    c.execute('''
    SELECT 
        strftime('%Y-%m-%d', timestamp) as date,
        SUM(key_count) as total_keys,
        SUM(click_count) as total_clicks
    FROM activity_logs
    WHERE device_id = ?
    AND timestamp >= datetime('now', '-7 days')
    GROUP BY date
    ORDER BY date
    ''', (device_id,))
    
    rows = c.fetchall()
    activity = [dict(row) for row in rows]
    
    conn.close()
    return jsonify(activity)

@app.route('/api/activity/hourly/<device_id>', methods=['GET'])
def get_hourly_activity(device_id):
    """Get hourly activity for a specific device"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get hourly activity for the last 24 hours
    c.execute('''
    SELECT 
        strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
        SUM(key_count) as total_keys,
        SUM(click_count) as total_clicks
    FROM activity_logs
    WHERE device_id = ?
    AND timestamp >= datetime('now', '-24 hours')
    GROUP BY hour
    ORDER BY hour
    ''', (device_id,))
    
    rows = c.fetchall()
    activity = [dict(row) for row in rows]
    
    conn.close()
    return jsonify(activity)

@app.route('/api/summary', methods=['GET'])
def get_summary():
    """Get overall activity summary"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get total counts
    c.execute('''
    SELECT 
        COUNT(DISTINCT device_id) as device_count,
        COUNT(DISTINCT user_id) as user_count,
        SUM(key_count) as total_keys,
        SUM(click_count) as total_clicks
    FROM activity_logs
    ''')
    
    summary = dict(c.fetchone())
    
    conn.close()
    return jsonify(summary)

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
