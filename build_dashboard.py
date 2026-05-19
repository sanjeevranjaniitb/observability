"""
Build the AI Gurukul Grafana dashboard JSON from sections.
Run: python build_dashboard.py
Output: grafana/dashboards/aigurukul.json
"""

import json, os

# ── helpers ──────────────────────────────────────────────────────────────────

def row(title, y):
    return {"type":"row","title":title,"gridPos":{"x":0,"y":y,"w":24,"h":1},"collapsed":False,"id":y*100}

def stat(id, title, expr, unit, y, x, w=4, h=3, color="#73BF69", thresholds=None):
    thr = thresholds or [{"color":"red","value":None},{"color":"yellow","value":0.5},{"color":"green","value":0.9}]
    return {
        "id":id,"type":"stat","title":title,
        "gridPos":{"x":x,"y":y,"w":w,"h":h},
        "datasource":{"type":"prometheus","uid":"PBFA97CFB590B2093"},
        "options":{"reduceOptions":{"calcs":["lastNotNull"]},"orientation":"auto","colorMode":"background","graphMode":"area","justifyMode":"auto"},
        "fieldConfig":{"defaults":{"unit":unit,"thresholds":{"mode":"absolute","steps":thr},"color":{"mode":"thresholds"}}},
        "targets":[{"expr":expr,"legendFormat":"","refId":"A","datasource":{"type":"prometheus","uid":"PBFA97CFB590B2093"}}]
    }

def timeseries(id, title, targets, unit, y, x, w=12, h=7, stack=False):
    return {
        "id":id,"type":"timeseries","title":title,
        "gridPos":{"x":x,"y":y,"w":w,"h":h},
        "datasource":{"type":"prometheus","uid":"PBFA97CFB590B2093"},
        "options":{"tooltip":{"mode":"multi"},"legend":{"displayMode":"list","placement":"bottom"}},
        "fieldConfig":{"defaults":{"unit":unit,"custom":{"lineWidth":2,"fillOpacity":10 if not stack else 40,"stacking":{"mode":"normal" if stack else "none"}}}},
        "targets":[{"expr":t["expr"],"legendFormat":t.get("legend","{{endpoint}}"),"refId":chr(65+i),"datasource":{"type":"prometheus","uid":"PBFA97CFB590B2093"}} for i,t in enumerate(targets)]
    }

def heatmap(id, title, expr, y, x, w=12, h=7):
    return {
        "id":id,"type":"heatmap","title":title,
        "gridPos":{"x":x,"y":y,"w":w,"h":h},
        "datasource":{"type":"prometheus","uid":"PBFA97CFB590B2093"},
        "options":{"calculate":False,"color":{"scheme":"Oranges","fill":"dark-orange"},"yAxis":{"unit":"s"}},
        "targets":[{"expr":expr,"legendFormat":"{{le}}","refId":"A","datasource":{"type":"prometheus","uid":"PBFA97CFB590B2093"}}]
    }

def gauge(id, title, expr, unit, y, x, w=4, h=4, min_val=0, max_val=1):
    return {
        "id":id,"type":"gauge","title":title,
        "gridPos":{"x":x,"y":y,"w":w,"h":h},
        "datasource":{"type":"prometheus","uid":"PBFA97CFB590B2093"},
        "options":{"reduceOptions":{"calcs":["lastNotNull"]},"showThresholdLabels":False,"showThresholdMarkers":True},
        "fieldConfig":{"defaults":{"unit":unit,"min":min_val,"max":max_val,
            "thresholds":{"mode":"absolute","steps":[{"color":"red","value":None},{"color":"yellow","value":max_val*0.5},{"color":"green","value":max_val*0.8}]}}},
        "targets":[{"expr":expr,"legendFormat":"","refId":"A","datasource":{"type":"prometheus","uid":"PBFA97CFB590B2093"}}]
    }

def table(id, title, targets, y, x, w=24, h=6):
    return {
        "id":id,"type":"table","title":title,
        "gridPos":{"x":x,"y":y,"w":w,"h":h},
        "datasource":{"type":"prometheus","uid":"PBFA97CFB590B2093"},
        "options":{"sortBy":[{"displayName":"Value","desc":True}]},
        "fieldConfig":{"defaults":{"custom":{"displayMode":"color-background"}}},
        "targets":[{"expr":t["expr"],"legendFormat":t.get("legend",""),"refId":chr(65+i),"instant":True,"datasource":{"type":"prometheus","uid":"PBFA97CFB590B2093"}} for i,t in enumerate(targets)]
    }


# ── Section 1: System Health ─────────────────────────────────────────────────

y = 0
panels = []

panels.append(row("🏥  System Health", y)); y+=1

# up{} = 0 or 1 — not time-dependent, always current
panels.append(stat(1,"AI Gurukul Backend",
    'up{job="ai-gurukul"}', "short", y, 0, 3, 3,
    thresholds=[{"color":"red","value":None},{"color":"green","value":1}]))

