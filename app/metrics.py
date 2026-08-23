from prometheus_client import Counter, Gauge, Histogram

requests_total = Counter(
    "gateway_requests_total",
    "Total number of requests",
    ["provider", "model", "status"]
)

request_duration_seconds = Histogram(
    "gateway_request_duration_seconds",
    "Request duration in seconds",
    ["provider", "model"]
)

cost_cents_total = Counter(
    "gateway_cost_cents_total",
    "Total cost in cents",
    ["provider", "model"]
)

cache_hits_total = Counter(
    "gateway_cache_hits_total",
    "Total cache hits"
)

cache_misses_total = Counter(
    "gateway_cache_misses_total",
    "Total cache misses"
)

provider_failures_total = Counter(
    "gateway_provider_failures_total",
    "Total provider failures",
    ["provider", "error_type"]
)

circuit_breaker_state = Gauge(
    "gateway_circuit_breaker_state",
    "Circuit breaker state (0=closed, 1=open, 0.5=half-open)",
    ["provider"]
)