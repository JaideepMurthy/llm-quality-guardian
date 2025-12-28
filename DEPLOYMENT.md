# Deployment Guide - LLM Quality Guardian

## Overview

This guide provides instructions for deploying the LLM Quality Guardian system to production environments, with integrated Datadog monitoring and comprehensive observability.

## Prerequisites

- Python 3.9+
- Docker & Docker Compose (for containerized deployment)
- AWS/GCP/Azure account (for cloud deployment)
- Datadog account and API key
- Google Cloud API credentials

## Local Deployment

### 1. Setup Environment

```bash
# Clone repository
git clone https://github.com/JaideepMurthy/llm-quality-guardian.git
cd llm-quality-guardian

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy and edit environment file
cp .env.example .env

# Edit .env with your credentials:
DATADOG_API_KEY=your_datadog_api_key
DATADOG_APP_KEY=your_datadog_app_key
GOOGLE_API_KEY=your_google_api_key
FLASK_ENV=production
DEBUG=False
```

### 3. Run the API Server

```bash
# Development mode with auto-reload
python -m src.phase3_api_gateway

# Production mode with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 'src.phase3_api_gateway:app'
```

API will be available at `http://localhost:8000`

## Docker Deployment

### 1. Build Docker Image

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "src.phase3_api_gateway:app"]
```

```bash
# Build image
docker build -t llm-quality-guardian:latest .

# Run container
docker run -p 8000:8000 \
  -e DATADOG_API_KEY=your_key \
  -e GOOGLE_API_KEY=your_key \
  llm-quality-guardian:latest
```

### 2. Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATADOG_API_KEY=${DATADOG_API_KEY}
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - FLASK_ENV=production
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  datadog-agent:
    image: datadog/agent:latest
    environment:
      - DD_API_KEY=${DATADOG_API_KEY}
      - DD_SITE=datadoghq.com
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - /proc/:/host/proc/:ro
      - /sys/fs/cgroup/:/host/sys/fs/cgroup:ro
    restart: unless-stopped
```

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f api
```

## Cloud Deployment

### AWS EC2 Deployment

```bash
# Launch EC2 instance (Ubuntu 20.04 LTS)
# SSH into instance
ssh -i key.pem ubuntu@your-instance-ip

# Install dependencies
sudo apt update && sudo apt install -y python3-pip python3-venv

# Clone and setup
git clone https://github.com/JaideepMurthy/llm-quality-guardian.git
cd llm-quality-guardian
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service
sudo cat > /etc/systemd/system/llm-guardian.service << EOF
[Unit]
Description=LLM Quality Guardian API
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/home/ubuntu/llm-quality-guardian
Environment="PATH=/home/ubuntu/llm-quality-guardian/venv/bin"
ExecStart=/home/ubuntu/llm-quality-guardian/venv/bin/gunicorn \
  -w 4 -b 0.0.0.0:8000 \
  'src.phase3_api_gateway:app'
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl start llm-guardian
sudo systemctl enable llm-guardian
```

### Google Cloud Run Deployment

```bash
# Authenticate with GCP
gcloud auth login

# Deploy to Cloud Run
gcloud run deploy llm-quality-guardian \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars DATADOG_API_KEY=your_key,GOOGLE_API_KEY=your_key
```

## Monitoring Setup

### Datadog Integration

```python
# Already integrated in phase3_datadog_monitor.py
# Key metrics being monitored:
# - Request latency (p50, p95, p99)
# - Error rates
# - Model performance scores
# - System resource usage (CPU, memory)
```

### Create Datadog Dashboard

```python
from datadog import api

# Configure Datadog
api.api_key = "your_api_key"
api.app_key = "your_app_key"

# Create dashboard
dashboard = {
    "title": "LLM Quality Guardian Dashboard",
    "widgets": [
        {
            "type": "timeseries",
            "queries": [{"metric": "llm.quality.latency"}]
        },
        {
            "type": "timeseries",
            "queries": [{"metric": "llm.quality.error_rate"}]
        },
        {
            "type": "number",
            "queries": [{"metric": "llm.quality.requests_total"}]
        }
    ]
}

