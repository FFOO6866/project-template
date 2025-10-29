"""WebSocket Stability Integration Tests.

Tests WebSocket connection stability, reconnection handling, and error recovery.
NO MOCKING - uses real WebSocket servers and network connections.

Tier 2 (Integration) Requirements:
- Use real Docker services from tests/utils
- NO MOCKING - test actual WebSocket infrastructure
- Test connection stability, timeouts, reconnection
- Validate error handling and recovery scenarios
- Test concurrent WebSocket connections
"""

import pytest
import asyncio
import json
import time
import os
import websockets
import websockets.exceptions
from pathlib import Path
import threading
import subprocess
import signal
import uuid
from datetime import datetime, timedelta
import logging

# Test markers
pytestmark = [pytest.mark.integration, pytest.mark.websocket, pytest.mark.timeout(5)]

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestWebSocketStability:
    """Integration tests for WebSocket connection stability."""
    
    @pytest.fixture(scope="class")
    def websocket_server_process(self):
        """Start real WebSocket server for stability testing."""
        project_root = Path(__file__).parent.parent.parent
        
        # Try to find WebSocket server script
        server_candidates = [
            project_root / "quotations_websocket_server.py",
            project_root / "simple_mcp_websocket_server.py",
            project_root / "test_basic_websocket.py"
        ]
        
        server_script = None
        for candidate in server_candidates:
            if candidate.exists():
                server_script = candidate
                break
        
        if not server_script:
            pytest.skip("No WebSocket server script found for stability testing")
        
        # Set test environment
        test_env = os.environ.copy()
        test_env.update({
            'WEBSOCKET_PORT': '8765',  # Use different port for testing
            'DATABASE_URL': 'sqlite:///test_websocket_stability.db',
            'REDIS_URL': f'redis://localhost:{os.environ.get("REDIS_PORT", "6380")}/2'
        })
        
        # Start WebSocket server
        process = subprocess.Popen([
            'python', str(server_script)
        ], env=test_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(3)
        
        # Verify server is accessible
        max_retries = 10
        server_ready = False
        
        for attempt in range(max_retries):
            try:
                async def check_server():
                    try:
                        async with websockets.connect("ws://localhost:8765") as websocket:
                            await websocket.ping()
                            return True
                    except Exception:
                        return False
                
                if asyncio.run(check_server()):
                    server_ready = True
                    break
            except Exception:
                pass
            
            time.sleep(0.5)
        
        if not server_ready:
            process.terminate()
            pytest.skip("WebSocket server failed to start for stability testing")
        
        yield process
        
        # Cleanup
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()

    def test_websocket_basic_connection_stability(self, websocket_server_process):
        """Test basic WebSocket connection establishment and maintenance."""
        async def test_connection():
            try:
                async with websockets.connect("ws://localhost:8765") as websocket:
                    # Verify connection is established
                    assert websocket.open
                    
                    # Test ping/pong for connection health
                    pong_waiter = await websocket.ping()
                    await asyncio.wait_for(pong_waiter, timeout=2.0)
                    
                    # Connection should still be open
                    assert websocket.open
                    
                    return True
            except Exception as e:
                logger.error(f"Basic connection test failed: {e}")
                return False
        
        result = asyncio.run(test_connection())
        assert result is True

    def test_websocket_message_exchange_stability(self, websocket_server_process):
        """Test stable message exchange over WebSocket connection."""
        async def test_message_exchange():
            try:
                async with websockets.connect("ws://localhost:8765") as websocket:
                    # Send multiple messages to test stability
                    messages_sent = []
                    messages_received = []
                    
                    for i in range(10):
                        message = {
                            "id": str(uuid.uuid4()),
                            "type": "test_message",
                            "sequence": i,
                            "timestamp": datetime.now().isoformat(),
                            "content": f"Test message {i}"
                        }
                        
                        await websocket.send(json.dumps(message))
                        messages_sent.append(message)
                        
                        # Receive echo or response
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                            response_data = json.loads(response)
                            messages_received.append(response_data)
                        except asyncio.TimeoutError:
                            # Some servers might not echo, just log
                            logger.info(f"No response received for message {i}")
                        except json.JSONDecodeError:
                            # Server might send non-JSON, log raw response
                            logger.info(f"Non-JSON response: {response}")
                    
                    # Verify connection remained stable throughout
                    assert websocket.open
                    assert len(messages_sent) == 10
                    
                    return True
                    
            except Exception as e:
                logger.error(f"Message exchange test failed: {e}")
                return False
        
        result = asyncio.run(test_message_exchange())
        assert result is True

    def test_websocket_connection_timeout_handling(self, websocket_server_process):
        """Test WebSocket connection timeout handling."""
        async def test_timeout():
            try:
                # Test connection with short timeout
                async with websockets.connect(
                    "ws://localhost:8765",
                    ping_interval=1,
                    ping_timeout=2,
                    close_timeout=1
                ) as websocket:
                    
                    # Send message and wait
                    test_message = {
                        "type": "timeout_test",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await websocket.send(json.dumps(test_message))
                    
                    # Wait longer than ping timeout to test keepalive
                    await asyncio.sleep(3)
                    
                    # Connection should still be alive due to ping/pong
                    assert websocket.open
                    
                    # Send another message to verify connection
                    await websocket.send(json.dumps({"type": "keepalive_test"}))
                    
                    return True
                    
            except Exception as e:
                logger.error(f"Timeout test failed: {e}")
                return False
        
        result = asyncio.run(test_timeout())
        assert result is True

    def test_websocket_concurrent_connections(self, websocket_server_process):
        """Test multiple concurrent WebSocket connections."""
        async def create_connection(connection_id):
            """Create and maintain a single WebSocket connection."""
            try:
                async with websockets.connect("ws://localhost:8765") as websocket:
                    # Send identification message
                    id_message = {
                        "type": "connection_id",
                        "connection_id": connection_id,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await websocket.send(json.dumps(id_message))
                    
                    # Keep connection alive for a short time
                    await asyncio.sleep(2)
                    
                    # Send final message before closing
                    final_message = {
                        "type": "connection_closing",
                        "connection_id": connection_id
                    }
                    
                    await websocket.send(json.dumps(final_message))
                    
                    return connection_id
                    
            except Exception as e:
                logger.error(f"Connection {connection_id} failed: {e}")
                return None
        
        async def test_concurrent():
            # Create multiple concurrent connections
            num_connections = 8
            tasks = [create_connection(f"conn_{i}") for i in range(num_connections)]
            
            # Wait for all connections to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Count successful connections
            successful = [r for r in results if isinstance(r, str) and r.startswith("conn_")]
            
            # At least 75% of connections should succeed
            success_rate = len(successful) / num_connections
            assert success_rate >= 0.75, f"Only {success_rate:.1%} connections succeeded"
            
            return True
        
        result = asyncio.run(test_concurrent())
        assert result is True

    def test_websocket_connection_recovery(self, websocket_server_process):
        """Test WebSocket connection recovery after disconnection."""
        async def test_recovery():
            connection_attempts = []
            
            # Test multiple connection cycles
            for cycle in range(3):
                try:
                    async with websockets.connect("ws://localhost:8765") as websocket:
                        # Send message to establish connection
                        message = {
                            "type": "recovery_test",
                            "cycle": cycle,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        await websocket.send(json.dumps(message))
                        
                        # Try to receive response
                        try:
                            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                            connection_attempts.append(("success", cycle, response))
                        except asyncio.TimeoutError:
                            connection_attempts.append(("timeout", cycle, None))
                        
                        # Connection closes automatically when leaving context
                        
                except Exception as e:
                    connection_attempts.append(("error", cycle, str(e)))
                
                # Wait between connection attempts
                if cycle < 2:
                    await asyncio.sleep(0.5)
            
            # Verify recovery capability - at least 2 out of 3 cycles should succeed
            successful_cycles = [attempt for attempt in connection_attempts if attempt[0] == "success"]
            assert len(successful_cycles) >= 2, f"Only {len(successful_cycles)} out of 3 recovery cycles succeeded"
            
            return True
        
        result = asyncio.run(test_recovery())
        assert result is True

    def test_websocket_large_message_handling(self, websocket_server_process):
        """Test WebSocket stability with large messages."""
        async def test_large_messages():
            try:
                async with websockets.connect("ws://localhost:8765") as websocket:
                    # Create progressively larger messages
                    message_sizes = [1024, 4096, 16384, 65536]  # 1KB to 64KB
                    
                    for size in message_sizes:
                        # Create large message
                        large_content = "X" * (size - 200)  # Leave room for JSON structure
                        large_message = {
                            "type": "large_message_test",
                            "size": size,
                            "content": large_content,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        message_json = json.dumps(large_message)
                        
                        # Send large message
                        await websocket.send(message_json)
                        
                        # Verify connection is still stable
                        assert websocket.open, f"Connection failed after {size} byte message"
                        
                        # Small delay between messages
                        await asyncio.sleep(0.1)
                    
                    # Send final small message to verify connection health
                    final_message = {"type": "large_message_test_complete"}
                    await websocket.send(json.dumps(final_message))
                    
                    assert websocket.open
                    return True
                    
            except Exception as e:
                logger.error(f"Large message test failed: {e}")
                return False
        
        result = asyncio.run(test_large_messages())
        assert result is True

    def test_websocket_rapid_message_burst(self, websocket_server_process):
        """Test WebSocket stability under rapid message bursts."""
        async def test_message_burst():
            try:
                async with websockets.connect("ws://localhost:8765") as websocket:
                    # Send burst of messages rapidly
                    burst_size = 50
                    start_time = time.time()
                    
                    for i in range(burst_size):
                        message = {
                            "type": "burst_test",
                            "sequence": i,
                            "timestamp": datetime.now().isoformat(),
                            "burst_id": str(uuid.uuid4())
                        }
                        
                        await websocket.send(json.dumps(message))
                        
                        # No delay - send as fast as possible
                    
                    end_time = time.time()
                    burst_duration = end_time - start_time
                    
                    # Verify connection survived the burst
                    assert websocket.open, "Connection failed during message burst"
                    
                    # Verify burst was reasonably fast (should complete in under 2 seconds)
                    assert burst_duration < 2.0, f"Message burst took too long: {burst_duration:.2f}s"
                    
                    # Send confirmation message
                    confirm_message = {
                        "type": "burst_complete",
                        "messages_sent": burst_size,
                        "duration": burst_duration
                    }
                    
                    await websocket.send(json.dumps(confirm_message))
                    
                    return True
                    
            except Exception as e:
                logger.error(f"Message burst test failed: {e}")
                return False
        
        result = asyncio.run(test_message_burst())
        assert result is True

    def test_websocket_connection_interruption_recovery(self, websocket_server_process):
        """Test WebSocket recovery from simulated network interruptions."""
        async def test_interruption_recovery():
            recovery_attempts = []
            
            for attempt in range(5):
                try:
                    # Create connection
                    async with websockets.connect(
                        "ws://localhost:8765",
                        ping_interval=None,  # Disable ping to simulate network issues
                        close_timeout=1
                    ) as websocket:
                        
                        # Send message
                        message = {
                            "type": "interruption_test",
                            "attempt": attempt,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        await websocket.send(json.dumps(message))
                        
                        # Simulate brief interruption by closing connection quickly
                        # Connection will close when context exits
                        
                        recovery_attempts.append(("success", attempt))
                        
                except websockets.exceptions.ConnectionClosedError:
                    recovery_attempts.append(("closed", attempt))
                except Exception as e:
                    recovery_attempts.append(("error", attempt, str(e)))
                
                # Brief pause between attempts
                await asyncio.sleep(0.2)
            
            # Verify recovery capability - most attempts should succeed
            successful_attempts = [attempt for attempt in recovery_attempts 
                                 if attempt[0] == "success"]
            
            success_rate = len(successful_attempts) / len(recovery_attempts)
            assert success_rate >= 0.6, f"Only {success_rate:.1%} recovery attempts succeeded"
            
            return True
        
        result = asyncio.run(test_interruption_recovery())
        assert result is True

    @pytest.mark.slow
    def test_websocket_long_duration_stability(self, websocket_server_process):
        """Test WebSocket connection stability over extended duration."""
        async def test_long_duration():
            try:
                async with websockets.connect(
                    "ws://localhost:8765",
                    ping_interval=5,  # Ping every 5 seconds
                    ping_timeout=3   # 3 second ping timeout
                ) as websocket:
                    
                    start_time = time.time()
                    test_duration = 15  # 15 seconds for integration test
                    message_count = 0
                    
                    while (time.time() - start_time) < test_duration:
                        # Send periodic message
                        message = {
                            "type": "long_duration_test",
                            "message_count": message_count,
                            "elapsed_time": time.time() - start_time,
                            "timestamp": datetime.now().isoformat()
                        }
                        
                        await websocket.send(json.dumps(message))
                        message_count += 1
                        
                        # Verify connection is still open
                        assert websocket.open, f"Connection failed after {message_count} messages"
                        
                        # Wait before next message
                        await asyncio.sleep(1)
                    
                    # Send final message
                    final_message = {
                        "type": "long_duration_complete",
                        "total_messages": message_count,
                        "total_duration": time.time() - start_time
                    }
                    
                    await websocket.send(json.dumps(final_message))
                    
                    # Verify final connection state
                    assert websocket.open
                    assert message_count >= 10  # Should have sent at least 10 messages
                    
                    return True
                    
            except Exception as e:
                logger.error(f"Long duration test failed: {e}")
                return False
        
        result = asyncio.run(test_long_duration())
        assert result is True

    def test_websocket_error_message_handling(self, websocket_server_process):
        """Test WebSocket error message handling and connection stability."""
        async def test_error_handling():
            try:
                async with websockets.connect("ws://localhost:8765") as websocket:
                    # Send various potentially problematic messages
                    problematic_messages = [
                        '{"invalid": "json"',  # Invalid JSON
                        json.dumps({"type": None, "data": "null_type"}),  # Null type
                        json.dumps({"very_large_key": "x" * 10000}),  # Large message
                        "",  # Empty message
                        json.dumps({"unicode": "Testing 🚀 unicode ñ ü ß"}),  # Unicode
                        json.dumps({"nested": {"deeply": {"nested": {"data": "test"}}}}),  # Deep nesting
                    ]
                    
                    successful_sends = 0
                    
                    for i, message in enumerate(problematic_messages):
                        try:
                            await websocket.send(message)
                            successful_sends += 1
                            
                            # Verify connection is still open after potentially problematic message
                            assert websocket.open, f"Connection closed after message {i}"
                            
                            # Brief pause between messages
                            await asyncio.sleep(0.1)
                            
                        except Exception as e:
                            logger.info(f"Expected error for message {i}: {e}")
                            # Connection should still be open even if message failed
                            if websocket.open:
                                successful_sends += 1
                    
                    # At least some messages should be handled gracefully
                    assert successful_sends >= len(problematic_messages) // 2
                    
                    # Send recovery message
                    recovery_message = {
                        "type": "error_handling_complete",
                        "successful_sends": successful_sends
                    }
                    
                    await websocket.send(json.dumps(recovery_message))
                    
                    return True
                    
            except Exception as e:
                logger.error(f"Error handling test failed: {e}")
                return False
        
        result = asyncio.run(test_error_handling())
        assert result is True