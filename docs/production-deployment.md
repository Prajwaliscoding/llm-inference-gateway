# Production Deployment (AWS EKS)

The gateway has been deployed multiple times to a real AWS environment: EKS cluster, RDS Postgres, HTTPS on a custom domain, and cluster wide observability. Infrastructure is torn down between deployments to avoid ongoing cost, so this document is the permanent record of what a live deployment looks like, along with what actually went wrong along the way and how it got fixed.

## Infrastructure

- **Cluster:** Amazon EKS, `eksctl`-provisioned, 2-node unmanaged node group
- **Ingress:** AWS Load Balancer Controller, provisioning an ALB
- **Database:** RDS Postgres, private subnets only, security-group-scoped to cluster nodes
- **Cache:** Redis, self-hosted in-cluster
- **Domain and TLS:** Route 53 plus an ACM certificate, HTTP redirects to HTTPS
- **Autoscaling:** HPA, 2 to 6 replicas on CPU
- **Access control:** IAM Roles for Service Accounts (IRSA), no static AWS credentials in the cluster
- **Observability:** `kube-prometheus-stack` via Helm, custom `ServiceMonitor`, Grafana public via its own Ingress
- **Frontend:** React app on Vercel, entirely separate from the AWS infrastructure, stays live regardless of backend state

![EKS cluster Active](images/eks-cluster-active.png)

![Gateway pods Running](images/gateway-pods-running.png)

## Database

RDS Postgres is not publicly accessible from the open internet; migrations run from a pod inside the cluster rather than a developer laptop, keeping the database's attack surface minimal.

![RDS instance Available](images/rds-available.png)

## HTTPS

![ACM certificate Issued](images/acm-certificate-issued.png)

![HTTPS verified via curl](images/https-verified.png)

## Observability

The same Grafana dashboard used locally (`grafana/dashboard.json`) was imported into this cluster's Grafana and populated with real traffic.

![Grafana dashboard populated with real data](images/grafana-dashboard-full.png)

## Load testing

Benchmarked with [k6](https://k6.io) against the live deployment, in two separate tests kept under the gateway's own rate limit so the numbers reflect real latency rather than rejected requests.

|     | Cache hit | Live provider call |
| --- | --------- | ------------------ |
| p50 | 56ms      | 550ms              |
| p90 | 66ms      | 945ms              |
| p95 | 96ms      | 1.03s              |

The gateway's own overhead, meaning auth, cache lookup, and response formatting, stays under 100ms at p95. The live provider path is roughly ten times slower, almost entirely due to OpenAI's own round trip time, which the gateway has no control over. Scripts for both tests are in `scripts/load-test-cached.js` and `scripts/load-test-live.js`.

A separate, continuous traffic generator also ran on a dedicated EC2 instance to keep the Grafana dashboard populated with realistic ongoing traffic, distinct from the k6 benchmarks above.

![Traffic generator log showing sustained requests](images/traffic-generator-log.png)

## Failover, demonstrated on demand

Rather than waiting for a real outage, the gateway exposes an admin-only endpoint that forces a provider to appear unhealthy for a set window. This is how failover is shown live, on the deployed playground itself, without needing to break anything real.

```bash
curl -X POST https://gateway.prajwalkhatiwada.com/dashboard/failover-demo \
  -H "Authorization: Bearer <admin-token>" \
  -H "Content-Type: application/json" \
  -d '{"provider": "openai", "seconds": 90}'
```

A request sent to an OpenAI-routed model within that window instead returns a response from Anthropic, visible directly in the response body.

![Successful response during simulated provider outage](images/failover-success-response.png)

## What went wrong rebuilding this, and how it got fixed

Tearing infrastructure down and rebuilding it is not the same as leaving it running. A few real problems came up rebuilding this deployment, in the order they were found.

**The EKS cluster's CloudFormation stack failed to delete cleanly the first time.** A leftover EC2 instance, unrelated to the cluster itself, still held a network interface inside the cluster's subnet, which blocked the subnet and its security group from being deleted. Terminating that instance let the stack delete complete.

**The new cluster landed in a different VPC than the existing RDS instance.** Nothing in a fresh `eksctl create cluster` guarantees the same VPC as before. Getting the two to talk required setting up VPC peering, adding routes in every subnet's route table on both sides, and adding security group rules allowing the cluster's actual node security group, not just the control plane's, to reach RDS on its port.

**Even after peering, connections still timed out.** RDS's default DNS hostname resolves to its public IP when queried from a peered VPC, not its private IP, and the security group rules only allowed the private path. The fix was a Route 53 private hosted zone with an A record pointing directly at RDS's private IP, giving the app a stable internal hostname instead of either the public DNS name or a hardcoded IP.

**The restored database was missing recent schema changes.** The RDS snapshot used to restore the database predated several Alembic migrations. Running `alembic upgrade head` against the live instance, with a temporary security group rule allowing the local machine's IP and SSL required on the connection, brought the schema up to date.

---

Back to **[README](../README.md)**.
