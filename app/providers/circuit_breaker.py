from collections import deque
import time

FAILURE_WINDOW_SECONDS = 60
FAILURE_THRESHOLD = 0.5
COOLDOWN_SECONDS = 30

circuit_state = {
    "openai": {"state": "closed", "outcomes": deque(), "opened_at": None},
    "anthropic": {"state": "closed", "outcomes": deque(), "opened_at": None},
}


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
    entry = circuit_state[provider_name]
    if entry["state"] == "closed":
        return True
    if entry["state"] == "open":
        if time.time() - entry["opened_at"] >= COOLDOWN_SECONDS:
            entry["state"] = "half_open"
            return True   # allow a test request
        return False
    if entry["state"] == "half_open":
        return True
    
    return False
