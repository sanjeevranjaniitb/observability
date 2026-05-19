# 🎓 AI Gurukul — Observability Stack

Full observability for the AI Gurukul platform using **Prometheus** + **Grafana**, deployed via Docker Compose. Monitors two backend services: the main AI Gurukul API and the RAG Evaluation System.

---

## Architecture

```
┌─────────────────────┐     scrape :8000/metrics     ┌─────────────────┐
│  AI Gurukul Backend │ ──────────────────────────►  │                 │
│     (port 8000)     │                              │   Prometheus    │
├─────────────────────┤     scrape :8001/metrics     │   (port 9090)   │
│  RAG Eval System    │ ──────────────────────────►  │                 │
│     (port 8001)     │                              └────────┬────────┘
└─────────────────────┘                                       │ datasource
                                                              ▼
                                                    ┌─────────────────┐
                                                    │     Grafana     │
                                                    │   (port 3000)   │
                                                    └─────────────────┘
```

---

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
- Python 3.x (only needed to regenerate the dashboard)
- AI Gurukul backend running on `localhost:8000` exposing `/metrics`
- RAG Eval System running on `localhost:8001` exposing `/metrics`

---

## Quick Start

```bash
# 1. Clone / navigate to this directory
cd observability

# 2. (Optional) Regenerate the Grafana dashboard JSON
python build_dashboard.py

# 3. Start the stack
docker compose up -d

# 4. Open Grafana
open http://localhost:3000
```

**Grafana credentials:**
| Field    | Value      |
|----------|------------|
| Username | `admin`    |
| Password | `aigurukul`|

The dashboard loads automatically at login — no manual import needed.

---

## Project Structure

```
observability/
├── docker-compose.yml                        # Prometheus + Grafana services
├── build_dashboard.py                        # Script to generate dashboard JSON
├── prometheus/
│   └── prometheus.yml                        # Scrape configs for both services
└── grafana/
    ├── dashboards/
    │   └── aigurukul.json                    # Pre-built Grafana dashboard
    └── provisioning/
        ├── dashboards/
        │   └── dashboards.yml                # Auto-provision dashboard from file
        └── datasources/
            └── prometheus.yml                # Auto-provision Prometheus datasource
```

---

## Services

| Service    | Image                      | Port | Container Name        |
|------------|----------------------------|------|-----------------------|
| Prometheus | `prom/prometheus:v2.51.0`  | 9090 | `aigurukul-prometheus`|
| Grafana    | `grafana/grafana:10.4.0`   | 3000 | `aigurukul-grafana`   |

**Prometheus** scrapes metrics every 15 seconds and retains data for 15 days.  
**Grafana** auto-provisions the datasource and dashboard on startup — no manual setup required.

---

## Grafana Dashboard

The dashboard (`🎓 AI Gurukul — System Observatory`) is divided into four sections:

### 🏥 System Health
Top-level stat panels showing current state:
- Service up/down status for both backends
- Uptime (seconds) for each service
- Memory usage (AI Gurukul)
- Request counts and error rate in the selected time window

### 🌐 HTTP Endpoints
- Request rate by endpoint (req/s) — both services
- p95 latency by endpoint — both services
- HTTP status code breakdown (stacked)
- Error rate by endpoint and status code
- In-flight request counts

### 🤖 RAG Pipeline
Focused view on `/v1/tutor/chat` and related endpoints:
- RAG request count, p50/p95 latency, session count
- RAG error count and success rate
- Time-series: request rate, latency percentiles (p50/p95/p99)
- All `/v1/*` endpoint request rates
- Error breakdown by status code

### 💰 LLM Cost & Token Usage
- Total input/output token counters
- Estimated USD cost (gpt-4o pricing: $2.50/1M input, $10.00/1M output)
- Token usage per minute broken down by pipeline step
- Estimated cost per minute over time

---

## Prometheus Scrape Targets

| Job              | Target                        | Metrics Path |
|------------------|-------------------------------|--------------|
| `ai-gurukul`     | `host.docker.internal:8000`   | `/metrics`   |
| `rag-eval-system`| `host.docker.internal:8001`   | `/metrics`   |
| `prometheus`     | `localhost:9090`              | `/metrics`   |

`host.docker.internal` resolves to the host machine from inside Docker, so both backends must be running locally.

---

## Key Prometheus Metrics

| Metric | Description |
|--------|-------------|
| `aigurukul_http_requests_total` | Total HTTP requests (labels: `endpoint`, `status_code`) |
| `aigurukul_http_errors_total` | Total HTTP errors (labels: `endpoint`, `status_code`) |
| `aigurukul_http_request_duration_seconds_bucket` | Request latency histogram |
| `aigurukul_http_requests_in_flight` | Current in-flight requests |
| `aigurukul_uptime_seconds` | Service uptime |
| `aigurukul_system_memory_bytes` | Process memory usage |
| `aigurukul_rag_requests_total` | RAG pipeline request counter |
| `aigurukul_llm_tokens_input_total` | LLM input tokens (labels: `model`, `step`) |
| `aigurukul_llm_tokens_output_total` | LLM output tokens (labels: `model`, `step`) |
| `rageval_http_requests_total` | Eval system HTTP requests |
| `rageval_http_request_duration_seconds_bucket` | Eval system latency histogram |
| `rageval_uptime_seconds` | Eval system uptime |

---

## Rebuilding the Dashboard

The dashboard JSON is generated programmatically from `build_dashboard.py`. Edit that file to add/modify panels, then regenerate:

```bash
python build_dashboard.py
# Output: grafana/dashboards/aigurukul.json
# Total panels: <n>
```

Grafana polls the dashboards directory every 30 seconds and will pick up changes automatically (no restart needed).

---

## Useful Commands

```bash
# Start stack in background
docker compose up -d

# View logs
docker compose logs -f

# Stop stack
docker compose down

# Stop and remove volumes (wipes all metrics history)
docker compose down -v

# Reload Prometheus config without restart
curl -X POST http://localhost:9090/-/reload
```

---

## Ports Summary

| URL                          | Service                   |
|------------------------------|---------------------------|
| http://localhost:3000        | Grafana UI                |
| http://localhost:9090        | Prometheus UI             |
| http://localhost:9090/targets| Prometheus scrape targets |
