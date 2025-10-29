"""
WebSocket Chat Server Integration Tests
========================================

Tests the WebSocket chat server with OpenAI GPT-4 integration.
"""

import asyncio
import json
import os
import sys
from datetime import datetime

import websockets


class WebSocketChatTester:
    """Test WebSocket chat server functionality"""

    def __init__(self, websocket_url: str):
        self.websocket_url = websocket_url
        self.test_results = []

    async def test_connection(self):
        """Test basic WebSocket connection"""
        print("\n🔌 Test 1: WebSocket Connection")
        print("-" * 50)

        try:
            async with websockets.connect(self.websocket_url, ping_interval=None) as websocket:
                # Wait for welcome message
                welcome = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(welcome)

                assert data["type"] == "system", "Expected system message"
                assert "Connected" in data["content"], "Expected connection confirmation"

                print(f"✅ Connection successful")
                print(f"   Welcome message: {data['content']}")
                self.test_results.append(("Connection Test", "PASSED"))
                return True

        except Exception as e:
            print(f"❌ Connection failed: {e}")
            self.test_results.append(("Connection Test", f"FAILED: {e}"))
            return False

    async def test_authentication(self):
        """Test authentication flow"""
        print("\n🔐 Test 2: Authentication")
        print("-" * 50)

        try:
            async with websockets.connect(self.websocket_url, ping_interval=None) as websocket:
                # Skip welcome message
                await websocket.recv()

                # Send authentication
                auth_message = {
                    "type": "auth",
                    "user_id": "test_user",
                    "session_id": "test_session_001"
                }
                await websocket.send(json.dumps(auth_message))

                # Wait for auth response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)

                assert data["type"] == "auth_success", f"Expected auth_success, got {data['type']}"
                assert data["session_id"] == "test_session_001", "Session ID mismatch"
                assert data["user_id"] == "test_user", "User ID mismatch"

                print(f"✅ Authentication successful")
                print(f"   Session ID: {data['session_id']}")
                print(f"   User ID: {data['user_id']}")
                print(f"   Message count: {data['message_count']}")

                # Wait for initial AI greeting
                greeting = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                greeting_data = json.loads(greeting)

                assert greeting_data["type"] == "message", "Expected message type"
                assert greeting_data["message"]["type"] == "ai", "Expected AI message"

                print(f"   AI Greeting: {greeting_data['message']['content'][:100]}...")

                self.test_results.append(("Authentication Test", "PASSED"))
                return True

        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            self.test_results.append(("Authentication Test", f"FAILED: {e}"))
            return False

    async def test_chat_message(self):
        """Test sending chat messages and receiving AI responses"""
        print("\n💬 Test 3: Chat Message Exchange")
        print("-" * 50)

        try:
            async with websockets.connect(self.websocket_url, ping_interval=None) as websocket:
                # Skip welcome message
                await websocket.recv()

                # Authenticate
                auth_message = {
                    "type": "auth",
                    "user_id": "test_user",
                    "session_id": f"test_session_{datetime.utcnow().timestamp()}"
                }
                await websocket.send(json.dumps(auth_message))
                await websocket.recv()  # Auth response
                await websocket.recv()  # Initial greeting

                # Send chat message
                chat_message = {
                    "type": "chat",
                    "content": "Hello, can you help me with a quotation?"
                }
                await websocket.send(json.dumps(chat_message))

                print(f"📤 Sent: {chat_message['content']}")

                # Receive echoed user message
                echo_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                echo_data = json.loads(echo_response)
                assert echo_data["type"] == "message", "Expected message echo"
                assert echo_data["message"]["type"] == "user", "Expected user message"
                print(f"✅ User message echoed")

                # Receive typing indicator
                typing_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                typing_data = json.loads(typing_response)
                assert typing_data["type"] == "typing", "Expected typing indicator"
                assert typing_data["typing"] == True, "Expected typing=True"
                print(f"✅ Typing indicator received")

                # Receive typing stop
                stop_typing_response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                stop_typing_data = json.loads(stop_typing_response)
                print(f"✅ Typing stopped")

                # Receive AI response
                ai_response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                ai_data = json.loads(ai_response)

                assert ai_data["type"] == "message", "Expected message type"
                assert ai_data["message"]["type"] == "ai", "Expected AI message"
                assert len(ai_data["message"]["content"]) > 0, "AI response is empty"

                print(f"📥 AI Response: {ai_data['message']['content'][:200]}...")
                print(f"   Response length: {len(ai_data['message']['content'])} characters")

                self.test_results.append(("Chat Message Test", "PASSED"))
                return True

        except Exception as e:
            print(f"❌ Chat message test failed: {e}")
            self.test_results.append(("Chat Message Test", f"FAILED: {e}"))
            return False

    async def test_context_update(self):
        """Test context update (document, quotation, product)"""
        print("\n📄 Test 4: Context Update")
        print("-" * 50)

        try:
            async with websockets.connect(self.websocket_url, ping_interval=None) as websocket:
                # Skip welcome and authenticate
                await websocket.recv()
                auth_message = {
                    "type": "auth",
                    "user_id": "test_user",
                    "session_id": f"test_session_{datetime.utcnow().timestamp()}"
                }
                await websocket.send(json.dumps(auth_message))
                await websocket.recv()
                await websocket.recv()

                # Send context update
                context_message = {
                    "type": "context",
                    "context": {
                        "type": "document",
                        "name": "Test RFP Document",
                        "document_id": "rfp-test-001"
                    }
                }
                await websocket.send(json.dumps(context_message))

                print(f"📤 Sent context update: {context_message['context']['name']}")

                # Receive context update confirmation
                confirmation = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                confirm_data = json.loads(confirmation)

                assert confirm_data["type"] == "context_updated", "Expected context_updated"
                assert confirm_data["context"]["type"] == "document", "Context type mismatch"
                print(f"✅ Context update confirmed")

                # Receive contextual AI message
                ai_message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                ai_data = json.loads(ai_message)

                assert ai_data["type"] == "message", "Expected message"
                assert ai_data["message"]["type"] == "ai", "Expected AI message"
                print(f"📥 Contextual AI message: {ai_data['message']['content'][:150]}...")

                self.test_results.append(("Context Update Test", "PASSED"))
                return True

        except Exception as e:
            print(f"❌ Context update test failed: {e}")
            self.test_results.append(("Context Update Test", f"FAILED: {e}"))
            return False

    async def test_ping_pong(self):
        """Test ping-pong keep-alive"""
        print("\n🏓 Test 5: Ping-Pong Keep-Alive")
        print("-" * 50)

        try:
            async with websockets.connect(self.websocket_url, ping_interval=None) as websocket:
                await websocket.recv()  # Welcome

                # Send ping
                ping_message = {"type": "ping"}
                await websocket.send(json.dumps(ping_message))

                # Receive pong
                pong_response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                pong_data = json.loads(pong_response)

                assert pong_data["type"] == "pong", f"Expected pong, got {pong_data['type']}"

                print(f"✅ Ping-pong successful")
                self.test_results.append(("Ping-Pong Test", "PASSED"))
                return True

        except Exception as e:
            print(f"❌ Ping-pong test failed: {e}")
            self.test_results.append(("Ping-Pong Test", f"FAILED: {e}"))
            return False

    async def run_all_tests(self):
        """Run all WebSocket tests"""
        print("\n" + "=" * 70)
        print("WebSocket Chat Server Integration Tests")
        print("=" * 70)
        print(f"WebSocket URL: {self.websocket_url}")
        print(f"Test started at: {datetime.utcnow().isoformat()}")

        # Run tests in sequence
        await self.test_connection()
        await asyncio.sleep(1)

        await self.test_authentication()
        await asyncio.sleep(1)

        await self.test_chat_message()
        await asyncio.sleep(1)

        await self.test_context_update()
        await asyncio.sleep(1)

        await self.test_ping_pong()

        # Print summary
        print("\n" + "=" * 70)
        print("Test Summary")
        print("=" * 70)

        passed = sum(1 for _, result in self.test_results if result == "PASSED")
        total = len(self.test_results)

        for test_name, result in self.test_results:
            status_icon = "✅" if result == "PASSED" else "❌"
            print(f"{status_icon} {test_name}: {result}")

        print(f"\nTotal: {passed}/{total} tests passed")
        print(f"Success rate: {(passed/total*100):.1f}%")

        return passed == total


async def main():
    """Main test execution"""
    # Get WebSocket URL from environment or use default
    websocket_url = os.getenv("WEBSOCKET_URL", "ws://localhost/ws")

    print(f"\nConnecting to WebSocket server: {websocket_url}")

    tester = WebSocketChatTester(websocket_url)

    try:
        success = await tester.run_all_tests()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
