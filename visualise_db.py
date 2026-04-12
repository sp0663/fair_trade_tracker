import psycopg2
from graphviz import Digraph

# DB connection
conn = psycopg2.connect(
    dbname = "fair_trade_tracker",
    user = "postgres",
    password = "password",
    host = "localhost",
    port = "5432"
)

cur = conn.cursor()

# Create a directed graph
dot = Digraph(comment="Supply Chain")

# Fetch nodes (batches and their current owners)
cur.execute("""
    SELECT b.id, b.product_name, s.name, s.role
    FROM batches b
    JOIN stakeholders s ON b.current_owner_id = s.id;
""")

color_map = {
    "farmer": "lightgreen",
    "processor": "lightblue",
    "distributor": "orange",
    "retailer": "pink"
}

for batch_id, product, owner, role in cur.fetchall():
    label = f"{product}\nID:{batch_id}\n{owner}"
    dot.node(str(batch_id), label,
             style = "filled",
             fillcolor = color_map.get(role, "white"))

# Fetch edges (relationships)
cur.execute("""
    SELECT parent_batch_id, child_batch_id
    FROM batch_relations;
""")

for parent, child in cur.fetchall():
    dot.edge(str(parent), str(child))

# Render the graph to a file and open it
dot.render("supply_chain_graph", format = "png", view = True)

cur.close()
conn.close()