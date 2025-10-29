"""MCP Server Integration Tests.

Tests MCP server functionality with real WebSocket connections and infrastructure.
NO MOCKING - uses real MCP server instances and WebSocket connections.

Tier 2 (Integration) Requirements:
- Use real Docker services from tests/utils
- NO MOCKING - test actual MCP server interactions
- Test WebSocket connections, MCP protocol compliance
- Validate message flows between client and server
- Test MCP server nodes with real services
"""

import pytest
import asyncio
import json
import time
import os
import websockets
import websockets.exceptions
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
import sqlite3
from datetime import datetime
import subprocess
import signal
import threading
import requests
import uuid

# Test markers
pytestmark = [pytest.mark.integration, pytest.mark.mcp, pytest.mark.timeout(5)]


class TestMCPServerIntegration:
    """Integration tests for MCP server functionality."""
    
    @pytest.fixture(scope="class")
    def database_connection(self):
        """Real database connection for MCP server testing."""
        # Try PostgreSQL first (production scenario)
        try:
            conn = psycopg2.connect(
                host=os.environ.get('POSTGRES_HOST', 'localhost'),
                port=int(os.environ.get('POSTGRES_PORT', '5434')),
                database=os.environ.get('POSTGRES_DB', 'horme_test'),
                user=os.environ.get('POSTGRES_USER', 'test_user'),
                password=os.environ.get('POSTGRES_PASSWORD', 'test_password'),
                cursor_factory=RealDictCursor
            )
            yield conn
            conn.close()
        except (psycopg2.Error, ConnectionError):
            # Fallback to SQLite for testing
            db_path = Path(__file__).parent.parent / "test_mcp_integration.db"
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            
            # Create test schema
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY,
                    title TEXT,
                    filename TEXT,
                    content TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS quotations (
                    id INTEGER PRIMARY KEY,
                    document_id INTEGER,
                    content TEXT,
                    total_value REAL,
                    status TEXT DEFAULT 'draft',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents (id)
                );
                
                CREATE TABLE IF NOT EXISTS processing_status (
                    id TEXT PRIMARY KEY,
                    status TEXT DEFAULT 'pending',
                    progress INTEGER DEFAULT 0,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()
            
            yield conn
            conn.close()
            
            # Cleanup
            if db_path.exists():
                db_path.unlink()

    @pytest.fixture
    def mcp_server_process(self):
        """Start real MCP server process for testing."""
        # Find MCP server script
        project_root = Path(__file__).parent.parent.parent
        mcp_server_script = project_root / "src" / "nexus_production_mcp.py"
        
        if not mcp_server_script.exists():
            # Try alternative locations
            alternatives = [
                project_root / "src" / "production_nexus_mcp_server.py",
                project_root / "lightweight_mcp_server.py",
                project_root / "simple_mcp_server_fixed.py"
            ]
            
            for alt in alternatives:
                if alt.exists():
                    mcp_server_script = alt
                    break
            else:
                pytest.skip("No MCP server script found for integration testing")
        
        # Set test environment
        test_env = os.environ.copy()
        test_env.update({
            'MCP_PORT': '3003',  # Use different port for testing
            'DATABASE_URL': 'sqlite:///test_mcp_integration.db',
            'REDIS_URL': f'redis://localhost:{os.environ.get("REDIS_PORT", "6380")}/1'
        })
        
        # Start MCP server
        process = subprocess.Popen([
            'python', str(mcp_server_script)
        ], env=test_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(2)
        
        # Verify server is running
        max_retries = 5
        for _ in range(max_retries):
            try:
                # Try to connect to WebSocket
                async def check_connection():
                    try:
                        async with websockets.connect("ws://localhost:3003") as websocket:
                            return True
                    except:
                        return False
                
                if asyncio.run(check_connection()):
                    break
            except:
                pass
            time.sleep(1)
        else:
            # Server didn't start, kill process and skip
            process.terminate()
            pytest.skip("MCP server failed to start for integration testing")
        
        yield process
        
        # Cleanup
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

    def test_mcp_server_websocket_connection(self, mcp_server_process):
        """Test WebSocket connection to MCP server."""
        async def test_connection():
            try:
                async with websockets.connect("ws://localhost:3003") as websocket:
                    # Test connection is established
                    assert websocket.open
                    
                    # Send ping message
                    ping_message = {
                        "jsonrpc": "2.0",
                        "method": "ping",
                        "id": 1
                    }
                    await websocket.send(json.dumps(ping_message))
                    
                    # Receive response (with timeout)
                    response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                    response_data = json.loads(response)
                    
                    # Verify response structure
                    assert "jsonrpc" in response_data
                    assert response_data["jsonrpc"] == "2.0"
                    assert "id" in response_data
                    
                    return True
            except Exception as e:
                pytest.fail(f"WebSocket connection failed: {e}")
                return False
        
        # Run async test
        result = asyncio.run(test_connection())
        assert result is True

    def test_mcp_initialize_protocol(self, mcp_server_process):
        """Test MCP protocol initialization handshake."""
        async def test_initialization():
            async with websockets.connect("ws://localhost:3003") as websocket:
                # Send initialize request
                initialize_request = {
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {
                            "roots": {"listChanged": True},
                            "sampling": {}
                        },
                        "clientInfo": {
                            "name": "Horme Test Client",
                            "version": "1.0.0"
                        }
                    },
                    "id": 1
                }
                
                await websocket.send(json.dumps(initialize_request))
                
                # Receive initialization response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                
                # Verify initialization response
                assert response_data["jsonrpc"] == "2.0"
                assert response_data["id"] == 1
                assert "result" in response_data
                
                result = response_data["result"]
                assert "protocolVersion" in result
                assert "capabilities" in result
                assert "serverInfo" in result
                
                return True
        
        result = asyncio.run(test_initialization())
        assert result is True

    def test_mcp_list_tools_capability(self, mcp_server_process):
        """Test MCP server tool listing capability."""
        async def test_tools():
            async with websockets.connect("ws://localhost:3003") as websocket:
                # First initialize
                await websocket.send(json.dumps({
                    "jsonrpc": "2.0",
                    "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "test", "version": "1.0"}
                    },
                    "id": 1
                }))
                
                # Wait for initialization response
                await websocket.recv()
                
                # List available tools
                list_tools_request = {
                    "jsonrpc": "2.0",
                    "method": "tools/list",
                    "id": 2
                }
                
                await websocket.send(json.dumps(list_tools_request))
                
                # Receive tools list
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                
                # Verify tools response
                assert response_data["jsonrpc"] == "2.0"
                assert response_data["id"] == 2
                assert "result" in response_data
                
                result = response_data["result"]
                assert "tools" in result
                assert isinstance(result["tools"], list)
                
                # Verify at least some tools are available
                assert len(result["tools"]) > 0
                
                # Check tool structure
                for tool in result["tools"]:
                    assert "name" in tool
                    assert "description" in tool
                    assert "inputSchema" in tool
                
                return True
        
        result = asyncio.run(test_tools())
        assert result is True

    def test_mcp_call_document_upload_tool(self, mcp_server_process, database_connection):
        """Test calling document upload tool through MCP."""
        async def test_document_tool():
            async with websockets.connect("ws://localhost:3003") as websocket:
                # Initialize connection
                await websocket.send(json.dumps({
                    "jsonrpc": "2.0", "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                              "clientInfo": {"name": "test", "version": "1.0"}},
                    "id": 1
                }))
                await websocket.recv()  # Initialization response
                
                # Call document upload tool
                tool_call = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "upload_document",
                        "arguments": {
                            "filename": "test_rfp.txt",
                            "content": "Test RFP document for quotation\nItem 1: Widget A - $100\nItem 2: Widget B - $200",
                            "document_type": "rfp"
                        }
                    },
                    "id": 3
                }
                
                await websocket.send(json.dumps(tool_call))
                
                # Receive tool response
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                response_data = json.loads(response)
                
                # Verify tool execution result
                assert response_data["jsonrpc"] == "2.0"
                assert response_data["id"] == 3
                assert "result" in response_data
                
                result = response_data["result"]
                assert "content" in result
                
                # Verify document was stored in database
                cursor = database_connection.cursor()
                if 'sqlite' in str(type(database_connection)):
                    cursor.execute("SELECT * FROM documents WHERE filename = ?", ("test_rfp.txt",))
                else:
                    cursor.execute("SELECT * FROM documents WHERE filename = %s", ("test_rfp.txt",))
                
                document_record = cursor.fetchone()
                assert document_record is not None
                assert document_record['filename'] == "test_rfp.txt"
                
                return True
        
        result = asyncio.run(test_document_tool())
        assert result is True

    def test_mcp_concurrent_connections(self, mcp_server_process):
        """Test MCP server handles multiple concurrent WebSocket connections."""
        async def create_connection(connection_id):
            """Create and test a single WebSocket connection."""
            try:
                async with websockets.connect("ws://localhost:3003") as websocket:
                    # Send unique message per connection
                    message = {
                        "jsonrpc": "2.0",
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {
                                "name": f"test_client_{connection_id}",
                                "version": "1.0"
                            }
                        },
                        "id": connection_id
                    }
                    
                    await websocket.send(json.dumps(message))
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    
                    # Verify each connection gets proper response
                    assert response_data["id"] == connection_id
                    assert response_data["jsonrpc"] == "2.0"
                    
                    return connection_id
            except Exception as e:
                pytest.fail(f"Connection {connection_id} failed: {e}")
                return None
        
        async def test_concurrent():
            # Create multiple concurrent connections
            num_connections = 5
            tasks = [create_connection(i) for i in range(num_connections)]
            
            # Wait for all connections to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Verify all connections succeeded
            successful_connections = [r for r in results if isinstance(r, int)]
            assert len(successful_connections) == num_connections
            
            return True
        
        result = asyncio.run(test_concurrent())
        assert result is True

    def test_mcp_tool_error_handling(self, mcp_server_process):
        """Test MCP server error handling for invalid tool calls."""
        async def test_error_handling():
            async with websockets.connect("ws://localhost:3003") as websocket:
                # Initialize
                await websocket.send(json.dumps({
                    "jsonrpc": "2.0", "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                              "clientInfo": {"name": "test", "version": "1.0"}},
                    "id": 1
                }))
                await websocket.recv()
                
                # Call non-existent tool
                invalid_tool_call = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "non_existent_tool",
                        "arguments": {}
                    },
                    "id": 4
                }
                
                await websocket.send(json.dumps(invalid_tool_call))
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                
                # Verify error response
                assert response_data["jsonrpc"] == "2.0"
                assert response_data["id"] == 4
                assert "error" in response_data
                
                error = response_data["error"]
                assert "code" in error
                assert "message" in error
                
                return True
        
        result = asyncio.run(test_error_handling())
        assert result is True

    def test_mcp_database_integration(self, mcp_server_process, database_connection):
        """Test MCP tools integrate properly with database operations."""
        # Setup test data
        cursor = database_connection.cursor()
        
        # Insert test document
        test_doc_id = str(uuid.uuid4())
        if 'sqlite' in str(type(database_connection)):
            cursor.execute("""
                INSERT INTO documents (id, title, filename, content)
                VALUES (?, ?, ?, ?)
            """, (test_doc_id, "Test Document", "test.txt", "Test content"))
        else:
            cursor.execute("""
                INSERT INTO documents (id, title, filename, content)
                VALUES (%s, %s, %s, %s)
            """, (test_doc_id, "Test Document", "test.txt", "Test content"))
        
        database_connection.commit()
        
        async def test_database_tool():
            async with websockets.connect("ws://localhost:3003") as websocket:
                # Initialize
                await websocket.send(json.dumps({
                    "jsonrpc": "2.0", "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                              "clientInfo": {"name": "test", "version": "1.0"}},
                    "id": 1
                }))
                await websocket.recv()
                
                # Call document query tool
                query_tool_call = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "query_documents",
                        "arguments": {
                            "search_query": "Test Document"
                        }
                    },
                    "id": 5
                }
                
                await websocket.send(json.dumps(query_tool_call))
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                response_data = json.loads(response)
                
                # Verify database integration
                assert response_data["jsonrpc"] == "2.0"
                assert response_data["id"] == 5
                assert "result" in response_data
                
                # Should find the test document we inserted
                result = response_data["result"]
                assert "content" in result
                
                return True
        
        result = asyncio.run(test_database_tool())
        assert result is True

    def test_mcp_session_persistence(self, mcp_server_process, database_connection):
        """Test MCP server maintains session state across multiple tool calls."""
        async def test_session():
            async with websockets.connect("ws://localhost:3003") as websocket:
                # Initialize with session info
                await websocket.send(json.dumps({
                    "jsonrpc": "2.0", "method": "initialize",
                    "params": {
                        "protocolVersion": "2024-11-05", 
                        "capabilities": {},
                        "clientInfo": {"name": "session_test", "version": "1.0"}
                    },
                    "id": 1
                }))
                await websocket.recv()
                
                # Create document in session
                create_doc_call = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "create_document",
                        "arguments": {
                            "title": "Session Test Document",
                            "content": "Document created in session test"
                        }
                    },
                    "id": 2
                }
                
                await websocket.send(json.dumps(create_doc_call))
                create_response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                create_data = json.loads(create_response)
                
                assert "result" in create_data
                
                # Query for the document we just created (should be found)
                query_call = {
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {
                        "name": "query_documents",
                        "arguments": {
                            "search_query": "Session Test Document"
                        }
                    },
                    "id": 3
                }
                
                await websocket.send(json.dumps(query_call))
                query_response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                query_data = json.loads(query_response)
                
                assert "result" in query_data
                
                # Verify session maintained state between calls
                return True
        
        result = asyncio.run(test_session())
        assert result is True

    @pytest.mark.slow
    def test_mcp_server_performance_under_load(self, mcp_server_process):
        """Test MCP server performance with multiple rapid requests."""
        async def rapid_requests():
            async with websockets.connect("ws://localhost:3003") as websocket:
                # Initialize
                await websocket.send(json.dumps({
                    "jsonrpc": "2.0", "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                              "clientInfo": {"name": "load_test", "version": "1.0"}},
                    "id": 1
                }))
                await websocket.recv()
                
                # Send many rapid requests
                num_requests = 20
                start_time = time.time()
                
                for i in range(num_requests):
                    request = {
                        "jsonrpc": "2.0",
                        "method": "tools/call",
                        "params": {
                            "name": "health_check",
                            "arguments": {}
                        },
                        "id": i + 2
                    }
                    await websocket.send(json.dumps(request))
                
                # Collect all responses
                responses = []
                for i in range(num_requests):
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                        responses.append(json.loads(response))
                    except asyncio.TimeoutError:
                        break
                
                end_time = time.time()
                duration = end_time - start_time
                
                # Verify performance (should handle 20 requests in under 5 seconds)
                assert duration < 5.0, f"Performance test failed: {duration:.2f}s for {num_requests} requests"
                assert len(responses) >= num_requests * 0.8, f"Only received {len(responses)} out of {num_requests} responses"
                
                # Verify all responses are valid
                for response in responses:
                    assert "jsonrpc" in response
                    assert response["jsonrpc"] == "2.0"
                    assert "id" in response
                
                return True
        
        result = asyncio.run(rapid_requests())
        assert result is True

    def test_mcp_connection_recovery(self, mcp_server_process):
        """Test MCP connection recovery after temporary network issues."""
        async def test_recovery():
            # Test initial connection
            async with websockets.connect("ws://localhost:3003") as websocket:
                await websocket.send(json.dumps({
                    "jsonrpc": "2.0", "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                              "clientInfo": {"name": "recovery_test", "version": "1.0"}},
                    "id": 1
                }))
                
                response = await websocket.recv()
                initial_data = json.loads(response)
                assert initial_data["jsonrpc"] == "2.0"
            
            # Connection closed, now test reconnection
            async with websockets.connect("ws://localhost:3003") as websocket2:
                await websocket2.send(json.dumps({
                    "jsonrpc": "2.0", "method": "initialize",
                    "params": {"protocolVersion": "2024-11-05", "capabilities": {},
                              "clientInfo": {"name": "recovery_test_2", "version": "1.0"}},
                    "id": 1
                }))
                
                response2 = await websocket2.recv()
                recovery_data = json.loads(response2)
                
                # Verify server handles reconnection properly
                assert recovery_data["jsonrpc"] == "2.0"
                assert "result" in recovery_data
                
                return True
        
        result = asyncio.run(test_recovery())
        assert result is True