"""
Fair Trade Supply Chain Tracker — ER Diagram Generator
======================================================
Introspects the live PostgreSQL database and renders an Entity-Relationship
diagram matching the CURRENT schema. Writes visualise/er_diagram.png.

Run AFTER setup/setup.sql has been loaded, so the diagram reflects what the
database actually contains rather than any manual sketch.
"""

import os
import psycopg2
from graphviz import Digraph

DB_CONFIG = {
    "dbname": "fair_trade_tracker",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5432",
}


TABLE_ORDER = ["stakeholders", "batches", "certifications", "batch_relations", "audit_log"]


def fetch_columns(cur, table):
    """Return a list of (column_name, data_type, is_pk, is_fk, fk_target) tuples."""
    cur.execute(
        """
        SELECT c.column_name, c.data_type
        FROM information_schema.columns c
        WHERE c.table_schema = 'public' AND c.table_name = %s
        ORDER BY c.ordinal_position;
        """,
        (table,),
    )
    cols = cur.fetchall()

    cur.execute(
        """
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
           AND tc.table_schema    = kcu.table_schema
        WHERE tc.table_schema = 'public' AND tc.table_name = %s
          AND tc.constraint_type = 'PRIMARY KEY';
        """,
        (table,),
    )
    pks = {r[0] for r in cur.fetchall()}

    cur.execute(
        """
        SELECT kcu.column_name,
               ccu.table_name  AS ref_table
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
           AND tc.table_schema    = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
           AND ccu.table_schema    = tc.table_schema
        WHERE tc.table_schema = 'public'
          AND tc.table_name   = %s
          AND tc.constraint_type = 'FOREIGN KEY';
        """,
        (table,),
    )
    fks = {r[0]: r[1] for r in cur.fetchall()}

    out = []
    for name, dtype in cols:
        out.append(
            {
                "name": name,
                "type": dtype,
                "pk": name in pks,
                "fk": name in fks,
                "ref": fks.get(name),
            }
        )
    return out


TYPE_SHORT = {
    "integer": "int",
    "text": "text",
    "boolean": "boolean",
    "timestamp without time zone": "timestamp",
    "date": "date",
}


def render_table_node(dot, table, cols):
    header_bg = "#3b5f8a"
    row_bg = "#f1f5f9"
    font_color = "#0f172a"

    # HTML-like label. Each column gets its own row with a port so edges can
    # terminate on the specific attribute (not just the table box).
    label = (
        '<<TABLE BORDER="0" CELLBORDER="1" CELLSPACING="0" CELLPADDING="6">'
        f'<TR><TD BGCOLOR="{header_bg}" ALIGN="LEFT">'
        f'<FONT COLOR="white"><B>  {table}</B></FONT></TD></TR>'
    )
    for col in cols:
        bullet = ""
        if col["pk"]:
            bullet += '<FONT COLOR="#b45309"><B>🔑</B></FONT> '
        if col["fk"]:
            bullet += '<FONT COLOR="#1d4ed8">🔗</FONT> '
        name_str = f"<B>{col['name']}</B>" if col["pk"] else col["name"]
        type_str = TYPE_SHORT.get(col["type"], col["type"])
        label += (
            f'<TR><TD BGCOLOR="{row_bg}" ALIGN="LEFT" PORT="{col["name"]}">'
            f'<FONT COLOR="{font_color}">{bullet}{name_str}'
            f'   <FONT COLOR="#64748b" POINT-SIZE="10">{type_str}</FONT>'
            "</FONT></TD></TR>"
        )
    label += "</TABLE>>"

    dot.node(table, label=label, shape="plaintext")


def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    dot = Digraph("ER", comment="Fair Trade Supply Chain Tracker — ER Diagram")
    dot.attr(rankdir="LR", bgcolor="white", nodesep="0.7", ranksep="1.2",
             fontname="Inter")
    dot.attr("edge", color="#64748b", arrowsize="0.8", penwidth="1.2")

    table_columns = {}
    for table in TABLE_ORDER:
        cols = fetch_columns(cur, table)
        table_columns[table] = cols
        render_table_node(dot, table, cols)

    # Build FK edges: many-side (column) -> one-side (referenced PK).
    for table, cols in table_columns.items():
        for col in cols:
            if col["fk"]:
                # Dashed crow's-foot style (PK side = 'one', FK side = 'many').
                dot.edge(
                    f"{table}:{col['name']}",
                    f"{col['ref']}:id",
                    arrowhead="crow",
                    arrowtail="none",
                    dir="both",
                )

    out_dir = os.path.dirname(__file__)
    out_path = os.path.join(out_dir, "er_diagram")
    dot.render(out_path, format="png", cleanup=True)
    print(f"ER diagram written to {out_path}.png")

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
