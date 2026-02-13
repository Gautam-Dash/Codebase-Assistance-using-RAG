"""Database module for handling data persistence."""
import json
from typing import Any, Dict, List


class DatabaseError(Exception):
    """Raised when database operations fail."""
    pass


class SimpleDatabase:
    """A simple in-memory database."""
    
    def __init__(self):
        """Initialize the database."""
        self.data: Dict[str, List[Dict[str, Any]]] = {}
    
    def create_table(self, table_name: str) -> None:
        """Create a new table."""
        if table_name in self.data:
            raise DatabaseError(f"Table {table_name} already exists")
        self.data[table_name] = []
    
    def insert(self, table_name: str, record: Dict[str, Any]) -> None:
        """Insert a record into a table."""
        if table_name not in self.data:
            raise DatabaseError(f"Table {table_name} does not exist")
        record["id"] = len(self.data[table_name])
        self.data[table_name].append(record)
    
    def select(self, table_name: str) -> List[Dict[str, Any]]:
        """Select all records from a table."""
        if table_name not in self.data:
            raise DatabaseError(f"Table {table_name} does not exist")
        return self.data[table_name]
    
    def update(self, table_name: str, record_id: int, updates: Dict[str, Any]) -> None:
        """Update a record."""
        if table_name not in self.data:
            raise DatabaseError(f"Table {table_name} does not exist")
        
        for record in self.data[table_name]:
            if record.get("id") == record_id:
                record.update(updates)
                return
        
        raise DatabaseError(f"Record {record_id} not found")
    
    def delete(self, table_name: str, record_id: int) -> None:
        """Delete a record."""
        if table_name not in self.data:
            raise DatabaseError(f"Table {table_name} does not exist")
        
        self.data[table_name] = [
            r for r in self.data[table_name] if r.get("id") != record_id
        ]


class ConnectionPool:
    """Manages database connections."""
    
    def __init__(self, max_connections: int = 10):
        """Initialize connection pool."""
        self.max_connections = max_connections
        self.available_connections = max_connections
    
    def acquire(self) -> Dict[str, Any]:
        """Acquire a connection from the pool."""
        if self.available_connections <= 0:
            raise DatabaseError("No available connections")
        self.available_connections -= 1
        return {"connection_id": id(self)}
    
    def release(self, connection: Dict[str, Any]) -> None:
        """Release a connection back to the pool."""
        self.available_connections += 1
