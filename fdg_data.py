import json
import sqlite3
import sys
from pathlib import Path
import pandas as pd
import argparse

def process_database(db_path, output_file='data.json'):
    """Process the database and generate graph data.
    
    Args:
        db_path: Path to the SQLite database file
        output_file: Path to the output JSON file (default: data.json)
        
    Returns:
        dict: Graph data with nodes and links
    """
    # Connect to the database
    conn = sqlite3.connect(db_path)

    # Get data
    memories = pd.read_sql_query("""
       SELECT memory.id, memory.type, memory.roomId, memory.userId, memory.agentId, 
              a1.name as user_name, a2.name as agent_name
       FROM memories memory
       LEFT JOIN accounts a1 ON memory.userId = a1.id
       LEFT JOIN accounts a2 ON memory.agentId = a2.id
    """, conn)
    
    accounts = pd.read_sql("SELECT id, name FROM accounts", conn)
    rooms = pd.read_sql("SELECT id FROM rooms", conn)
    
    # Create nodes with labels
    nodes = []
    for _, m in memories.iterrows():
       nodes.append({"id": m["id"], "type": "memory", "name": m["type"]})
    for _, a in accounts.iterrows():
       nodes.append({"id": a["id"], "type": "account", "name": a["name"]})
    for _, r in rooms.iterrows():
       nodes.append({"id": r["id"], "type": "room"})
    
    # Create links
    links = []
    for _, m in memories.iterrows():
       if pd.notna(m["roomId"]):
           links.append({"source": m["id"], "target": m["roomId"]})
       if pd.notna(m["userId"]):
           links.append({"source": m["id"], "target": m["userId"]})
       if pd.notna(m["agentId"]):
           links.append({"source": m["id"], "target": m["agentId"]})
    
    conn.close()
    
    graph_data = {"nodes": nodes, "links": links}
    
    with open(output_file, 'w') as f:
       json.dump(graph_data, f)
    
    return graph_data

def main():
    parser = argparse.ArgumentParser(description='Generate force-directed graph data from SQLite database')
    parser.add_argument('db_path', help='Path to the SQLite database file')
    args = parser.parse_args()
    
    process_database(args.db_path)
    print(f"Generated data.json from {args.db_path}")

if __name__ == "__main__":
    main()
