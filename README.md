# Fair Trade Supply Chain Tracker

A relational database system designed to ensure end-to-end transparency and ethical compliance in supply chains. The project enables recursive tracing of product batches, automated certification enforcement, and immutable audit logging to verify Fair Trade claims across all stakeholders.

## Features

* Recursive lineage tracking (backward + forward tracing)
* Certification validation via database triggers
* Immutable audit logging for all transactions
* Support for complex supply chain structures

## Tech Stack

* PostgreSQL
* SQL (CTEs, triggers, constraints)

## Setup

Run the setup script to initialize the database:

```sql
\i setup/setup.sql
```

## Structure

* `schema/` → table definitions
* `triggers/` → enforcement logic
* `queries/` → lineage + analysis queries
* `seed/` → sample data
* `setup/` → full DB initialization
* `docs/` → design documentation

## Collaborators
* Rushil Jain
* Shresh Parti
