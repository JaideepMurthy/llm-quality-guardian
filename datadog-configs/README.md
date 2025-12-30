# Datadog Configurations for LLM Quality Guardian

## Overview

This folder contains the Datadog monitoring configurations for the LLM Quality Guardian project, created for the AI Partner Catalyst Hackathon Datadog Challenge.

**Datadog Organization**: jaideep-murthy-llm-guardian
**Trial Account**: Active (12 days remaining)
**Dashboard Link**: https://app.datadoghq.com/dashboard/p4k-7se-hhe
**Monitors Page**: https://app.datadoghq.com/monitors/manage

## Files in this Directory

- `README.md` - This file, documenting the Datadog setup
- `monitors.json` - Monitor configurations exported from Datadog
- `dashboard.json` - Dashboard configuration exported from Datadog

## Monitors Created

The project includes 3 detection rules (monitors) to evaluate application signals:

### 1. System Load Detection
- **Type**: Metric Monitor
- **Metric**: `system.load.1`
- **Alert Threshold**: > 75
- **Detection Method**: Threshold Alert
- **Integration**: Incident Management (creates incidents when triggered)
- **Monitor ID**: 247467395
- **Status**: Draft (with incident management configured)

### 2. CPU Usage is High
- **Type**: Metric Monitor
- **Metric**: CPU usage percentage
- **Alert Threshold**: High CPU utilization
- **Detection Method**: Threshold Alert
- **Monitor ID**: 247467447
- **Status**: Production (Active)

### 3. Disk Usage is High
- **Type**: Forecast Monitor
- **Metric**: Disk usage percentage
- **Detection Method**: Forecast Alert
- **Monitor ID**: 247467507
- **Status**: Production (Active)

## Dashboard

**Name**: LLM Quality Guardian - Application Health
**URL**: https://app.datadoghq.com/dashboard/p4k-7se-hhe
**Widgets**: System metrics timeseries visualization

The dashboard displays:
- Application health metrics (latency, errors, resource usage)
- Detection rule status
- Actionable items derived from monitors

## Incident Management Integration

The system is configured with Datadog Incident Management to:
1. Automatically create incidents when detection rules trigger
2. Include contextual signal data for AI engineers
3. Provide actionable insights for operational response

## Telemetry Data Reporting

The LLM Quality Guardian application reports the following telemetry to Datadog:

- **Custom Metrics**: LLM quality scores, hallucination detection confidence
- **APM**: Request latency, error rates, throughput
- **Logs**: Application logs, error traces, debug information
- **Infrastructure Metrics**: CPU, memory, disk usage, network I/O

Integration is handled via:
- File: `src/datadog_logging.py`
- Method: Python SDK with custom metric instrumentation

## Traffic Generator

To test and demonstrate the detection rules in action:

```bash
python scripts/traffic_generator.py 20
```

This script:
- Sends 20 test queries to the LLM API
- Generates hallucination scores
- Triggers detection rules when scores exceed thresholds
- Logs all events for monitoring
- Shows how high hallucination detections trigger Datadog alerts

## Reproducing the Setup

### Prerequisites
- Datadog trial account (free 14-day trial)
- Python 3.9+
- Deployed LLM Quality Guardian API

### Steps

1. **Create Datadog Account**
   ```
   Visit: https://www.datadoghq.com/
   Sign up for free trial
   ```

2. **Get API Keys**
   - Navigate to Datadog Organization Settings
   - Generate API Key and App Key
   - Store in `.env` file

3. **Deploy Application**
   ```bash
   # See DEPLOYMENT.md in root directory
   docker-compose up -d
   ```

4. **Enable Datadog Agent**
   - The docker-compose.yml includes Datadog Agent
   - Agent automatically reports metrics

5. **Import Configurations** (Optional)
   - Use `monitors.json` and `dashboard.json`
   - Datadog API or web UI can import these

6. **Run Traffic Generator**
   ```bash
   python scripts/traffic_generator.py 20
   ```

7. **Monitor in Datadog**
   - Visit dashboard: https://app.datadoghq.com/dashboard/p4k-7se-hhe
   - Check monitors: https://app.datadoghq.com/monitors/manage
   - View incidents if rules trigger

## Key Metrics for Judges

**Observability Strategy Implemented**:
- ✅ Real-time health monitoring (latency, errors, costs)
- ✅ SLO-based alerting with detection rules
- ✅ Incident management for actionable response
- ✅ Custom LLM metrics (hallucination scores)
- ✅ Full telemetry pipeline (logs, APM, infrastructure)

**Innovation Highlights**:
- Integrated hallucination detection scoring with Datadog monitoring
- Automated incident creation on detection rule triggers
- Demonstrates end-to-end observability for LLM applications
- Combines Vertex AI, Datadog, and custom Python instrumentation

**Challenges Addressed**:
- Real-time detection of LLM hallucinations
- Correlating LLM-specific metrics with infrastructure health
- Actionable alerting for operational teams
- Reproducible setup for testing and demonstration

## References

- [Datadog Documentation](https://docs.datadoghq.com/)
- [Datadog Monitors](https://docs.datadoghq.com/monitors/)
- [Datadog Incident Management](https://docs.datadoghq.com/service_management/incident_management/)
- [Datadog Python SDK](https://github.com/DataDog/dd-trace-py)
- [Hackathon Challenge](https://ai-partner-catalyst.devpost.com/resources)