panels.append(stat(2,"RAG Eval System",
    'up{job="rag-eval-system"}', "short", y, 3, 3, 3,
    thresholds=[{"color":"red","value":None},{"color":"green","value":1}]))

# Uptime — always current, not time-windowed
panels.append(stat(3,"AI Gurukul Uptime",
    'aigurukul_uptime_seconds', "s", y, 6, 3, 3,
    thresholds=[{"color":"green","value":None}]))

panels.append(stat(4,"Eval System Uptime",
    'rageval_uptime_seconds', "s", y, 9, 3, 3,
    thresholds=[{"color":"green","value":None}]))

# Memory — always current
panels.append(stat(5,"Memory (AI Gurukul)",
    'aigurukul_system_memory_bytes', "bytes", y, 12, 3, 3,
    thresholds=[{"color":"green","value":None},{"color":"yellow","value":4e9},{"color":"red","value":8e9}]))

# Requests IN SELECTED TIME WINDOW — use increase($__range) so time filter works
panels.append(stat(6,"Requests in Window (AI Gurukul)",
    'round(sum(increase(aigurukul_http_requests_total[$__range])) - sum(increase(aigurukul_http_requests_total[$__range] offset $__range)))', "short", y, 15, 3, 3,
    thresholds=[{"color":"blue","value":None}]))

panels.append(stat(7,"Requests in Window (Eval)",
    'round(sum(increase(rageval_http_requests_total[$__range])) - sum(increase(rageval_http_requests_total[$__range] offset $__range)))', "short", y, 18, 3, 3,
    thresholds=[{"color":"blue","value":None}]))

# Error rate — rate over $__rate_interval respects time filter
panels.append(stat(8,"Error Rate (AI Gurukul)",
    'sum(rate(aigurukul_http_errors_total[$__rate_interval])) / (sum(rate(aigurukul_http_requests_total[$__rate_interval])) > 0) * 100 or vector(0)',
    "percent", y, 21, 3, 3,
    thresholds=[{"color":"green","value":None},{"color":"yellow","value":1},{"color":"red","value":5}]))

y += 3

# ── Section 2: HTTP Endpoints ─────────────────────────────────────────────────

panels.append(row("🌐  HTTP Endpoints — All Requests & Latency", y)); y+=1

# $__rate_interval auto-adjusts to selected time range
panels.append(timeseries(10,"Request Rate by Endpoint (AI Gurukul)",
    [{"expr":'sum by (endpoint) (rate(aigurukul_http_requests_total[$__rate_interval]))'}],
    "reqps", y, 0, 12, 7))

panels.append(timeseries(11,"Request Rate by Endpoint (Eval System)",
    [{"expr":'sum by (endpoint) (rate(rageval_http_requests_total[$__rate_interval]))'}],
    "reqps", y, 12, 12, 7))

y += 7

panels.append(timeseries(12,"p95 Latency by Endpoint (AI Gurukul)",
    [{"expr":'histogram_quantile(0.95, sum by (endpoint, le) (rate(aigurukul_http_request_duration_seconds_bucket[$__rate_interval])))'}],
    "s", y, 0, 12, 7))

panels.append(timeseries(13,"p95 Latency by Endpoint (Eval System)",
    [{"expr":'histogram_quantile(0.95, sum by (endpoint, le) (rate(rageval_http_request_duration_seconds_bucket[$__rate_interval])))'}],
    "s", y, 12, 12, 7))

y += 7

panels.append(timeseries(14,"HTTP Status Codes (AI Gurukul)",
    [{"expr":'sum by (status_code) (rate(aigurukul_http_requests_total[$__rate_interval]))',"legend":"{{status_code}}"}],
    "reqps", y, 0, 12, 6, stack=True))

panels.append(timeseries(15,"HTTP Errors (AI Gurukul)",
    [{"expr":'sum by (endpoint, status_code) (rate(aigurukul_http_errors_total[$__rate_interval]))',"legend":"{{status_code}} {{endpoint}}"}],
    "reqps", y, 12, 12, 6))

y += 6

panels.append(timeseries(16,"In-Flight Requests (AI Gurukul)",
    [{"expr":'sum by (endpoint) (aigurukul_http_requests_in_flight)'}],
    "short", y, 0, 12, 5))

panels.append(timeseries(17,"In-Flight Requests (Eval System)",
    [{"expr":'sum by (endpoint) (rageval_http_requests_in_flight)'}],
    "short", y, 12, 12, 5))

y += 5

# ── Section 3: RAG Pipeline ───────────────────────────────────────────────────

panels.append(row("🤖  RAG Pipeline", y)); y+=1

# Requests in selected window
panels.append(stat(20,"RAG Requests in Window",
    'round(sum(increase(aigurukul_http_requests_total{endpoint="/v1/tutor/chat"}[$__range])) - sum(increase(aigurukul_http_requests_total{endpoint="/v1/tutor/chat"}[$__range] offset $__range)))',
    "short", y, 0, 4, 3, thresholds=[{"color":"blue","value":None}]))

