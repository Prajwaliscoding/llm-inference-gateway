"""
Traffic generator for the LLM Inference Gateway.

Sends a steady stream of varied requests to the gateway to exercise:
- Caching (mix of repeated and unique prompts)
- Streaming vs non-streaming
- "auto" model resolution vs explicit model choice
- Multiple providers (via "auto" and explicit model names)

Designed to run continuously (e.g. on a t3.nano EC2 instance) for
multiple days, feeding real data into the Grafana dashboards.
"""

import os
import random
import time
import logging
from datetime import datetime

import requests

# ---- Configuration (override via environment variables) ----
GATEWAY_URL = os.environ.get("GATEWAY_URL", "https://gateway.prajwalkhatiwada.com")
GATEWAY_API_TOKEN = os.environ.get("GATEWAY_API_TOKEN", "gateway-key")
REQUESTS_PER_INTERVAL = 1
INTERVAL_SECONDS = float(os.environ.get("INTERVAL_SECONDS", "5"))
TIMEOUT_SECONDS = 30

EXPLICIT_MODELS = ["gpt-4o-mini", "claude-3-5-haiku-20241022"]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("traffic_generator")

# ---- Prompt pool: 100+ prompts, mixed lengths ----

SHORT_PROMPTS = [
    "What is 2+2?",
    "Say hello in French.",
    "What color is the sky?",
    "Name a fruit.",
    "What is the capital of Japan?",
    "Define recursion in one sentence.",
    "What year is it?",
    "Spell 'necessary'.",
    "What's 7 times 8?",
    "Name a planet.",
    "Translate 'cat' to Spanish.",
    "What is H2O?",
    "Give me a synonym for 'happy'.",
    "What is the opposite of 'up'?",
    "Name a primary color.",
    "What is 100 divided by 4?",
    "What day comes after Monday?",
    "Name a programming language.",
    "What is the boiling point of water in Celsius?",
    "Give me one word that means 'fast'.",
    "14*14",
    "What is the square root of 81?",
    "Name a continent.",
    "What is the chemical symbol for gold?",
    "How many legs does a spider have?",
]

MEDIUM_PROMPTS = [
    "Explain the difference between a list and a tuple in Python.",
    "Summarize the plot of Romeo and Juliet in two sentences.",
    "What are the main causes of climate change?",
    "Describe how a binary search algorithm works.",
    "What is the difference between HTTP and HTTPS?",
    "Explain what a REST API is to a beginner.",
    "What are the benefits of regular exercise?",
    "Describe the water cycle in simple terms.",
    "What is the difference between machine learning and deep learning?",
    "Explain how DNS resolution works.",
    "What are the key principles of object-oriented programming?",
    "Describe the process of photosynthesis.",
    "What is the difference between a stack and a queue?",
    "Explain what containerization means in software development.",
    "What are the pros and cons of remote work?",
    "Describe how a hash table works.",
    "What is the difference between SQL and NoSQL databases?",
    "Explain the concept of eventual consistency in distributed systems.",
    "What are some best practices for writing clean code?",
    "Describe how load balancing works in web applications.",
    "What is the difference between authentication and authorization?",
    "Explain how garbage collection works in most programming languages.",
    "What are the main components of a computer's CPU?",
    "Describe the difference between TCP and UDP.",
    "What is horizontal scaling versus vertical scaling?",
]

LONG_PROMPTS = [
    "Write a short story about a robot who discovers it can dream, "
    "focusing on its emotional journey as it grapples with this new "
    "experience and what it means for its understanding of itself.",
    "Explain in detail how a Kubernetes cluster schedules pods onto "
    "nodes, including the role of the scheduler, resource requests "
    "and limits, and how affinity/anti-affinity rules affect placement.",
    "Compare and contrast three different approaches to caching in "
    "distributed systems: write-through, write-back, and write-around, "
    "including their tradeoffs in terms of consistency and performance.",
    "Describe the full lifecycle of an HTTP request from a browser "
    "typing a URL to receiving a rendered webpage, including DNS "
    "resolution, TCP handshake, TLS negotiation, and HTTP response.",
    "Write a detailed explanation of how retrieval-augmented generation "
    "(RAG) works in large language model applications, including the "
    "roles of embeddings, vector databases, and prompt construction.",
    "Explain the tradeoffs between microservices and monolithic "
    "architectures for a mid-sized startup, considering team size, "
    "deployment complexity, and long-term maintainability.",
    "Describe how database indexing improves query performance, "
    "including the differences between B-tree and hash indexes, and "
    "when each is most appropriate to use.",
    "Write a comprehensive overview of how OAuth 2.0 authorization "
    "flows work, covering the authorization code grant, implicit "
    "grant, and client credentials grant, with use cases for each.",
]

ALL_PROMPTS = SHORT_PROMPTS + MEDIUM_PROMPTS + LONG_PROMPTS

# A smaller, fixed subset that gets reused often to generate cache hits.
CACHEABLE_PROMPTS = random.sample(ALL_PROMPTS, 15)


def build_request_body() -> tuple[dict, bool]:
    """Randomly build a chat completion request body."""
    # 40% chance of reusing a cacheable prompt, 60% chance of any prompt
    if random.random() < 0.4:
        content = random.choice(CACHEABLE_PROMPTS)
    else:
        content = random.choice(ALL_PROMPTS)

    # 50/50 between "auto" and an explicit model
    if random.random() < 0.5:
        model = "auto"
    else:
        model = random.choice(EXPLICIT_MODELS)

    stream = random.random() < 0.3  # 30% streaming requests

    return {
        "model": model,
        "messages": [{"role": "user", "content": content}],
        "stream": stream,
    }, stream


def send_request(session: requests.Session) -> None:
    body, stream = build_request_body()
    headers = {
        "Authorization": f"Bearer {GATEWAY_API_TOKEN}",
        "Content-Type": "application/json",
    }
    url = f"{GATEWAY_URL}/v1/chat/completions"

    start = time.monotonic()
    try:
        resp = session.post(
            url,
            json=body,
            headers=headers,
            timeout=TIMEOUT_SECONDS,
            stream=stream,
        )
        if stream:
            # Drain the stream so the connection completes properly.
            for _ in resp.iter_lines():
                pass
        elapsed = time.monotonic() - start
        logger.info(
            "model=%s stream=%s status=%s elapsed=%.2fs prompt_len=%d",
            body["model"],
            stream,
            resp.status_code,
            elapsed,
            len(body["messages"][0]["content"]),
        )
    except requests.RequestException as exc:
        elapsed = time.monotonic() - start
        logger.error(
            "model=%s stream=%s error=%s elapsed=%.2fs",
            body["model"],
            stream,
            exc,
            elapsed,
        )


def main() -> None:
    logger.info(
        "Starting traffic generator against %s (interval=%.1fs)",
        GATEWAY_URL,
        INTERVAL_SECONDS,
    )
    session = requests.Session()
    request_count = 0

    while True:
        send_request(session)
        request_count += 1
        if request_count % 50 == 0:
            logger.info("Sent %d requests so far (%s)", request_count, datetime.utcnow().isoformat())
        time.sleep(INTERVAL_SECONDS)


if __name__ == "__main__":
    main()