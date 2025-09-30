# Deployment Guide

## System Requirements

### Hardware Requirements
- **CPU**: Modern processor with good single-thread performance
- **RAM**: 16GB minimum (32GB recommended for development)
- **Storage**: 50GB free space (for ROMs, screenshots, logs, checkpoints)
- **Graphics**: OpenGL 2.1+ compatible GPU (for visual display)
- **Network**: Stable internet connection for Mistral API access

### Software Requirements
- **Operating System**: 
  - Linux (Ubuntu 20.04+, CentOS 8+, etc.)
  - macOS (10.15+)
  - Windows (10+, with WSL2 recommended)
- **Python**: 3.12+
- **Dependencies**: See `requirements.txt`

## Installation

### Production Environment Setup

#### Using uv (Recommended for Production)
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create production environment
uv venv --python 3.12

# Activate environment
source .venv/bin/activate

# Install only runtime dependencies
uv pip install pyboy pydantic fastapi streamlit psutil requests
```

#### Using pip (Alternative)
```bash
# Create virtual environment
python3.12 -m venv .venv

# Activate environment
source .venv/bin/activate

# Install dependencies
pip install pyboy pydantic fastapi streamlit psutil requests
```

### Development Environment Setup

For development and testing:
```bash
# Install all dependencies including development tools
uv pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install
```

## Configuration

### Environment Variables
Create a `.env` file in the project root:

```ini
# Mistral API Configuration
MISTRAL_API_KEY=your_production_api_key_here
MISTRAL_MODEL=mistral-medium-latest

# Game Configuration
ROM_PATH=/path/to/pokemon-blue-version.gb
SAVE_STATE_PATH=/path/to/save/states/

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=/var/log/pokestral/agent.log
LOG_MAX_SIZE=100MB
LOG_BACKUP_COUNT=5

# Performance Configuration
FRAME_SKIP=1
MAX_FRAME_SKIPS=60
SCREENSHOT_INTERVAL=300
CHECKPOINT_INTERVAL=600

# API Configuration
API_TIMEOUT=30
API_RETRY_ATTEMPTS=3
API_RATE_LIMIT=1000  # requests per hour
```

### Directory Structure
```
/var/lib/pokestral/          # Data directory (production)
├── roms/                     # Game ROMs
├── screenshots/               # Game screenshots
├── checkpoints/              # Game state saves
├── logs/                     # Application logs
└── config/                   # Configuration files

/opt/pokestral/               # Application directory (production)
├── agent_core/               # Core agent modules
├── emulator/                # Emulator interface
├── memory_map/               # Memory mapping
├── state_detector/           # State detection
├── prompt_manager/           # Prompt management
├── tools/                    # Specialized tools
└── main.py                  # Main entry point
```

## Running the Agent

### Basic Execution
```bash
# Run with default settings
python main.py

# Run with specific ROM path
python main.py --rom /path/to/pokemon-blue-version.gb

# Run in headless mode (no visual window)
python main.py --headless

# Run with debug logging
python main.py --debug
```

### Production Deployment
```bash
# Run as background service
nohup python main.py --headless > /var/log/pokestral/agent.log 2>&1 &

# Run with systemd service (recommended)
sudo systemctl start pokestral-agent
```

### Command Line Options
```bash
usage: main.py [-h] [--rom PATH] [--headless] [--debug] [--config CONFIG]

Pokemon Blue AI Agent

options:
  -h, --help            show this help message and exit
  --rom PATH           Path to Pokemon Blue ROM file
  --headless           Run without visual window
  --debug              Enable debug logging
  --config CONFIG      Path to configuration file
```

## Monitoring and Maintenance

### Health Checks
```bash
# Check if agent is running
ps aux | grep main.py

# Check log files
tail -f /var/log/pokestral/agent.log

# Monitor system resources
htop
```

### Log Analysis
```bash
# View recent errors
grep "ERROR" /var/log/pokestral/agent.log | tail -20

# Monitor API usage
grep "Mistral API" /var/log/pokestral/agent.log

# Check performance metrics
grep "Runtime\|FPS" /var/log/pokestral/agent.log
```

### Performance Tuning
```bash
# Adjust frame skip for better performance
export FRAME_SKIP=2

# Modify screenshot interval to reduce I/O
export SCREENSHOT_INTERVAL=600

# Tune checkpoint frequency
export CHECKPOINT_INTERVAL=1200
```

## Backup and Recovery

### Data Backup Strategy
```bash
# Daily backups of checkpoints and saves
0 2 * * * /opt/pokestral/scripts/backup.sh

# Weekly full backup
0 3 * * 0 /opt/pokestral/scripts/full_backup.sh
```

### Checkpoint Management
```bash
# List available checkpoints
ls -la /var/lib/pokestral/checkpoints/