# p50 latency — quantile over rate_interval
panels.append(stat(21,"RAG p50 Latency",
    'histogram_quantile(0.50, sum(rate(aigurukul_http_request_duration_seconds_bucket{endpoint="/v1/tutor/chat"}[$__rate_interval])) by (le))',
    "s", y, 4, 4, 3,
    thresholds=[{"color":"green","value":None},{"color":"yellow","value":10},{"color":"red","value":20}]))

panels.append(stat(22,"RAG p95 Latency",
    'histogram_quantile(0.95, sum(rate(aigurukul_http_request_duration_seconds_bucket{endpoint="/v1/tutor/chat"}[$__rate_interval])) by (le))',
    "s", y, 8, 4, 3,
    thresholds=[{"color":"green","value":None},{"color":"yellow","value":15},{"color":"red","value":30}]))

panels.append(stat(23,"Sessions in Window",
    'round(sum(increase(aigurukul_http_requests_total{endpoint="/v1/sessions"}[$__range])) - sum(increase(aigurukul_http_requests_total{endpoint="/v1/sessions"}[$__range] offset $__range)))',
    "short", y, 12, 4, 3, thresholds=[{"color":"blue","value":None}]))

panels.append(stat(24,"RAG Errors in Window",
    'round(sum(increase(aigurukul_http_errors_total{endpoint="/v1/tutor/chat"}[$__range])) - sum(increase(aigurukul_http_errors_total{endpoint="/v1/tutor/chat"}[$__range] offset $__range)))',
    "short", y, 16, 4, 3,
    thresholds=[{"color":"green","value":None},{"color":"red","value":1}]))

panels.append(stat(25,"RAG Success Rate",
    '(1 - sum(rate(aigurukul_http_errors_total{endpoint="/v1/tutor/chat"}[$__rate_interval])) / (sum(rate(aigurukul_http_requests_total{endpoint="/v1/tutor/chat"}[$__rate_interval])) > 0)) * 100 or vector(100)',
    "percent", y, 20, 4, 3,
    thresholds=[{"color":"red","value":None},{"color":"yellow","value":90},{"color":"green","value":99}]))

y += 3

panels.append(timeseries(26,"RAG Request Rate over Time",
    [{"expr":'rate(aigurukul_http_requests_total{endpoint="/v1/tutor/chat"}[$__rate_interval])',"legend":"requests/s"}],
    "reqps", y, 0, 12, 7))

panels.append(timeseries(27,"RAG Latency — p50 / p95 / p99",
    [
        {"expr":'histogram_quantile(0.50, sum(rate(aigurukul_http_request_duration_seconds_bucket{endpoint="/v1/tutor/chat"}[$__rate_interval])) by (le))',"legend":"p50"},
        {"expr":'histogram_quantile(0.95, sum(rate(aigurukul_http_request_duration_seconds_bucket{endpoint="/v1/tutor/chat"}[$__rate_interval])) by (le))',"legend":"p95"},
        {"expr":'histogram_quantile(0.99, sum(rate(aigurukul_http_request_duration_seconds_bucket{endpoint="/v1/tutor/chat"}[$__rate_interval])) by (le))',"legend":"p99"},
    ], "s", y, 12, 12, 7))

y += 7

panels.append(timeseries(28,"All RAG Endpoint Request Rates",
    [{"expr":'sum by (endpoint) (rate(aigurukul_http_requests_total{endpoint=~"/v1/.*"}[$__rate_interval]))',"legend":"{{endpoint}}"}],
    "reqps", y, 0, 12, 6))

panels.append(timeseries(29,"RAG Error Rate by Status Code",
    [{"expr":'sum by (status_code) (rate(aigurukul_http_errors_total{endpoint="/v1/tutor/chat"}[$__rate_interval]))',"legend":"{{status_code}}"}],
    "reqps", y, 12, 12, 6))

y += 6


# ── Assemble dashboard ────────────────────────────────────────────────────────

dashboard = {
    "uid": "aigurukul-main",
    "title": "🎓 AI Gurukul — System Observatory",
    "description": "Full observability: all REST endpoints, RAG pipeline, system health — time-filter aware",
    "tags": ["aigurukul", "rag", "eval"],
    "timezone": "browser",
    "refresh": "30s",
    "time": {"from": "now-6h", "to": "now"},
    "timepicker": {"refresh_intervals": ["15s","30s","1m","5m"]},
    "schemaVersion": 38,
    "version": 1,
    "panels": panels,
    "templating": {"list": []},
    "annotations": {"list": []},
    "links": [],
    "style": "dark",
    "graphTooltip": 1,
}

out = os.path.join(os.path.dirname(__file__), "grafana", "dashboards", "aigurukul.json")
os.makedirs(os.path.dirname(out), exist_ok=True)
with open(out, "w") as f:
    json.dump(dashboard, f, indent=2)

print(f"Dashboard written to {out}")
print(f"Total panels: {len(panels)}")
