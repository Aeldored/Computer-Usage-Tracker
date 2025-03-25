# Computer Usage Tracking System

This system tracks computer usage across multiple machines by logging key presses and mouse clicks, sending the data to a central server, and displaying analytics on a web-based dashboard.

## Features

- **Client Application**: Tracks keyboard and mouse activity on client computers
- **Central Server**: Collects and stores activity data from all clients
- **Web Dashboard**: Visualizes usage patterns with interactive charts
- **Multi-User Support**: Tracks activity across different users and devices
- **Privacy-Focused**: Only counts key presses without recording actual keystrokes

## System Architecture

The system consists of three main components:

1. **Client Tracker**: Python application that runs on end-user computers
2. **Central Server**: Flask web server that receives and stores activity data
3. **Web Dashboard**: Interactive UI for data visualization and analysis

## Installation

### Prerequisites

- Python 3.7+
- SQLite3
- Flask
- pynput

### Server Setup

1. Clone the repository:

   ```
   git clone https://github.com/Aeldored/computer-usage-tracker.git
   cd computer-usage-tracker
   ```

2. Install server dependencies:

   ```
   pip install flask flask-cors
   ```

3. Start the server:
   ```
   python server.py
   ```
   The server will run on http://localhost:5000 by default.

### Client Setup

1. Install client dependencies:

   ```
   pip install pynput requests
   ```

2. Configure the client:
   Create a `config.ini` file with the following content:

   ```
   [Server]
   url = http://your-server-ip:5000

   [Client]
   user_id = your_username
   device_id = your_device_name
   ```

3. Run the client application:
   ```
   python client_tracker.py
   ```

## Usage

### Dashboard Access

Open a web browser and navigate to `http://your-server-ip:5000` to access the dashboard.

### Dashboard Features

- Overview of all connected devices
- Total key press and mouse click statistics
- Daily and hourly activity charts
- Device-specific activity analysis

### Client Configuration Options

The client application supports the following command-line options:

- `--config`: Path to the configuration file (default: config.ini)
- `--server`: Server URL (overrides config file)
- `--user`: User ID (overrides config file)
- `--device`: Device ID (overrides config file)

Example:

```
python client_tracker.py --server http://192.168.1.100:5000 --user john --device laptop
```

## Security and Privacy Considerations

- The system only counts keystrokes and does not record the actual keys pressed
- Data is transmitted over HTTP by default - consider implementing HTTPS for production use
- The system does not track application names or window titles
- Consider implementing user authentication for the dashboard in production environments
- Review local privacy laws and regulations before deployment

## Extending the System

### Adding User Authentication

For production use, you may want to add user authentication to the server:

1. Install Flask-Login:

   ```
   pip install flask-login
   ```

2. Create user authentication system and integrate it with the dashboard

### Adding SSL/TLS Support

For secure data transmission, configure the server with SSL/TLS:

1. Generate SSL certificates
2. Update the server code to use HTTPS
3. Update client configurations to use HTTPS URLs

## Troubleshooting

- **Client Connection Issues**: Verify server URL and network connectivity
- **Permission Errors**: The client may require administrative privileges to monitor keyboard/mouse events
- **Database Errors**: Check SQLite database permissions
