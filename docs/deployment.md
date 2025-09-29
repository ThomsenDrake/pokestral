# Deployment Instructions

## Overview

This guide covers deployment options for the Pokémon Blue AI agent, from local development to production environments.

## Local Deployment

### Prerequisites
- Python 3.10+
- Git
- Pokémon Blue ROM

### Steps

1. Clone repository:
```bash
git clone https://github.com/yourorg/pokemon-blue-agent.git
cd pokemon-blue-agent
```

2. Install dependencies:
```bash
uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

4. Run agent:
```bash
python -m agent_core
```

## Docker Deployment

### Building Image

```bash
docker build -t pokemon-agent .
```

### Running Container

```bash
docker run -it --rm \
  -v ./roms:/app/roms \
  -v ./data:/app/data \
  -e MISTRAL_API_KEY=your_key \
  pokemon-agent
```

### Docker Compose

```yaml
version: '3'
services:
  agent:
    build: .
    volumes:
      - ./roms:/app/roms
      - ./data:/app/data
    environment:
      - MISTRAL_API_KEY=${MISTRAL_API_KEY}
    ports:
      - "8501:8501"  # Dashboard
```

## Production Deployment

### Recommended Setup

1. **Server Requirements**:
   - 4+ CPU cores
   - 16GB RAM
   - 50GB SSD storage

2. **Process Management**:
   - Use systemd or Supervisor
   - Example systemd service:

```ini
# /etc/systemd/system/pokemon-agent.service
[Unit]
Description=Pokémon Blue AI Agent
After=network.target

[Service]
User=agent
WorkingDirectory=/opt/pokemon-agent
ExecStart=/opt/pokemon-agent/.venv/bin/python -m agent_core
Restart=always
EnvironmentFile=/opt/pokemon-agent/.env

[Install]
WantedBy=multi-user.target
```

3. **Logging**:
   - Configure syslog or log rotation
   - Example logrotate config:

```conf
# /etc/logrotate.d/pokemon-agent
/opt/pokemon-agent/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}
```

## Cloud Deployment

### AWS Example

1. **EC2 Instance**:
   - t3.xlarge or better
   - Amazon Linux 2
   - 50GB GP2 storage

2. **Setup Script**:
```bash
#!/bin/bash
yum update -y
yum install -y git python3 docker
usermod -aG docker ec2-user
systemctl enable docker
systemctl start docker

git clone https://github.com/yourorg/pokemon-blue-agent.git
cd pokemon-blue-agent
# Add your config and ROM

docker build -t pokemon-agent .
docker run -d --restart always -v $(pwd)/data:/app/data pokemon-agent
```

### Monitoring

1. **CloudWatch**:
   - Monitor CPU, memory, disk
   - Set alerts for failures

2. **Custom Metrics**:
   - Push agent metrics to CloudWatch
   - Example:

```python
import boto3

cloudwatch = boto3.client('cloudwatch')
cloudwatch.put_metric_data(
    Namespace='PokemonAgent',
    MetricData=[{
        'MetricName': 'ActionsPerMinute',
        'Value': actions_count,
        'Unit': 'Count'
    }]
)
```

## Configuration Management

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MISTRAL_API_KEY` | Mistral API key | - |
| `ROM_PATH` | Path to ROM file | roms/pokemon-blue.gb |
| `HEADLESS` | Run without display | false |
| `FAST_FORWARD` | Enable frame skipping | true |
| `LOG_LEVEL` | Logging level | INFO |
| `CHECKPOINT_INTERVAL` | Auto-save interval (sec) | 300 |

### Configuration File

Example `config.yaml`:
```yaml
agent:
  fast_forward: true
  checkpoint_interval: 300
  max_context_tokens: 8000

mistral:
  model: mistral-tiny
  temperature: 0.7

logging:
  level: INFO
  file: logs/agent.log
```

## Scaling

### Horizontal Scaling
- Run multiple agents with different strategies
- Share database with read replicas

### Vertical Scaling
- Increase instance size for better performance
- Optimize frame skipping

## Backup Strategy

1. **Database Backups**:
```bash
sqlite3 agent.db .dump > backups/agent-$(date +%F).sql
```

2. **Checkpoint Backups**:
```bash
cp data/checkpoints/* backups/checkpoints/
```

3. **Automated Backups**:
```bash
#!/bin/bash
# Daily backup script
mkdir -p backups/$(date +%F)
cp -r data backups/$(date +%F)/
sqlite3 agent.db .dump > backups/$(date +%F)/agent.sql
```

## Troubleshooting Deployment

**Common Issues:**

1. **ROM not found**:
   - Verify ROM path in .env
   - Check file permissions
   - Confirm ROM checksum

2. **API connection errors**:
   - Test network connectivity
   - Verify API key
   - Check rate limits

3. **Performance problems**:
   - Reduce frame skip
   - Increase instance size
   - Optimize memory access

4. **Database corruption**:
   - Restore from backup
   - Run `sqlite3 agent.db "VACUUM;"`
   - Check disk space