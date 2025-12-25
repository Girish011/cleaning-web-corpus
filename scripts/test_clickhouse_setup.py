#!/usr/bin/env python3
"""
Test script to verify ClickHouse setup (T25, T26).

This script tests:
1. Configuration loading
2. ClickHouse client initialization
3. Connection (if ClickHouse is running)
4. Table creation
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config, ClickHouseConfig
from src.db.clickhouse_client import ClickHouseClient
from src.db.schema import create_raw_documents_table

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)

logger = logging.getLogger(__name__)


def test_config_loading():
    """Test 1: Verify configuration loads correctly."""
    print("\n" + "="*60)
    print("Test 1: Configuration Loading")
    print("="*60)
    
    try:
        config = get_config()
        clickhouse_config = config.clickhouse
        
        print(f"✓ Config loaded successfully")
        print(f"  Host: {clickhouse_config.host}")
        print(f"  Port: {clickhouse_config.port}")
        print(f"  Database: {clickhouse_config.database}")
        print(f"  User: {clickhouse_config.user}")
        print(f"  Password: {'***' if clickhouse_config.password else '(empty)'}")
        print(f"  Connect Timeout: {clickhouse_config.connect_timeout}s")
        print(f"  Send/Receive Timeout: {clickhouse_config.send_receive_timeout}s")
        print(f"  Compression: {clickhouse_config.compression}")
        
        return True
    except Exception as e:
        print(f"✗ Config loading failed: {e}")
        return False


def test_client_initialization():
    """Test 2: Verify client can be initialized."""
    print("\n" + "="*60)
    print("Test 2: Client Initialization")
    print("="*60)
    
    try:
        client = ClickHouseClient()
        print(f"✓ Client initialized successfully")
        print(f"  Connection params: {client._connection_params['host']}:{client._connection_params['port']}")
        return True, client
    except Exception as e:
        print(f"✗ Client initialization failed: {e}")
        return False, None


def test_connection(client):
    """Test 3: Verify connection to ClickHouse (if running)."""
    print("\n" + "="*60)
    print("Test 3: Connection Test")
    print("="*60)
    
    if client is None:
        print("✗ Skipped: Client not initialized")
        return False
    
    try:
        client.connect()
        print("✓ Connected to ClickHouse successfully")
        
        # Test a simple query
        result = client.execute("SELECT version()")
        print(f"✓ Query execution works")
        print(f"  ClickHouse version: {result[0][0] if result else 'unknown'}")
        
        # Test database creation
        client.create_database()
        print(f"✓ Database creation/verification works")
        
        client.disconnect()
        return True
    except ConnectionError as e:
        print(f"⚠ Connection failed (ClickHouse may not be running): {e}")
        print("  This is expected if ClickHouse is not installed/running")
        print("  To install: https://clickhouse.com/docs/en/install")
        return None  # Not a failure, just not available
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        return False


def test_table_creation(client):
    """Test 4: Verify table creation."""
    print("\n" + "="*60)
    print("Test 4: Table Creation")
    print("="*60)
    
    if client is None:
        print("✗ Skipped: Client not initialized")
        return False
    
    try:
        # Create table
        create_raw_documents_table(client)
        print("✓ Table creation function executed")
        
        # Verify table exists
        if client.table_exists("raw_documents"):
            print("✓ raw_documents table exists")
            
            # Check table structure
            result = client.execute("DESCRIBE TABLE raw_documents")
            print(f"✓ Table has {len(result)} columns")
            print("\n  Table structure:")
            for row in result[:5]:  # Show first 5 columns
                print(f"    - {row[0]}: {row[1]}")
            if len(result) > 5:
                print(f"    ... and {len(result) - 5} more columns")
            
            return True
        else:
            print("✗ Table does not exist after creation")
            return False
    except ConnectionError:
        print("⚠ Skipped: ClickHouse not running")
        return None
    except Exception as e:
        print(f"✗ Table creation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("ClickHouse Setup Verification (T25, T26)")
    print("="*60)
    
    results = {}
    
    # Test 1: Config loading
    results['config'] = test_config_loading()
    
    # Test 2: Client initialization
    results['client_init'], client = test_client_initialization()
    
    # Test 3: Connection (optional - ClickHouse may not be running)
    results['connection'] = test_connection(client)
    
    # Test 4: Table creation (optional - requires connection)
    results['table'] = test_table_creation(client)
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    for test_name, result in results.items():
        if result is True:
            status = "✓ PASS"
        elif result is None:
            status = "⚠ SKIP (ClickHouse not running)"
        else:
            status = "✗ FAIL"
        print(f"  {test_name:15} {status}")
    
    # Overall result
    critical_tests = ['config', 'client_init']
    if all(results.get(t) for t in critical_tests):
        print("\n✓ Core setup is correct!")
        if results.get('connection') is None:
            print("  Note: ClickHouse connection tests skipped (server not running)")
            print("  Install and start ClickHouse to test full functionality")
        return 0
    else:
        print("\n✗ Some critical tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

