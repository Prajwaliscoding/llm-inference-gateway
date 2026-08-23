import time
from collections import deque
from typing import Any

from app.metrics import circuit_breaker_state

FAILURE_WINDOW_SECONDS = 60
FAILURE_THRESHOLD = 0.5
COOLDOWN_SECONDS = 30

STATE_VALUES = {"closed": 0, "open": 1, "half_open": 0.5}

circuit_state: dict[str, dict[str, Any]] = {
    "openai": {"state": "closed", "outcomes": deque(), "opened_at": None},
    "anthropic": {"state": "closed", "outcomes": deque(), "opened_at": None},
}
forced_down: dict[str, float | None] = {
    "openai": None,
    "anthropic": None,
}

def force_provider_down(provider_name: str, seconds: int) -> None:
    forced_down[provider_name] = time.time() + seconds

def clear_forced_down(provider_name: str) -> None:
    forced_down[provider_name] = None

def record_outcome(provider_name: str, success: bool) -> None:
    circuit_state[provider_name]["outcomes"].append((time.time(), success))

def get_failure_rate(provider_name: str) -> float:
    now = time.time()
    outcomes = circuit_state[provider_name]["outcomes"]
    
    while outcomes and now - outcomes[0][0] > FAILURE_WINDOW_SECONDS:
        outcomes.popleft()
    
    if not outcomes:
        return 0.0
    
    failures = 0
    for timestamp, success in outcomes:
        if not success:
            failures += 1
    
    return failures / len(outcomes)



def is_available(provider_name: str) -> bool:
    forced_until = forced_down.get(provider_name)
    if forced_until is not None:
        if time.time() < forced_until:
            return False
        forced_down[provider_name] = None
        
    entry = circuit_state[provider_name]
    if entry["state"] == "closed":
        return True
    if entry["state"] == "open":
        if time.time() - entry["opened_at"] >= COOLDOWN_SECONDS:
            entry["state"] = "half_open"
            circuit_breaker_state.labels(provider=provider_name).set(STATE_VALUES[entry["state"]])
            return True   # allow a test request
        return False
    return entry["state"] == "half_open"

def update_circuit(provider_name: str, success: bool) -> None:
    entry = circuit_state[provider_name]
    if entry["state"] == "half_open":     # for half-open
        entry["state"] = "closed" if success else "open"
        circuit_breaker_state.labels(provider=provider_name).set(STATE_VALUES[entry["state"]])
        if entry["state"] == "open":
            entry["opened_at"] = time.time()
        return
    if get_failure_rate(provider_name) >= FAILURE_THRESHOLD: # for closed as the (above if) will fail when the circuit is closed for this provider
        entry["state"] = "open"
        circuit_breaker_state.labels(provider=provider_name).set(STATE_VALUES[entry["state"]])
        entry["opened_at"] = time.time()