# Restore from checkpoint
python main.py --checkpoint /var/lib/pokestral/checkpoints/latest.state
```

### Log Rotation
Configure logrotate in `/etc/logrotate.d/pokestral`:
```
/var/log/pokestral/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 pokestral pokestral
    postrotate
        systemctl reload pokestral-agent
    endscript
}
```

## Scaling and High Availability

### Horizontal Scaling
For running multiple agents:
```bash
# Agent 1
python main.py --rom /roms/pokemon1.gb --port 8001

# Agent 2
python main.py --rom /roms/pokemon2.gb --port 8002

# Agent 3
python main.py --rom /roms/pokemon3.gb --port 8003
```

### Load Balancing
Use nginx or HAProxy to distribute API requests:
```nginx
upstream mistral_api {
    server api.mistral.ai:443;
    keepalive 32;
}

location /v1 {
    proxy_pass https://mistral_api;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
}
```

### Container Deployment
Dockerfile for containerized deployment:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsdl2-dev \
    libsdl2-image-dev \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv and dependencies
COPY requirements.txt .
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
RUN uv pip install -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /data/screenshots /data/checkpoints /data/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV DATA_DIR=/data

EXPOSE 8000

CMD ["python", "main.py"]
```

## Security Considerations

### API Key Management
```bash
# Store API keys securely
chmod 600 /etc/pokestral/.env
chown pokestral:pokestral /etc/pokestral/.env

# Use environment variables instead of hardcoded keys
export MISTRAL_API_KEY=$(cat /secure/location/api_key)
```

### Network Security
```bash
# Firewall rules
ufw allow from 10.0.0.0/8 to any port 8000
ufw deny from any to any port 8000

# SSL/TLS for API endpoints
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/pokestral.key \
    -out /etc/ssl/certs/pokestral.crt
```

### File Permissions
```bash
# Set proper ownership
chown -R pokestral:pokestral /var/lib/pokestral/
chmod -R 755 /var/lib/pokestral/

# Secure sensitive files
chmod 600 /var/lib/pokestral/config/*
chmod 644 /var/lib/pokestral/roms/*
```

## Troubleshooting Production Issues

### Common Production Problems

**High Memory Usage**
```bash
# Monitor memory usage
ps aux --sort=-%mem | head -10

# Restart agent to clear memory
systemctl restart pokestral-agent

# Increase system swap space
sudo fallocate -l 8G /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**API Rate Limiting**
```bash
# Check current API usage
grep "rate limit\|429" /var/log/pokestral/agent.log

# Implement exponential backoff
# Already built into MistralAPI client
```

**Emulator Crashes**
```bash
# Check for segmentation faults
dmesg | grep segfault

# Enable core dumps for debugging
ulimit -c unlimited

# Monitor system stability
journalctl -f
```

**Disk Space Issues**
```bash
# Check disk usage
df -h

# Clean up old screenshots
find /var/lib/pokestral/screenshots -name "*.png" -mtime +7 -delete

# Rotate large log files
logrotate /etc/logrotate.d/pokestral
```

## Performance Monitoring

### Metrics Collection
Monitor these key metrics:
- **Frame Rate**: Target 60 FPS, minimum 30 FPS
- **API Latency**: Average response time < 2 seconds
- **Memory Usage**: < 8GB RAM utilization
- **Disk I/O**: < 100 MB/s sustained writes
- **Network Usage**: < 1 MB/s API traffic

### Dashboard Integration
Set up monitoring with Prometheus/Grafana:
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'pokestral'
    static_configs:
      - targets: ['localhost:8000']
```

### Alerting Rules
Configure alerts for critical issues:
- Agent downtime > 5 minutes
- API errors > 10% rate
- Disk space < 10% remaining
- Memory usage > 90%

## Updates and Maintenance

### Version Updates
```bash
# Backup current installation
tar -czf pokestral-backup-$(date +%Y%m%d).tar.gz /opt/pokestral

# Update dependencies
uv pip install --upgrade -r requirements.txt

# Restart services
systemctl restart pokestral-agent
```

### Patch Management
```bash
# Schedule regular updates
0 4 * * 0 /opt/pokestral/scripts/update.sh

# Security patch notifications
# Subscribe to security mailing lists for dependencies
```

### Rollback Procedures
```bash
# In case of failed update
systemctl stop pokestral-agent
cp -r /opt/pokestral-backup/* /opt/pokestral/
systemctl start pokestral-agent
```

## Compliance and Legal

### ROM Distribution
- **DO NOT** distribute Pokémon Blue ROMs
- Users must provide their own legally obtained ROMs
- Verify ROM checksums against known good values

### API Usage
- Comply with Mistral API terms of service
- Monitor and respect rate limits
- Implement proper error handling and retries

### Data Privacy
- No personal data collection without consent
- Secure storage of API keys and credentials
- Regular security audits of deployed systems