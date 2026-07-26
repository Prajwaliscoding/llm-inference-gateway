# LLM Inference Gateway — Specification

## Problem Statement

**What it does:** The LLM Inference Gateway is a single API that sits between client applications and multiple LLM providers (OpenAI, Anthropic). It routes each request to the appropriate model based on simple rules (cheap/fast model for short prompts, more capable model for complex ones), logs every request for cost and usage tracking, caches repeated queries to avoid redundant spend, and exposes metrics for observability — all through an OpenAI-compatible API, so existing client code can point at the gateway with just a base URL change.

**Who uses it:** Any application that currently calls an LLM provider directly. For this project, the primary client is a demo/testing client built alongside the gateway to prove the pattern end-to-end.

**Why it needs to exist:** Calling a single LLM provider directly means no cost optimization (every request uses the same model regardless of complexity), no failover if a provider has an outage, and no centralized visibility into spend or usage patterns.