api.Dashboard.create(**dashboard)
```

## Performance Optimization

### 1. Load Balancing

```bash
# Using Nginx as reverse proxy
upstream gunicorn {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
    server 127.0.0.1:8004;
}

server {
    listen 8000;
    
    location / {
        proxy_pass http://gunicorn;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 2. Caching

```python
# Redis caching for model predictions
from functools import lru_cache
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

@app.route('/analyze', methods=['POST'])
def analyze():
    text = request.json['text']
    cache_key = f"analysis:{hash(text)}"
    
    # Check cache
    cached_result = redis_client.get(cache_key)
    if cached_result:
        return json.loads(cached_result)
    
    # Analyze and cache
    result = analyzer.analyze(text)
    redis_client.setex(cache_key, 3600, json.dumps(result))
    return result
```

### 3. Database Connection Pooling

```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'postgresql://user:password@localhost/db',
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_recycle=3600
)
```

## Health Checks

### Kubernetes Health Probes

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: llm-quality-guardian
spec:
  containers:
  - name: api
    image: llm-quality-guardian:latest
    livenessProbe:
      httpGet:
        path: /health
        port: 8000
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /health
        port: 8000
      initialDelaySeconds: 5
      periodSeconds: 5
```

## Scaling

### Horizontal Scaling

```bash
# Kubernetes deployment
kubectl scale deployment llm-guardian --replicas=5

# Docker Swarm
docker service scale llm-guardian=5
```

### Vertical Scaling

```bash
# Increase resources in k8s
kubectl set resources deployment llm-guardian \
  --requests=cpu=2,memory=4Gi \
  --limits=cpu=4,memory=8Gi
```

## Backup & Recovery

### Database Backup

```bash
# PostgreSQL backup
pg_dump -U user -h localhost dbname > backup.sql

# Restore
psql -U user -h localhost dbname < backup.sql
```

### Disaster Recovery Plan

1. **Backup Frequency**: Daily automated backups
2. **Retention**: 30-day backup retention
3. **Recovery Time Objective (RTO)**: < 1 hour
4. **Recovery Point Objective (RPO)**: < 15 minutes

## Security

### SSL/TLS Setup

```bash
# Using Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d yourdomain.com

# Configure Nginx
server {
    listen 443 ssl;
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
}
```

### API Authentication

```python
from functools import wraps
from flask import request, abort

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key or not verify_api_key(api_key):
            abort(401)
        return f(*args, **kwargs)
    return decorated_function

@app.route('/analyze', methods=['POST'])
@require_api_key
def analyze():
    # Implementation
    pass
```

## Monitoring & Alerts

### Key Metrics to Monitor

1. **Request Latency**
   - Alert: P95 > 1000ms
   - Alert: P99 > 2000ms

2. **Error Rate**
   - Alert: > 2% error rate
   - Alert: > 5% error rate (critical)

3. **Throughput**
   - Alert: < 50 req/sec
   - Alert: < 20 req/sec (critical)

4. **System Resources**
   - Alert: CPU > 80%
   - Alert: Memory > 85%

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| High Latency | Check model cache, optimize feature extraction, increase workers |
| OOM Errors | Increase memory allocation, implement batch streaming |
| Connection Errors | Check database connectivity, verify firewall rules |
| Datadog Lag | Implement local caching, reduce metric frequency |

## Version Management

```bash
# Semantic versioning
v1.0.0-rc.1  # Release candidate
v1.0.0       # Production release
v1.0.1       # Patch release
v1.1.0       # Minor release
v2.0.0       # Major release

# Tag release
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0
```

## Post-Deployment Checklist

- [ ] All endpoints responding correctly
- [ ] Datadog metrics flowing
- [ ] Health checks passing
- [ ] Logs being aggregated
- [ ] Backups configured
- [ ] Monitoring alerts active
- [ ] SSL/TLS working
- [ ] API authentication enabled
- [ ] Load balancing verified
- [ ] Disaster recovery tested

## Support & Maintenance

For issues or questions:
- Check logs: `docker-compose logs -f`
- Review metrics: Datadog dashboard
- Contact: support@llm-quality-guardian.dev
