"""
Fair Trade Supply Chain Tracker — Report Generator
===================================================
Connects to the PostgreSQL database, runs all key scenarios,
and generates a comprehensive HTML report with formatted outputs.
"""

import psycopg2
import datetime
import html
import os

DB_CONFIG = {
    "dbname": "fair_trade_tracker",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5432"
}

HTML_HEADER = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Fair Trade Supply Chain Tracker — Database Report</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Fira+Code&display=swap');
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Inter', sans-serif;
    background: #0f172a;
    color: #e2e8f0;
    padding: 40px 60px;
    line-height: 1.6;
  }
  .report-header {
    text-align: center;
    margin-bottom: 50px;
    padding: 40px;
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid #334155;
    border-radius: 16px;
  }
  .report-header h1 {
    font-size: 2.2em;
    background: linear-gradient(135deg, #38bdf8, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
  }
  .report-header .subtitle {
    color: #94a3b8;
    font-size: 1em;
  }
  .report-header .meta {
    color: #64748b;
    font-size: 0.85em;
    margin-top: 12px;
  }
  .scenario {
    margin-bottom: 40px;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    overflow: hidden;
  }
  .scenario-header {
    padding: 18px 24px;
    background: linear-gradient(135deg, #1e3a5f, #1e293b);
    border-bottom: 1px solid #334155;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .scenario-num {
    background: linear-gradient(135deg, #3b82f6, #8b5cf6);
    color: white;
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 0.85em;
    flex-shrink: 0;
  }
  .scenario-header h2 {
    font-size: 1.15em;
    color: #f1f5f9;
  }
  .scenario-body { padding: 20px 24px; }
  .scenario-desc {
    color: #94a3b8;
    font-size: 0.9em;
    margin-bottom: 16px;
    padding: 12px 16px;
    background: #0f172a;
    border-left: 3px solid #3b82f6;
    border-radius: 0 8px 8px 0;
  }
  .query-block {
    margin-bottom: 20px;
  }
  .query-label {
    font-size: 0.8em;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #64748b;
    margin-bottom: 6px;
  }
  .query-sql {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 14px 18px;
    font-family: 'Fira Code', monospace;
    font-size: 0.82em;
    color: #7dd3fc;
    overflow-x: auto;
    white-space: pre-wrap;
    margin-bottom: 14px;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85em;
    margin-bottom: 6px;
  }
  thead th {
    background: #334155;
    color: #e2e8f0;
    padding: 10px 14px;
    text-align: left;
    font-weight: 600;
    border-bottom: 2px solid #475569;
    white-space: nowrap;
  }
  tbody td {
    padding: 9px 14px;
    border-bottom: 1px solid #1e293b;
    color: #cbd5e1;
  }
  tbody tr:nth-child(even) { background: #1a2536; }
  tbody tr:hover { background: #253347; }
  .row-count {
    text-align: right;
    color: #64748b;
    font-size: 0.8em;
    margin-top: 4px;
  }
  .error-box {
    background: #2d1b1b;
    border: 1px solid #7f1d1d;
    border-radius: 8px;
    padding: 14px 18px;
    color: #fca5a5;
    font-family: 'Fira Code', monospace;
    font-size: 0.85em;
    margin-bottom: 14px;
  }
  .success-box {
    background: #1a2e1a;
    border: 1px solid #166534;
    border-radius: 8px;
    padding: 14px 18px;
    color: #86efac;
    font-family: 'Fira Code', monospace;
    font-size: 0.85em;
    margin-bottom: 14px;
  }
  .tag {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75em;
    font-weight: 600;
  }
  .tag-pass { background: #166534; color: #86efac; }
  .tag-fail { background: #7f1d1d; color: #fca5a5; }
  .toc {
    margin-bottom: 40px;
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 24px 30px;
  }
  .toc h3 { color: #f1f5f9; margin-bottom: 14px; }
  .toc-list { list-style: none; }
  .toc-list li {
    padding: 6px 0;
    border-bottom: 1px solid #24334a;
  }
  .toc-list li:last-child { border-bottom: none; }
  .toc-list a {
    color: #7dd3fc;
    text-decoration: none;
    font-size: 0.9em;
  }
  .toc-list a:hover { color: #bae6fd; }
  .images-section { text-align: center; margin: 20px 0; }
  .images-section img {
    max-width: 100%;
    border-radius: 8px;
    border: 1px solid #334155;
    margin: 10px 0;
  }
  .img-caption {
    color: #64748b;
    font-size: 0.8em;
    margin-top: 4px;
    margin-bottom: 20px;
  }
  @media print {
    body { background: white; color: #1e293b; padding: 20px; }
    .scenario { border-color: #d1d5db; page-break-inside: avoid; }
    .scenario-header { background: #f1f5f9; }
    .scenario-num { background: #3b82f6; }
    thead th { background: #e5e7eb; color: #1e293b; }
    tbody td { color: #374151; border-color: #e5e7eb; }
    .query-sql { background: #f8fafc; color: #1e40af; border-color: #d1d5db; }
  }
</style>
</head>
<body>
"""

HTML_FOOTER = """
</body>
</html>
"""


def connect():
    return psycopg2.connect(**DB_CONFIG)


def run_query(conn, sql):
    """Run a SELECT query and return (columns, rows)."""
    cur = conn.cursor()
    cur.execute(sql)
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    cur.close()
    return cols, rows


def run_action(conn, sql):
    """Run a DML/DDL statement. Returns success message or error string."""
    cur = conn.cursor()
    try:
        cur.execute(sql)
        conn.commit()
        return True, "Query executed successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e).strip()
    finally:
        cur.close()


def table_html(cols, rows):
    """Render columns and rows as an HTML table."""
    h = '<table><thead><tr>'
    for c in cols:
        h += f'<th>{html.escape(str(c))}</th>'
    h += '</tr></thead><tbody>'
    for row in rows:
        h += '<tr>'
        for val in row:
            h += f'<td>{html.escape(str(val) if val is not None else "NULL")}</td>'
        h += '</tr>'
    h += '</tbody></table>'
    h += f'<div class="row-count">({len(rows)} row{"s" if len(rows) != 1 else ""})</div>'
    return h


def scenario_html(num, title, desc, blocks):
    """
    blocks: list of dicts with keys:
      - label: str
      - sql: str (optional)
      - type: 'query' | 'action_success' | 'action_error' | 'image'
      - result: str (HTML)
    """
    h = f'<div class="scenario" id="scenario-{num}">'
    h += f'<div class="scenario-header"><div class="scenario-num">{num}</div><h2>{html.escape(title)}</h2></div>'
    h += '<div class="scenario-body">'
    h += f'<div class="scenario-desc">{desc}</div>'
    for blk in blocks:
        h += '<div class="query-block">'
        if blk.get('label'):
            h += f'<div class="query-label">{html.escape(blk["label"])}</div>'
        if blk.get('sql'):
            h += f'<div class="query-sql">{html.escape(blk["sql"])}</div>'
        if blk['type'] == 'query':
            h += blk['result']
        elif blk['type'] == 'action_success':
            h += f'<div class="success-box">✓ {html.escape(blk["result"])}</div>'
        elif blk['type'] == 'action_error':
            h += f'<div class="error-box">✗ ERROR: {html.escape(blk["result"])}</div>'
        elif blk['type'] == 'image':
            h += blk['result']
        h += '</div>'
    h += '</div></div>'
    return h


def main():
    conn = connect()
    report = HTML_HEADER

    now = datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p")
    report += f'''
    <div class="report-header">
        <h1>Fair Trade Supply Chain Tracker</h1>
        <div class="subtitle">Comprehensive Database Output Report</div>
        <div class="meta">CS251M — Database Systems Project &nbsp;|&nbsp; Generated: {now}</div>
        <div class="meta">Rushil Jain (241EC148) &nbsp;&bull;&nbsp; Shresh Parti (241EC252)</div>
    </div>
    '''

    scenarios = [
        "Schema Overview — Tables, Triggers, Views, Functions",
        "Stakeholders & Certifications Data",
        "All Product Batches with Owner Details",
        "Supply Chain Relationships (Batch Relations)",
        "Backward Lineage Tracing — Coffee Retail to Origin",
        "Forward Tracing — Impact Analysis from Raw Material",
        "Certification Trigger — Blocking Uncertified Stakeholder",
        "Certification Trigger — Blocking Expired Certification",
        "Certification Trigger — Blocking Revoked Certification",
        "Transfer Trigger — Blocking Transfer to Uncertified Owner",
        "Batch Transfer with Automatic Audit Logging",
        "Audit Log Immutability — Tamper-Proof Verification",
        "Views — Compliance Overview (all four states)",
        "Views — Supply Chain Summary",
        "Views — Final Retail Products & Raw Materials",
        "Stored Function — get_backward_lineage()",
        "Stored Function — get_forward_trace()",
        "Stored Function — get_compliance_report()",
        "Analytical Queries — Aggregates & Statistics",
        "ER Diagram & Supply Chain Visualization",
    ]

    report += '<div class="toc"><h3>Table of Contents</h3><ol class="toc-list">'
    for i, s in enumerate(scenarios, 1):
        report += f'<li><a href="#scenario-{i}">{i}. {s}</a></li>'
    report += '</ol></div>'

    n = 0

    n += 1
    blocks = []

    sql = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name;"
    cols, rows = run_query(conn, sql)
    blocks.append({"label": "Tables", "sql": sql, "type": "query", "result": table_html(cols, rows)})

    sql = "SELECT trigger_name, event_manipulation, event_object_table, action_timing FROM information_schema.triggers WHERE trigger_schema = 'public' ORDER BY event_object_table, action_timing;"
    cols, rows = run_query(conn, sql)
    blocks.append({"label": "Triggers", "sql": sql, "type": "query", "result": table_html(cols, rows)})

    sql = "SELECT table_name AS view_name FROM information_schema.views WHERE table_schema = 'public' ORDER BY table_name;"
    cols, rows = run_query(conn, sql)
    blocks.append({"label": "Views", "sql": sql, "type": "query", "result": table_html(cols, rows)})

    sql = """SELECT routine_name
FROM information_schema.routines
WHERE routine_schema = 'public' AND routine_type = 'FUNCTION'
  AND routine_name NOT IN (
      'check_certification','check_transfer_certification',
      'log_batch_insert','log_batch_update','prevent_audit_modification'
  )
ORDER BY routine_name;"""
    cols, rows = run_query(conn, sql)
    blocks.append({"label": "Stored Functions (non-trigger)", "sql": sql, "type": "query", "result": table_html(cols, rows)})

    report += scenario_html(n, scenarios[n-1],
        "Overview of all database objects created by <code>setup/setup.sql</code> — 5 tables, 5 triggers, 6 views, and 4 stored functions.",
        blocks)

    n += 1
    blocks = []

    sql = "SELECT id, name, role, created_at FROM stakeholders ORDER BY id;"
    cols, rows = run_query(conn, sql)
    blocks.append({"label": "All Stakeholders", "sql": sql, "type": "query", "result": table_html(cols, rows)})

    sql = """SELECT s.id, s.name, s.role, c.certifying_body, c.issue_date, c.expiry_date, c.is_active
FROM stakeholders s
LEFT JOIN certifications c ON c.stakeholder_id = s.id
ORDER BY s.id;"""
    cols, rows = run_query(conn, sql)
    blocks.append({"label": "Stakeholders joined with their certification rows (LEFT JOIN)", "sql": sql, "type": "query", "result": table_html(cols, rows)})

    report += scenario_html(n, scenarios[n-1],
        "18 stakeholders across 3 supply chains (Coffee, Cocoa, Cotton) plus 3 edge-case stakeholders — one with an <strong>expired</strong> certification (id=16), one with <strong>no</strong> certification (id=17), and one with a <strong>revoked</strong> certification (id=18). Certification state lives entirely in the <code>certifications</code> table; <code>stakeholders</code> is fully normalized.",
        blocks)

    n += 1
    sql = """SELECT b.id, b.product_name, b.quantity, b.unit, s.name AS owner, s.role
FROM batches b JOIN stakeholders s ON b.current_owner_id = s.id ORDER BY b.id;"""
    cols, rows = run_query(conn, sql)
    report += scenario_html(n, scenarios[n-1],
        "24 product batches across Coffee (100-107), Cocoa (200-207), and Cotton (300-307) chains.",
        [{"label": "Query", "sql": sql, "type": "query", "result": table_html(cols, rows)}])

    n += 1
    sql = """SELECT br.parent_batch_id, pb.product_name AS parent_product,
       br.child_batch_id, cb.product_name AS child_product
FROM batch_relations br
JOIN batches pb ON br.parent_batch_id = pb.id
JOIN batches cb ON br.child_batch_id = cb.id
ORDER BY br.parent_batch_id, br.child_batch_id;"""
    cols, rows = run_query(conn, sql)
    report += scenario_html(n, scenarios[n-1],
        "Parent-child relationships forming a Directed Acyclic Graph (DAG) — models splitting and merging of batches through processing stages.",
        [{"label": "Query", "sql": sql, "type": "query", "result": table_html(cols, rows)}])

    n += 1
    sql = """WITH RECURSIVE lineage AS (
    SELECT b.id, b.product_name, s.name AS owner, s.role, 0 AS depth
    FROM batches b JOIN stakeholders s ON b.current_owner_id = s.id
    WHERE b.id = 106
    UNION
    SELECT parent.id, parent.product_name, ps.name, ps.role, l.depth + 1
    FROM batches parent
    JOIN stakeholders ps ON parent.current_owner_id = ps.id
    JOIN batch_relations br ON br.parent_batch_id = parent.id
    JOIN lineage l ON l.id = br.child_batch_id
)
SELECT * FROM lineage ORDER BY depth DESC, id;"""
    cols, rows = run_query(conn, sql)
    report += scenario_html(n, scenarios[n-1],
        "Traces <em>Coffee Retail 1</em> (batch 106) backward through every supply-chain stage to its raw-material origins at the farm level. The recursive CTE walks the <code>batch_relations</code> DAG until no more parents are found; <code>UNION</code> (not <code>UNION ALL</code>) collapses the same node visited through multiple paths.",
        [{"label": "Recursive Backward Lineage Query (batch_id = 106)", "sql": sql, "type": "query", "result": table_html(cols, rows)}])

    n += 1
    sql = """WITH RECURSIVE trace AS (
    SELECT b.id, b.product_name, s.name AS owner, s.role, 0 AS depth
    FROM batches b JOIN stakeholders s ON b.current_owner_id = s.id
    WHERE b.id = 200
    UNION
    SELECT child.id, child.product_name, cs.name, cs.role, t.depth + 1
    FROM batches child
    JOIN stakeholders cs ON child.current_owner_id = cs.id
    JOIN batch_relations br ON br.child_batch_id = child.id
    JOIN trace t ON t.id = br.parent_batch_id
)
SELECT * FROM trace ORDER BY depth, id;"""
    cols, rows = run_query(conn, sql)
    report += scenario_html(n, scenarios[n-1],
        "Simulates a recall: traces <em>Cocoa Raw A</em> (batch 200) forward to find every downstream product that would be affected. Critical for rapid impact analysis.",
        [{"label": "Recursive Forward Trace Query (batch_id = 200)", "sql": sql, "type": "query", "result": table_html(cols, rows)}])

    n += 1
    sql = "INSERT INTO batches (product_name, quantity, unit, current_owner_id) VALUES ('Illegal Batch', 100, 'kg', 17);"
    ok, msg = run_action(conn, sql)
    blocks = [{"label": "Attempt: Insert batch for Uncertified Retailer (stakeholder_id = 17)", "sql": sql,
               "type": "action_success" if ok else "action_error", "result": msg}]
    report += scenario_html(n, scenarios[n-1],
        "The <code>certification_trigger</code> (BEFORE INSERT on <code>batches</code>) prevents any batch creation if the stakeholder lacks a valid active certification. Stakeholder 17 (<em>Uncertified Retailer</em>) has <strong>no row</strong> in the certifications table.",
        blocks)

    n += 1
    sql = "INSERT INTO batches (product_name, quantity, unit, current_owner_id) VALUES ('Expired Cert Batch', 100, 'kg', 16);"
    ok, msg = run_action(conn, sql)
    blocks = [{"label": "Attempt: Insert batch for Expired Farm (stakeholder_id = 16)", "sql": sql,
               "type": "action_success" if ok else "action_error", "result": msg}]

    # Show the offending certification row so the reader can verify the expiry date.
    sql_cert = "SELECT id, stakeholder_id, certifying_body, issue_date, expiry_date, is_active FROM certifications WHERE stakeholder_id = 16;"
    cols, rows = run_query(conn, sql_cert)
    blocks.append({"label": "Verifying the stakeholder's certification (expiry in the past)", "sql": sql_cert, "type": "query", "result": table_html(cols, rows)})

    report += scenario_html(n, scenarios[n-1],
        "Stakeholder 16 (<em>Expired Farm</em>) holds a certification whose <code>expiry_date = 2020-01-01</code>. Because <code>expiry_date &lt; CURRENT_DATE</code>, the trigger rejects the INSERT.",
        blocks)

    n += 1
    sql = "INSERT INTO batches (product_name, quantity, unit, current_owner_id) VALUES ('Revoked Cert Batch', 100, 'kg', 18);"
    ok, msg = run_action(conn, sql)
    blocks = [{"label": "Attempt: Insert batch for Revoked Distributor (stakeholder_id = 18)", "sql": sql,
               "type": "action_success" if ok else "action_error", "result": msg}]
    sql_cert = "SELECT id, stakeholder_id, certifying_body, issue_date, expiry_date, is_active FROM certifications WHERE stakeholder_id = 18;"
    cols, rows = run_query(conn, sql_cert)
    blocks.append({"label": "Verifying the stakeholder's certification (is_active = FALSE)", "sql": sql_cert, "type": "query", "result": table_html(cols, rows)})

    report += scenario_html(n, scenarios[n-1],
        "Stakeholder 18 (<em>Revoked Distributor</em>) holds a certification that was administratively revoked (<code>is_active = FALSE</code>). The trigger rejects the INSERT even though the expiry date is in the future.",
        blocks)

    n += 1
    # Transfer trigger demo: attempt to move a valid batch to an uncertified owner (id=17).
    sql = "UPDATE batches SET current_owner_id = 17 WHERE id = 107;"
    ok, msg = run_action(conn, sql)
    blocks = [{"label": "Attempt: Transfer batch 107 to Uncertified Retailer (stakeholder_id = 17)", "sql": sql,
               "type": "action_success" if ok else "action_error", "result": msg}]
    report += scenario_html(n, scenarios[n-1],
        "The <code>transfer_certification_trigger</code> (BEFORE UPDATE on <code>batches</code>) fires on ownership change only. It guarantees that a certified batch cannot be moved into the custody of an uncertified stakeholder, closing the gap that the INSERT trigger alone would miss.",
        blocks)

    n += 1
    blocks = []

    # Show before state
    sql_before = "SELECT b.id, b.product_name, s.name AS current_owner FROM batches b JOIN stakeholders s ON b.current_owner_id = s.id WHERE b.id = 106;"
    cols, rows = run_query(conn, sql_before)
    blocks.append({"label": "BEFORE Transfer — Batch 106", "sql": sql_before, "type": "query", "result": table_html(cols, rows)})

    # Perform transfer
    sql_transfer = "SELECT transfer_batch(106, 4);"
    cols, rows = run_query(conn, sql_transfer)
    blocks.append({"label": "Execute Transfer Function", "sql": sql_transfer, "type": "query", "result": table_html(cols, rows)})

    # Show after state
    cols, rows = run_query(conn, sql_before)
    blocks.append({"label": "AFTER Transfer — Batch 106", "sql": sql_before, "type": "query", "result": table_html(cols, rows)})

    # Show audit log entry
    sql_audit = "SELECT * FROM v_audit_trail WHERE batch_id = 106 ORDER BY timestamp DESC LIMIT 3;"
    cols, rows = run_query(conn, sql_audit)
    blocks.append({"label": "Audit Trail for Batch 106 (showing transfer logged automatically)", "sql": sql_audit, "type": "query", "result": table_html(cols, rows)})

    # Transfer back for clean state
    run_query(conn, "SELECT transfer_batch(106, 5);")

    report += scenario_html(n, scenarios[n-1],
        "Demonstrates the <code>transfer_batch(batch_id, new_owner_id)</code> stored function, which safely re-assigns ownership. The <code>audit_update_trigger</code> automatically logs a <code>transferred</code> row, and the <code>transfer_certification_trigger</code> validates that the receiving stakeholder is certified.",
        blocks)

    n += 1
    blocks = []

    sql = "UPDATE audit_log SET action = 'hacked' WHERE id = 1;"
    ok, msg = run_action(conn, sql)
    blocks.append({"label": "Attempt: Modify an audit record", "sql": sql,
                   "type": "action_success" if ok else "action_error", "result": msg})

    sql = "DELETE FROM audit_log WHERE id = 1;"
    ok, msg = run_action(conn, sql)
    blocks.append({"label": "Attempt: Delete an audit record", "sql": sql,
                   "type": "action_success" if ok else "action_error", "result": msg})

    report += scenario_html(n, scenarios[n-1],
        "The <code>audit_immutability_trigger</code> rejects any UPDATE or DELETE on <code>audit_log</code>, guaranteeing a tamper-proof, append-only transaction ledger for third-party auditing.",
        blocks)

    n += 1
    sql = "SELECT * FROM v_compliance_overview ORDER BY stakeholder_id;"
    cols, rows = run_query(conn, sql)
    report += scenario_html(n, scenarios[n-1],
        "The <code>v_compliance_overview</code> view provides a real-time compliance status for every stakeholder. Thanks to the edge-case seed data, all four CASE branches appear: <code>COMPLIANT</code>, <code>EXPIRED</code> (id 16), <code>NO CERTIFICATION</code> (id 17), and <code>REVOKED</code> (id 18).",
        [{"label": "Query", "sql": sql, "type": "query", "result": table_html(cols, rows)}])

    n += 1
    sql = "SELECT * FROM v_supply_chain_summary;"
    cols, rows = run_query(conn, sql)
    report += scenario_html(n, scenarios[n-1],
        "Aggregated statistics per product supply chain — total batches, total quantity, and unique stakeholders involved.",
        [{"label": "Query", "sql": sql, "type": "query", "result": table_html(cols, rows)}])

    n += 1
    blocks = []

    sql = "SELECT * FROM v_final_products ORDER BY batch_id;"
    cols, rows = run_query(conn, sql)
    blocks.append({"label": "Final Retail Products (Leaf Nodes)", "sql": sql, "type": "query", "result": table_html(cols, rows)})

    sql = "SELECT * FROM v_raw_materials ORDER BY batch_id;"
    cols, rows = run_query(conn, sql)
    blocks.append({"label": "Raw Material Sources (Root Nodes)", "sql": sql, "type": "query", "result": table_html(cols, rows)})

    report += scenario_html(n, scenarios[n-1],
        "v_final_products shows leaf batches (retail-ready, no downstream children). v_raw_materials shows root batches (farm-origin, no upstream parents).",
        blocks)

    n += 1
    sql = "SELECT * FROM get_backward_lineage(207);"
    cols, rows = run_query(conn, sql)
    report += scenario_html(n, scenarios[n-1],
        "The get_backward_lineage() stored function wraps the recursive CTE into a reusable call. Tracing Chocolate Batch 2 (id=207) back to cocoa farm origins.",
        [{"label": "Function Call", "sql": sql, "type": "query", "result": table_html(cols, rows)}])

    n += 1
    sql = "SELECT * FROM get_forward_trace(300);"
    cols, rows = run_query(conn, sql)
    report += scenario_html(n, scenarios[n-1],
        "The get_forward_trace() function traces Cotton Raw A (id=300) forward to find all downstream clothing products — useful for recall/impact analysis.",
        [{"label": "Function Call", "sql": sql, "type": "query", "result": table_html(cols, rows)}])

    n += 1
    sql = "SELECT * FROM get_compliance_report();"
    cols, rows = run_query(conn, sql)
    report += scenario_html(n, scenarios[n-1],
        "Full compliance audit. Its result shape matches <code>v_compliance_overview</code>, so the function and the view are interchangeable. Stakeholders 16, 17, and 18 are flagged as non-compliant (EXPIRED, NO CERTIFICATION, REVOKED respectively).",
        [{"label": "Function Call", "sql": sql, "type": "query", "result": table_html(cols, rows)}])

    n += 1
    blocks = []

    sql = """SELECT s.role, SUM(b.quantity) AS total_quantity, COUNT(b.id) AS batch_count
FROM batches b JOIN stakeholders s ON b.current_owner_id = s.id
GROUP BY s.role
ORDER BY CASE s.role WHEN 'farmer' THEN 1 WHEN 'processor' THEN 2 WHEN 'distributor' THEN 3 WHEN 'retailer' THEN 4 END;"""
    cols, rows = run_query(conn, sql)
    blocks.append({"label": "Total Quantity per Supply Chain Stage", "sql": sql, "type": "query", "result": table_html(cols, rows)})

    sql = """SELECT b.id, b.product_name, COUNT(br.child_batch_id) AS children_count
FROM batches b LEFT JOIN batch_relations br ON b.id = br.parent_batch_id
GROUP BY b.id, b.product_name HAVING COUNT(br.child_batch_id) > 0
ORDER BY children_count DESC;"""
    cols, rows = run_query(conn, sql)
    blocks.append({"label": "Branching Factor — Batches with Most Children", "sql": sql, "type": "query", "result": table_html(cols, rows)})

    sql = """WITH RECURSIVE chain AS (
    SELECT b.id AS root_id, b.product_name AS root_product, b.id, 0 AS depth
    FROM batches b WHERE b.id NOT IN (SELECT child_batch_id FROM batch_relations)
    UNION ALL
    SELECT c.root_id, c.root_product, br.child_batch_id, c.depth + 1
    FROM chain c JOIN batch_relations br ON br.parent_batch_id = c.id
)
SELECT root_id, root_product, MAX(depth) AS max_chain_depth
FROM chain GROUP BY root_id, root_product ORDER BY root_id;"""
    cols, rows = run_query(conn, sql)
    blocks.append({"label": "Supply Chain Depth per Root Batch", "sql": sql, "type": "query", "result": table_html(cols, rows)})

    sql = "SELECT action, COUNT(*) AS total FROM audit_log GROUP BY action ORDER BY total DESC;"
    cols, rows = run_query(conn, sql)
    blocks.append({"label": "Audit Actions Summary", "sql": sql, "type": "query", "result": table_html(cols, rows)})

    report += scenario_html(n, scenarios[n-1],
        "Aggregate and analytical queries demonstrating GROUP BY, HAVING, recursive depth calculation, and audit statistics.",
        blocks)

    n += 1
    blocks = []
    er_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "visualise", "er_diagram.png"))
    sc_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "visualise", "supply_chain_graph.png"))

    blocks.append({"label": "Entity-Relationship Diagram", "type": "image",
                   "result": f'<div class="images-section"><img src="file:///{er_path.replace(chr(92), "/")}" alt="ER Diagram"><div class="img-caption">ER Diagram — 5 tables with foreign key relationships</div></div>'})
    blocks.append({"label": "Supply Chain Graph (Generated from Data)", "type": "image",
                   "result": f'<div class="images-section"><img src="file:///{sc_path.replace(chr(92), "/")}" alt="Supply Chain Graph"><div class="img-caption">Supply Chain DAG — 3 chains (Coffee, Cocoa, Cotton) with color-coded stakeholder roles</div></div>'})

    report += scenario_html(n, scenarios[n-1],
        "Visual representations of the database schema and the supply chain data. The graph is auto-generated from live database data using Python + Graphviz.",
        blocks)

    report += HTML_FOOTER
    conn.close()

    report_path = os.path.join(os.path.dirname(__file__), "report.html")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    print(f"Report generated: {report_path}")
    return report_path


if __name__ == "__main__":
    main()
