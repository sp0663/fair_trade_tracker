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

Initialize the database by running the setup script.

### Using psql

```bash
psql -U <username> -d <database_name> -f setup/setup.sql
```

### Using pgAdmin

1. Open the Query Tool for your database
2. Open the file `setup/setup.sql`
3. Click **Run**

---

## Seed Data

After setup, populate the database with sample data:

### Using psql

```bash
psql -U <username> -d <database_name> -f setup/seed.sql
```

### Using pgAdmin

1. Open the Query Tool
2. Open the file `setup/seed.sql`
3. Click **Run**


## Structure

* `schema/` → table definitions
* `triggers/` → enforcement logic
* `queries/` → lineage + analysis queries
* `seed/` → sample data
* `setup/` → full DB initialization
* `visualise/` → design visualization

## Collaborators
* Rushil Jain
* Shresh Parti
