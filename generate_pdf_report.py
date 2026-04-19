"""
Fair Trade Supply Chain Tracker — PDF Report Generator
======================================================
Connects to PostgreSQL, runs all key scenarios, and
generates a professional PDF report with formatted tables.
"""

import psycopg2
import datetime
import os
from fpdf import FPDF

DB_CONFIG = {
    "dbname": "fair_trade_tracker",
    "user": "postgres",
    "password": "postgres",
    "host": "localhost",
    "port": "5432"
}

DARK_BG     = (15, 23, 42)
CARD_BG     = (30, 41, 59)
HEADER_BG   = (51, 65, 85)
ACCENT      = (59, 130, 246)
ACCENT2     = (139, 92, 246)
TEXT_LIGHT  = (226, 232, 240)
TEXT_MUTED  = (148, 163, 184)
SUCCESS_BG  = (26, 46, 26)
SUCCESS_TXT = (134, 239, 172)
ERROR_BG    = (45, 27, 27)
ERROR_TXT   = (252, 165, 165)
TABLE_HDR   = (51, 65, 85)
TABLE_EVEN  = (26, 37, 54)
TABLE_ODD   = (30, 41, 59)
WHITE       = (255, 255, 255)


class FTTPdf(FPDF):
    """Custom PDF class with dark-themed styling."""

    def __init__(self):
        super().__init__(orientation='L', unit='mm', format='A4')
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(12, 12, 12)
        # Add Unicode font
        self.add_font("DejaVu", "", os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans.ttf"), uni=True)
        self.add_font("DejaVu", "B", os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans-Bold.ttf"), uni=True)

    def _bg_rect(self):
        """Fill the page background."""
        self.set_fill_color(*DARK_BG)
        self.rect(0, 0, self.w, self.h, 'F')

    def header(self):
        self._bg_rect()

    def footer(self):
        self.set_y(-14)
        self.set_font("DejaVu", "", 7)
        self.set_text_color(*TEXT_MUTED)
        self.cell(0, 10, f"Fair Trade Supply Chain Tracker  |  Page {self.page_no()}/{{nb}}", align='C')

    # ─── Drawing helpers ───

    def section_title(self, num, title):
        """Draw a numbered scenario header."""
        self.ln(6)
        # Badge
        x0 = self.get_x()
        y0 = self.get_y()
        self.set_fill_color(*ACCENT)
        self.set_draw_color(*ACCENT)
        badge_w = 10
        self.rect(x0, y0, badge_w, 8, 'F')
        self.set_font("DejaVu", "B", 9)
        self.set_text_color(*WHITE)
        self.set_xy(x0, y0)
        self.cell(badge_w, 8, str(num), align='C')
        # Title bar
        self.set_fill_color(*CARD_BG)
        self.set_xy(x0 + badge_w, y0)
        self.cell(self.w - 2 * self.l_margin - badge_w, 8, f"  {title}", fill=True)
        self.ln(10)

    def description(self, text):
        """Render a description block."""
        self.set_fill_color(15, 23, 50)
        self.set_draw_color(*ACCENT)
        x0 = self.get_x()
        y0 = self.get_y()
        self.set_font("DejaVu", "", 7.5)
        self.set_text_color(*TEXT_MUTED)
        self.set_x(x0 + 3)
        # Use multi_cell with border trick
        w = self.w - 2 * self.l_margin - 3
        self.multi_cell(w, 5, text, align='L')
        self.ln(3)

    def sql_block(self, sql):
        """Render an SQL code block."""
        self.set_font("DejaVu", "", 6.5)
        self.set_fill_color(15, 23, 42)
        self.set_text_color(125, 211, 252)
        x0 = self.get_x()
        w = self.w - 2 * self.l_margin
        lines = sql.strip().split('\n')
        for line in lines:
            self.set_x(x0)
            self.cell(w, 4, "  " + line, fill=True, ln=True)
        self.ln(3)

    def data_table(self, cols, rows, col_widths=None):
        """Render a data table with alternating row colours."""
        if not cols:
            return

        avail_w = self.w - 2 * self.l_margin
        if col_widths is None:
            col_widths = [avail_w / len(cols)] * len(cols)

        # Ensure col_widths sum to avail_w
        total = sum(col_widths)
        col_widths = [w * avail_w / total for w in col_widths]

        row_h = 5.5

        # Header
        self.set_font("DejaVu", "B", 7)
        self.set_fill_color(*TABLE_HDR)
        self.set_text_color(*TEXT_LIGHT)
        x0 = self.get_x()
        for i, col in enumerate(cols):
            self.cell(col_widths[i], row_h + 1, " " + str(col), border=0, fill=True)
        self.ln(row_h + 1)

        # Rows
        self.set_font("DejaVu", "", 6.5)
        for r_idx, row in enumerate(rows):
            # Check for page break
            if self.get_y() + row_h > self.h - 18:
                self.add_page()

            if r_idx % 2 == 0:
                self.set_fill_color(*TABLE_EVEN)
            else:
                self.set_fill_color(*TABLE_ODD)
            self.set_text_color(203, 213, 225)

            self.set_x(x0)
            for i, val in enumerate(row):
                txt = str(val) if val is not None else "NULL"
                # Truncate if too long
                max_chars = int(col_widths[i] / 1.6)
                if len(txt) > max_chars:
                    txt = txt[:max_chars - 2] + ".."
                self.cell(col_widths[i], row_h, " " + txt, border=0, fill=True)
            self.ln(row_h)

        # Row count
        self.set_font("DejaVu", "", 6)
        self.set_text_color(*TEXT_MUTED)
        self.cell(avail_w, 4, f"({len(rows)} row{'s' if len(rows) != 1 else ''})", align='R')
        self.ln(6)

    def success_box(self, msg):
        """Green success box."""
        self.set_fill_color(*SUCCESS_BG)
        self.set_text_color(*SUCCESS_TXT)
        self.set_font("DejaVu", "", 7)
        self.cell(self.w - 2 * self.l_margin, 7, f"  ✓ {msg}", fill=True, ln=True)
        self.ln(3)

    def error_box(self, msg):
        """Red error box."""
        self.set_fill_color(*ERROR_BG)
        self.set_text_color(*ERROR_TXT)
        self.set_font("DejaVu", "", 7)
        w = self.w - 2 * self.l_margin
        # Handle long messages
        if len(msg) > 140:
            self.multi_cell(w, 5, f"  ✗ ERROR: {msg}", fill=True)
        else:
            self.cell(w, 7, f"  ✗ ERROR: {msg}", fill=True, ln=True)
        self.ln(3)

    def add_image_block(self, path, caption=""):
        """Insert an image with caption."""
        if os.path.exists(path):
            avail_w = self.w - 2 * self.l_margin
            # Limit height
            try:
                self.image(path, x=self.l_margin, w=avail_w)
            except Exception:
                self.set_font("DejaVu", "", 7)
                self.set_text_color(*TEXT_MUTED)
                self.cell(avail_w, 6, f"[Image: {os.path.basename(path)}]", ln=True)
            if caption:
                self.set_font("DejaVu", "", 6)
                self.set_text_color(*TEXT_MUTED)
                self.cell(avail_w, 5, caption, align='C', ln=True)
            self.ln(4)


def connect():
    return psycopg2.connect(**DB_CONFIG)


def run_query(conn, sql):
    cur = conn.cursor()
    cur.execute(sql)
    cols = [desc[0] for desc in cur.description]
    rows = cur.fetchall()
    cur.close()
    return cols, rows


def run_action(conn, sql):
    cur = conn.cursor()
    try:
        cur.execute(sql)
        conn.commit()
        return True, "Query executed successfully."
    except Exception as e:
        conn.rollback()
        return False, str(e).strip().split('\n')[0]
    finally:
        cur.close()


def estimate_col_widths(cols, rows):
    """Estimate column widths based on content."""
    widths = []
    for i, col in enumerate(cols):
        max_len = len(str(col))
        for row in rows[:20]:
            val = str(row[i]) if row[i] is not None else "NULL"
            max_len = max(max_len, len(val))
        widths.append(min(max_len, 40) + 2)
    return widths


def main():
    conn = connect()

    # Check if fonts exist, download if not
    fonts_dir = os.path.join(os.path.dirname(__file__), "fonts")
    os.makedirs(fonts_dir, exist_ok=True)
    dejavu_regular = os.path.join(fonts_dir, "DejaVuSans.ttf")
    dejavu_bold = os.path.join(fonts_dir, "DejaVuSans-Bold.ttf")

    if not os.path.exists(dejavu_regular) or not os.path.exists(dejavu_bold):
        print("Downloading DejaVu fonts...")
        import urllib.request
        import zipfile
        import io
        url = "https://github.com/dejavu-fonts/dejavu-fonts/releases/download/version_2_37/dejavu-fonts-ttf-2.37.zip"
        try:
            data = urllib.request.urlopen(url).read()
            z = zipfile.ZipFile(io.BytesIO(data))
            for name in z.namelist():
                if name.endswith("DejaVuSans.ttf"):
                    with open(dejavu_regular, "wb") as f:
                        f.write(z.read(name))
                elif name.endswith("DejaVuSans-Bold.ttf"):
                    with open(dejavu_bold, "wb") as f:
                        f.write(z.read(name))
            print("Fonts downloaded successfully.")
        except Exception as e:
            print(f"Font download failed: {e}")
            print("Falling back to built-in fonts...")
            # Create a simpler PDF class without custom fonts
            return generate_fallback_pdf(conn)

    pdf = FTTPdf()
    pdf.alias_nb_pages()
    now = datetime.datetime.now().strftime("%B %d, %Y at %I:%M %p")
    base_dir = os.path.dirname(__file__)

    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("DejaVu", "B", 28)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 14, "Fair Trade Supply Chain Tracker", align='C', ln=True)
    pdf.ln(4)
    pdf.set_font("DejaVu", "", 14)
    pdf.set_text_color(*TEXT_LIGHT)
    pdf.cell(0, 10, "Comprehensive Database Output Report", align='C', ln=True)
    pdf.ln(8)
    pdf.set_font("DejaVu", "", 10)
    pdf.set_text_color(*TEXT_MUTED)
    pdf.cell(0, 7, "CS251M — Database Systems Project", align='C', ln=True)
    pdf.cell(0, 7, f"Generated: {now}", align='C', ln=True)
    pdf.ln(6)
    pdf.set_font("DejaVu", "B", 11)
    pdf.set_text_color(*TEXT_LIGHT)
    pdf.cell(0, 8, "Rushil Jain (241EC148)   •   Shresh Parti (241EC252)", align='C', ln=True)

    pdf.ln(20)
    # Tech stack
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(*TEXT_MUTED)
    pdf.cell(0, 6, "PostgreSQL 16  |  SQL (CTEs, Triggers, Views, Functions)  |  Python 3  |  Graphviz", align='C', ln=True)

    pdf.add_page()
    pdf.set_font("DejaVu", "B", 16)
    pdf.set_text_color(*ACCENT)
    pdf.cell(0, 10, "Table of Contents", ln=True)
    pdf.ln(4)

    toc_items = [
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

    pdf.set_font("DejaVu", "", 9)
    for i, item in enumerate(toc_items, 1):
        pdf.set_text_color(*TEXT_MUTED)
        pdf.cell(8, 6, f"{i}.", align='R')
        pdf.set_text_color(*TEXT_LIGHT)
        pdf.cell(0, 6, f"  {item}", ln=True)


    n = 0

    # 1. Schema Overview
    n += 1
    pdf.add_page()
    pdf.section_title(n, toc_items[n-1])
    pdf.description("Overview of all database objects created by setup/setup.sql — 5 tables, 5 triggers, 6 views, and 4 stored functions.")

    sql = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE' ORDER BY table_name;"
    cols, rows = run_query(conn, sql)
    pdf.sql_block(sql)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    sql = "SELECT trigger_name, event_manipulation, event_object_table, action_timing FROM information_schema.triggers WHERE trigger_schema = 'public' ORDER BY event_object_table, action_timing;"
    cols, rows = run_query(conn, sql)
    pdf.sql_block(sql)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    sql = "SELECT table_name AS view_name FROM information_schema.views WHERE table_schema = 'public' ORDER BY table_name;"
    cols, rows = run_query(conn, sql)
    pdf.sql_block(sql)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    sql = """SELECT routine_name
FROM information_schema.routines
WHERE routine_schema = 'public' AND routine_type = 'FUNCTION'
  AND routine_name NOT IN (
      'check_certification','check_transfer_certification',
      'log_batch_insert','log_batch_update','prevent_audit_modification'
  )
ORDER BY routine_name;"""
    cols, rows = run_query(conn, sql)
    pdf.sql_block(sql)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    # 2. Stakeholders & Certs
    n += 1
    pdf.add_page()
    pdf.section_title(n, toc_items[n-1])
    pdf.description("18 stakeholders across 3 supply chains plus 3 edge-case stakeholders (id 16 has an EXPIRED cert, id 17 has NO cert, id 18 has a REVOKED cert). Stakeholders table is fully normalized — all certification state lives in the certifications table.")

    sql = "SELECT id, name, role, created_at FROM stakeholders ORDER BY id;"
    cols, rows = run_query(conn, sql)
    pdf.sql_block(sql)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    sql = """SELECT s.id, s.name, s.role, c.certifying_body, c.issue_date, c.expiry_date, c.is_active
FROM stakeholders s
LEFT JOIN certifications c ON c.stakeholder_id = s.id
ORDER BY s.id;"""
    cols, rows = run_query(conn, sql)
    pdf.sql_block(sql)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    # 3. All Batches
    n += 1
    pdf.add_page()
    pdf.section_title(n, toc_items[n-1])
    pdf.description("24 product batches across Coffee (100-107), Cocoa (200-207), and Cotton (300-307) chains.")

    sql = """SELECT b.id, b.product_name, b.quantity, b.unit, s.name AS owner, s.role
FROM batches b JOIN stakeholders s ON b.current_owner_id = s.id ORDER BY b.id;"""
    cols, rows = run_query(conn, sql)
    pdf.sql_block(sql)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    # 4. Batch Relations
    n += 1
    pdf.add_page()
    pdf.section_title(n, toc_items[n-1])
    pdf.description("Parent-child relationships forming a Directed Acyclic Graph (DAG) — models splitting and merging of batches.")

    sql = """SELECT br.parent_batch_id, pb.product_name AS parent_product,
       br.child_batch_id, cb.product_name AS child_product
FROM batch_relations br
JOIN batches pb ON br.parent_batch_id = pb.id
JOIN batches cb ON br.child_batch_id = cb.id
ORDER BY br.parent_batch_id, br.child_batch_id;"""
    cols, rows = run_query(conn, sql)
    pdf.sql_block(sql)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    # 5. Backward Lineage
    n += 1
    pdf.add_page()
    pdf.section_title(n, toc_items[n-1])
    pdf.description("Traces 'Coffee Retail 1' (batch 106) backward through each supply chain stage to its raw-material origins using a Recursive CTE. UNION (not UNION ALL) collapses duplicate DAG paths.")

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
    pdf.sql_block(sql)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    # 6. Forward Trace
    n += 1
    pdf.add_page()
    pdf.section_title(n, toc_items[n-1])
    pdf.description("Simulates a recall: traces 'Cocoa Raw A' (batch 200) forward to find ALL downstream products affected.")

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
    pdf.sql_block(sql)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    # 7. Cert Trigger — Uncertified
    n += 1
    pdf.add_page()
    pdf.section_title(n, toc_items[n-1])
    pdf.description("The certification_trigger (BEFORE INSERT on batches) rejects any batch whose owner has no valid active certification. Stakeholder 17 (Uncertified Retailer) has no row in the certifications table.")

    sql = "INSERT INTO batches (product_name, quantity, unit, current_owner_id) VALUES ('Illegal Batch', 100, 'kg', 17);"
    pdf.sql_block(sql)
    ok, msg = run_action(conn, sql)
    if ok:
        pdf.success_box(msg)
    else:
        pdf.error_box(msg)

    # 8. Cert Trigger — Expired
    n += 1
    pdf.section_title(n, toc_items[n-1])
    pdf.description("Stakeholder 16 (Expired Farm) holds a certification whose expiry_date = 2020-01-01. Because expiry_date < CURRENT_DATE, the trigger rejects the INSERT.")

    sql_cert = "SELECT id, stakeholder_id, certifying_body, issue_date, expiry_date, is_active FROM certifications WHERE stakeholder_id = 16;"
    cols, rows = run_query(conn, sql_cert)
    pdf.sql_block(sql_cert)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    sql = "INSERT INTO batches (product_name, quantity, unit, current_owner_id) VALUES ('Expired Cert Batch', 100, 'kg', 16);"
    pdf.sql_block(sql)
    ok, msg = run_action(conn, sql)
    if ok:
        pdf.success_box(msg)
    else:
        pdf.error_box(msg)

    # 9. Cert Trigger — Revoked
    n += 1
    pdf.add_page()
    pdf.section_title(n, toc_items[n-1])
    pdf.description("Stakeholder 18 (Revoked Distributor) holds a certification that was administratively revoked (is_active = FALSE). The trigger rejects the INSERT even though the expiry date is in the future.")

    sql_cert = "SELECT id, stakeholder_id, certifying_body, issue_date, expiry_date, is_active FROM certifications WHERE stakeholder_id = 18;"
    cols, rows = run_query(conn, sql_cert)
    pdf.sql_block(sql_cert)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    sql = "INSERT INTO batches (product_name, quantity, unit, current_owner_id) VALUES ('Revoked Cert Batch', 100, 'kg', 18);"
    pdf.sql_block(sql)
    ok, msg = run_action(conn, sql)
    if ok:
        pdf.success_box(msg)
    else:
        pdf.error_box(msg)

    # 10. Transfer Trigger — block transfer to uncertified owner
    n += 1
    pdf.section_title(n, toc_items[n-1])
    pdf.description("The transfer_certification_trigger (BEFORE UPDATE on batches) fires on ownership change. It ensures a certified batch cannot be moved into the custody of an uncertified stakeholder.")

    sql = "UPDATE batches SET current_owner_id = 17 WHERE id = 107;"
    pdf.sql_block(sql)
    ok, msg = run_action(conn, sql)
    if ok:
        pdf.success_box(msg)
    else:
        pdf.error_box(msg)

    # 11. Batch Transfer
    n += 1
    pdf.add_page()
    pdf.section_title(n, toc_items[n-1])
    pdf.description("Demonstrates transfer_batch() function — changes batch ownership, validates certification, and automatically logs to audit trail.")

    sql_before = "SELECT b.id, b.product_name, s.name AS current_owner FROM batches b JOIN stakeholders s ON b.current_owner_id = s.id WHERE b.id = 106;"
    cols, rows = run_query(conn, sql_before)
    pdf.set_font("DejaVu", "B", 7)
    pdf.set_text_color(*TEXT_LIGHT)
    pdf.cell(0, 5, "BEFORE Transfer:", ln=True)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    sql_transfer = "SELECT transfer_batch(106, 4);"
    cols, rows = run_query(conn, sql_transfer)
    pdf.sql_block(sql_transfer)
    pdf.success_box(str(rows[0][0]))

    cols, rows = run_query(conn, sql_before)
    pdf.set_font("DejaVu", "B", 7)
    pdf.set_text_color(*TEXT_LIGHT)
    pdf.cell(0, 5, "AFTER Transfer:", ln=True)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    sql_audit = "SELECT * FROM v_audit_trail WHERE batch_id = 106 ORDER BY timestamp DESC LIMIT 3;"
    cols, rows = run_query(conn, sql_audit)
    pdf.set_font("DejaVu", "B", 7)
    pdf.set_text_color(*TEXT_LIGHT)
    pdf.cell(0, 5, "Audit Trail (transfer logged automatically):", ln=True)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    # Transfer back
    run_query(conn, "SELECT transfer_batch(106, 5);")

    # 10. Audit Immutability
    n += 1
    pdf.add_page()
    pdf.section_title(n, toc_items[n-1])
    pdf.description("The audit_immutability_trigger prevents any UPDATE or DELETE on audit_log — ensuring a tamper-proof, append-only ledger.")

    sql = "UPDATE audit_log SET action = 'hacked' WHERE id = 1;"
    pdf.sql_block(sql)
    ok, msg = run_action(conn, sql)
    pdf.error_box(msg) if not ok else pdf.success_box(msg)

    sql = "DELETE FROM audit_log WHERE id = 1;"
    pdf.sql_block(sql)
    ok, msg = run_action(conn, sql)
    pdf.error_box(msg) if not ok else pdf.success_box(msg)

    # 13. Compliance View
    n += 1
    pdf.add_page()
    pdf.section_title(n, toc_items[n-1])
    pdf.description("Real-time compliance status for every stakeholder. Thanks to edge-case seed data, all four CASE branches appear: COMPLIANT, EXPIRED (id 16), NO CERTIFICATION (id 17), and REVOKED (id 18).")

    sql = "SELECT * FROM v_compliance_overview ORDER BY stakeholder_id;"
    cols, rows = run_query(conn, sql)
    pdf.sql_block(sql)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    # 12. Supply Chain Summary
    n += 1
    pdf.section_title(n, toc_items[n-1])
    pdf.description("Aggregated statistics per product supply chain.")

    sql = "SELECT * FROM v_supply_chain_summary;"
    cols, rows = run_query(conn, sql)
    pdf.sql_block(sql)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    # 13. Final Products & Raw Materials
    n += 1
    pdf.add_page()
    pdf.section_title(n, toc_items[n-1])
    pdf.description("v_final_products shows leaf batches (retail-ready). v_raw_materials shows root batches (farm-origin).")

    sql = "SELECT * FROM v_final_products ORDER BY batch_id;"
    cols, rows = run_query(conn, sql)
    pdf.set_font("DejaVu", "B", 7)
    pdf.set_text_color(*TEXT_LIGHT)
    pdf.cell(0, 5, "Final Retail Products (Leaf Nodes):", ln=True)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    sql = "SELECT * FROM v_raw_materials ORDER BY batch_id;"
    cols, rows = run_query(conn, sql)
    pdf.set_font("DejaVu", "B", 7)
    pdf.set_text_color(*TEXT_LIGHT)
    pdf.cell(0, 5, "Raw Material Sources (Root Nodes):", ln=True)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    # 14. Function — Backward Lineage
    n += 1
    pdf.add_page()
    pdf.section_title(n, toc_items[n-1])
    pdf.description("Wraps recursive CTE into a reusable function. Tracing Chocolate Batch 2 (id=207) back to cocoa farm origins.")

    sql = "SELECT * FROM get_backward_lineage(207);"
    cols, rows = run_query(conn, sql)
    pdf.sql_block(sql)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    # 15. Function — Forward Trace
    n += 1
    pdf.section_title(n, toc_items[n-1])
    pdf.description("Traces Cotton Raw A (id=300) forward to find all downstream clothing products.")

    sql = "SELECT * FROM get_forward_trace(300);"
    cols, rows = run_query(conn, sql)
    pdf.sql_block(sql)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    # 18. Function — Compliance Report
    n += 1
    pdf.add_page()
    pdf.section_title(n, toc_items[n-1])
    pdf.description("Full compliance audit. Shape matches v_compliance_overview, so function and view are interchangeable. Stakeholders 16, 17, 18 are flagged as non-compliant (EXPIRED, NO CERTIFICATION, REVOKED respectively).")

    sql = "SELECT * FROM get_compliance_report();"
    cols, rows = run_query(conn, sql)
    pdf.sql_block(sql)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    # 17. Analytical Queries
    n += 1
    pdf.add_page()
    pdf.section_title(n, toc_items[n-1])
    pdf.description("Aggregate and analytical queries — GROUP BY, HAVING, recursive depth, and audit statistics.")

    sql = """SELECT s.role, SUM(b.quantity) AS total_quantity, COUNT(b.id) AS batch_count
FROM batches b JOIN stakeholders s ON b.current_owner_id = s.id
GROUP BY s.role ORDER BY CASE s.role WHEN 'farmer' THEN 1 WHEN 'processor' THEN 2
WHEN 'distributor' THEN 3 WHEN 'retailer' THEN 4 END;"""
    cols, rows = run_query(conn, sql)
    pdf.set_font("DejaVu", "B", 7)
    pdf.set_text_color(*TEXT_LIGHT)
    pdf.cell(0, 5, "Total Quantity per Supply Chain Stage:", ln=True)
    pdf.sql_block(sql)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    sql = """SELECT b.id, b.product_name, COUNT(br.child_batch_id) AS children_count
FROM batches b LEFT JOIN batch_relations br ON b.id = br.parent_batch_id
GROUP BY b.id, b.product_name HAVING COUNT(br.child_batch_id) > 0
ORDER BY children_count DESC;"""
    cols, rows = run_query(conn, sql)
    pdf.set_font("DejaVu", "B", 7)
    pdf.set_text_color(*TEXT_LIGHT)
    pdf.cell(0, 5, "Branching Factor — Batches with Most Children:", ln=True)
    pdf.sql_block(sql)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

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
    pdf.set_font("DejaVu", "B", 7)
    pdf.set_text_color(*TEXT_LIGHT)
    pdf.cell(0, 5, "Supply Chain Depth per Root Batch:", ln=True)
    pdf.sql_block(sql)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    sql = "SELECT action, COUNT(*) AS total FROM audit_log GROUP BY action ORDER BY total DESC;"
    cols, rows = run_query(conn, sql)
    pdf.set_font("DejaVu", "B", 7)
    pdf.set_text_color(*TEXT_LIGHT)
    pdf.cell(0, 5, "Audit Actions Summary:", ln=True)
    pdf.sql_block(sql)
    pdf.data_table(cols, rows, estimate_col_widths(cols, rows))

    # 18. ER Diagram & Visualization
    n += 1
    pdf.add_page()
    pdf.section_title(n, toc_items[n-1])
    pdf.description("Visual representations of the database schema and supply chain data. Auto-generated using Python + Graphviz.")

    er_path = os.path.join(base_dir, "visualise", "er_diagram.png")
    sc_path = os.path.join(base_dir, "visualise", "supply_chain_graph.png")

    pdf.set_font("DejaVu", "B", 8)
    pdf.set_text_color(*TEXT_LIGHT)
    pdf.cell(0, 6, "Entity-Relationship Diagram:", ln=True)
    pdf.ln(2)
    pdf.add_image_block(er_path, "ER Diagram — 5 tables with foreign key relationships")

    pdf.ln(6)
    pdf.set_font("DejaVu", "B", 8)
    pdf.set_text_color(*TEXT_LIGHT)
    pdf.cell(0, 6, "Supply Chain Graph (Generated from Live Data):", ln=True)
    pdf.ln(2)
    pdf.add_image_block(sc_path, "Supply Chain DAG — 3 chains with color-coded stakeholder roles")

    conn.close()
    output_path = os.path.join(base_dir, "Fair_Trade_Tracker_Report.pdf")
    pdf.output(output_path)
    print(f"PDF report generated: {output_path}")
    return output_path


def generate_fallback_pdf(conn):
    """Fallback using built-in Helvetica if DejaVu fonts fail."""
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.alias_nb_pages()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 24)
    pdf.cell(0, 20, "Fair Trade Supply Chain Tracker - Report", ln=True, align='C')
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 10, "Please install DejaVu fonts to generate the full styled report.", ln=True, align='C')
    pdf.cell(0, 10, "Run: python generate_pdf_report.py again after fonts are downloaded.", ln=True, align='C')
    output = os.path.join(os.path.dirname(__file__), "Fair_Trade_Tracker_Report.pdf")
    pdf.output(output)
    print(f"Fallback PDF generated: {output}")
    conn.close()


if __name__ == "__main__":
    main()
