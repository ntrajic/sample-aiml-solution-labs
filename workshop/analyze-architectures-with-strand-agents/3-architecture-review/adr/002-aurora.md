# Aurora PostgreSQL for Entitlements Database Hosting

## Context and Problem Statement

Following the decision to use PostgreSQL for our entitlements database, we need to select the optimal AWS hosting solution. The database must support high availability for 24/7 content access, handle variable traffic patterns from streaming peaks, and provide fast failover to minimize service disruption during outages.

## Considered Options

* Amazon RDS for PostgreSQL
* Amazon Aurora PostgreSQL
* Amazon Aurora Serverless v2 PostgreSQL

## Decision Outcome

Chosen option: "Amazon Aurora PostgreSQL", because it provides the best balance of performance, availability, and cost predictability for our consistent entitlements workload with built-in multi-AZ replication and faster recovery times.

### Consequences

* Good, because Aurora's storage auto-scaling eliminates capacity planning for entitlements growth
* Good, because 15 read replicas support high-concurrency permission checks during peak viewing
* Good, because continuous backup to S3 provides point-in-time recovery for billing corrections
* Good, because faster failover (typically under 30 seconds) minimizes content access disruption
* Bad, because higher cost than RDS for predictable workloads
* Bad, because Aurora Serverless v2 would better handle traffic spikes, but adds complexity for consistent workloads
