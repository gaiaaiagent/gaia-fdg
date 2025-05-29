# Eliza Force-Directed Graph Visualizer

This tool generates a force-directed graph visualization from an Eliza database.

## Prerequisites

- Python 3.8+
- Poetry
- An Eliza SQLite database file

## Installation

1. Install dependencies using Poetry:
```bash
poetry install
```

## Usage

1. Activate the Poetry shell:
```bash
poetry shell
```

2. Generate the graph data from your database:
```bash
python fdg_data.py <path/to/db.sqlite>
```

This will create a `data.json` file containing the graph data.

3. Start the local web server to view the visualization:
```bash
python -m http.server 3000
```

4. Open your browser and navigate to `http://localhost:3000`

## Example

```bash
poetry install
poetry shell
python fdg_data.py ./db.sqlite
python -m http.server 3000
```

## How it works

The script reads from the Eliza database and creates:
- **Nodes**: Memories, Accounts, and Rooms
- **Links**: Connections between memories and their associated rooms, users, and agents

The visualization shows these relationships as an interactive force-directed graph.