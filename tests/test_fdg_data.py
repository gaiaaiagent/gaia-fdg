import pytest
import sqlite3
import json
import tempfile
import os
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fdg_data import process_database


@pytest.fixture
def test_database():
    """Create a temporary test database with sample data."""
    with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as tmp:
        db_path = tmp.name
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE accounts (
            id TEXT PRIMARY KEY,
            name TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE rooms (
            id TEXT PRIMARY KEY
        )
    """)
    
    cursor.execute("""
        CREATE TABLE memories (
            id TEXT PRIMARY KEY,
            type TEXT,
            roomId TEXT,
            userId TEXT,
            agentId TEXT,
            FOREIGN KEY (roomId) REFERENCES rooms(id),
            FOREIGN KEY (userId) REFERENCES accounts(id),
            FOREIGN KEY (agentId) REFERENCES accounts(id)
        )
    """)
    
    # Insert test data
    cursor.execute("INSERT INTO accounts VALUES ('user1', 'Alice')")
    cursor.execute("INSERT INTO accounts VALUES ('agent1', 'Bot')")
    cursor.execute("INSERT INTO rooms VALUES ('room1')")
    cursor.execute("""
        INSERT INTO memories VALUES 
        ('mem1', 'message', 'room1', 'user1', 'agent1')
    """)
    
    conn.commit()
    conn.close()
    
    yield db_path
    
    # Cleanup
    os.unlink(db_path)


@pytest.fixture
def output_file():
    """Create a temporary output file."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
        output_path = tmp.name
    
    yield output_path
    
    # Cleanup
    if os.path.exists(output_path):
        os.unlink(output_path)


def test_process_database_creates_output_file(test_database, output_file):
    """Test that process_database creates the output file."""
    process_database(test_database, output_file)
    assert os.path.exists(output_file)


def test_process_database_returns_valid_json(test_database, output_file):
    """Test that process_database returns valid JSON structure."""
    result = process_database(test_database, output_file)
    
    assert isinstance(result, dict)
    assert 'nodes' in result
    assert 'links' in result
    assert isinstance(result['nodes'], list)
    assert isinstance(result['links'], list)


def test_process_database_creates_correct_nodes(test_database, output_file):
    """Test that process_database creates correct node types."""
    result = process_database(test_database, output_file)
    
    nodes = result['nodes']
    node_types = {node['type'] for node in nodes}
    
    assert 'memory' in node_types
    assert 'account' in node_types
    assert 'room' in node_types
    
    # Check specific nodes
    account_nodes = [n for n in nodes if n['type'] == 'account']
    assert len(account_nodes) == 2
    assert any(n['name'] == 'Alice' for n in account_nodes)
    assert any(n['name'] == 'Bot' for n in account_nodes)
    
    memory_nodes = [n for n in nodes if n['type'] == 'memory']
    assert len(memory_nodes) == 1
    assert memory_nodes[0]['name'] == 'message'
    
    room_nodes = [n for n in nodes if n['type'] == 'room']
    assert len(room_nodes) == 1


def test_process_database_creates_correct_links(test_database, output_file):
    """Test that process_database creates correct links."""
    result = process_database(test_database, output_file)
    
    links = result['links']
    assert len(links) == 3  # memory to room, user, and agent
    
    link_targets = {link['target'] for link in links}
    assert 'room1' in link_targets
    assert 'user1' in link_targets
    assert 'agent1' in link_targets


def test_process_database_handles_missing_relations(test_database, output_file):
    """Test that process_database handles memories with missing relations."""
    # Add a memory with no relations
    conn = sqlite3.connect(test_database)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO memories VALUES 
        ('mem2', 'note', NULL, NULL, NULL)
    """)
    conn.commit()
    conn.close()
    
    result = process_database(test_database, output_file)
    
    # Should have one more memory node
    memory_nodes = [n for n in result['nodes'] if n['type'] == 'memory']
    assert len(memory_nodes) == 2
    
    # Links should still be 3 (no new links for the memory with NULL relations)
    assert len(result['links']) == 3


def test_process_database_file_output_matches_return_value(test_database, output_file):
    """Test that the file output matches the return value."""
    result = process_database(test_database, output_file)
    
    with open(output_file, 'r') as f:
        file_data = json.load(f)
    
    assert file_data == result


def test_process_database_handles_nonexistent_database():
    """Test that process_database raises appropriate error for non-existent database."""
    with tempfile.NamedTemporaryFile(suffix='.json') as tmp:
        # Use a path in a non-existent directory to ensure SQLite won't create it
        with pytest.raises(sqlite3.OperationalError):
            process_database('/nonexistent_dir/nonexistent.db', tmp.name)


def test_empty_database(output_file):
    """Test processing an empty database."""
    with tempfile.NamedTemporaryFile(suffix='.sqlite', delete=False) as tmp:
        db_path = tmp.name
    
    # Create empty database with schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE accounts (
            id TEXT PRIMARY KEY,
            name TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE rooms (
            id TEXT PRIMARY KEY
        )
    """)
    
    cursor.execute("""
        CREATE TABLE memories (
            id TEXT PRIMARY KEY,
            type TEXT,
            roomId TEXT,
            userId TEXT,
            agentId TEXT
        )
    """)
    
    conn.commit()
    conn.close()
    
    try:
        result = process_database(db_path, output_file)
        assert result['nodes'] == []
        assert result['links'] == []
    finally:
        os.unlink(db_path)