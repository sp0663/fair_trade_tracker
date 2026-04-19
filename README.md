# Fair Trade Supply Chain Tracker

A relational database system designed to ensure end-to-end transparency and ethical compliance in supply chains. The project enables recursive tracing of product batches, automated certification enforcement, and immutable audit logging to verify Fair Trade claims across all stakeholders.

## Features

* Recursive lineage tracking (backward + forward tracing) over a DAG of batch relations
* Certification validation on both INSERT and transfer (UPDATE) via database triggers
* Immutable audit logging for every `created` / `updated` / `transferred` event
* Compliance view distinguishing COMPLIANT / EXPIRED / REVOKED / NO CERTIFICATION
* Python report generator that produces a styled HTML run-report

## Tech Stack

* PostgreSQL 16
* SQL — CTEs, triggers, views, stored functions, constraints
* Python 3 — psycopg2, Graphviz

## Project Structure

```
schema/      table definitions (read-only reference; also inlined in setup.sql)
triggers/    individual trigger files (read-only reference; also inlined in setup.sql)
queries/     views.sql, procedures.sql, sample recursive queries, test_queries.sql
seed/        seed_data.sql — 18 stakeholders, 17 certs, 24 batches, 24 DAG edges
setup/       setup.sql — ONE-SHOT bootstrap that creates everything
visualise/   visualise_db.py, er_diagram generator, generated PNGs
```

## Quick start

1. Create an empty database:

   ```bash
   createdb -U postgres fair_trade_tracker
   ```

2. Run the bootstrap (creates tables, triggers, views, and stored functions):

   ```bash
   psql -U postgres -d fair_trade_tracker -f setup/setup.sql
   ```

3. Load seed data:

   ```bash
   psql -U postgres -d fair_trade_tracker -f seed/seed_data.sql
   ```

4. Generate the HTML run-report:

   ```bash
   pip install -r requirements.txt
   python generate_report.py          # writes report.html
   ```

   Optional: `python generate_pdf_report.py` writes `Fair_Trade_Tracker_Report.pdf`.

### Using pgAdmin instead of psql

Open the Query Tool and run `setup/setup.sql` followed by `seed/seed_data.sql`.

### Regenerating the diagrams

```bash
python visualise/generate_er_diagram.py      # -> visualise/er_diagram.png
python visualise/visualise_db.py             # -> visualise/supply_chain_graph.png
```

## What `setup.sql` creates

| Kind      | Count | Objects |
|-----------|------:|---------|
| Tables    | 5     | `stakeholders`, `batches`, `certifications`, `batch_relations`, `audit_log` |
| Triggers  | 5     | `certification_trigger`, `transfer_certification_trigger`, `audit_insert_trigger`, `audit_update_trigger`, `audit_immutability_trigger` |
| Views     | 6     | `v_batch_details`, `v_compliance_overview`, `v_audit_trail`, `v_supply_chain_summary`, `v_final_products`, `v_raw_materials` |
| Functions | 4     | `transfer_batch`, `get_backward_lineage`, `get_forward_trace`, `get_compliance_report` |

(The individual files under `schema/` and `triggers/` are kept as read-only reference copies so each concern can be reviewed in isolation. `setup/setup.sql` is the single source of truth for building the DB.)

## Collaborators

* Rushil Jain (241EC148)
* Shresh Parti (241EC252)
