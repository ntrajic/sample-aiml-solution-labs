# PostgreSQL for Content Viewing Entitlements Database

## Context and Problem Statement

Our content viewing microservice requires a relational database to manage user entitlements, including subscription tiers, content access permissions, and viewing restrictions. The database must handle complex queries for permission checks, support ACID transactions for billing operations, and scale to support millions of users with low-latency access control decisions.

## Considered Options

* PostgreSQL
* MySQL

## Decision Outcome

Chosen option: "PostgreSQL", because it provides superior JSON support for flexible entitlement metadata, better performance for complex permission queries, and stronger data integrity guarantees essential for billing and access control.

### Consequences

* Good, because PostgreSQL's advanced indexing (GIN, GiST) optimizes complex entitlement queries
* Good, because native JSON/JSONB support allows flexible entitlement rule storage without schema changes
* Good, because stronger ACID compliance ensures billing and permission consistency
* Good, because better support for concurrent reads/writes under high load
* Bad, because team has more MySQL experience, requiring additional training
* Bad, because slightly higher memory usage compared to MySQL
