"""
Production MCP Server Integration Demo
=====================================

Demonstrates how to integrate AI agents with the production MCP server,
including session management, tool discovery, and collaborative workflows.

Usage:
    python mcp_agent_integration_demo.py
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional
from datetime import datetime

# Kailash imports for LLM agents
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# MCP client
try:
    from kailash.mcp_server import get_mcp_client, discover_mcp_servers
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("WARNING: MCP client not available")

class MCPAgentDemo:
    """Demonstration of AI agent integration with production MCP server"""
    
    def __init__(self):
        self.mcp_server_config = {
            "name": "production-dataflow-server",
            "transport": "stdio",
            "command": "python",
            "args": ["-m", "production_mcp_server"],
            "env": {},
            "auth": {
                "type": "api_key",
                "key": "agent_key"
            }
        }
        
        self.session_id = None
        self.agent_id = "demo_ai_agent_001"
        
    async def demonstrate_agent_workflows(self):
        """Demonstrate various AI agent workflows with MCP server"""
        
        print("\n" + "="*80)
        print("🤖 PRODUCTION MCP SERVER AI AGENT INTEGRATION DEMO")
        print("="*80)
        
        # 1. Agent Session Management
        await self.demo_session_management()
        
        # 2. Tool Discovery and Usage
        await self.demo_tool_discovery()
        
        # 3. DataFlow Operations
        await self.demo_dataflow_operations()
        
        # 4. Multi-Agent Collaboration
        await self.demo_agent_collaboration()
        
        # 5. Performance Monitoring
        await self.demo_performance_monitoring()
        
        # 6. Complex Workflow Orchestration
        await self.demo_complex_workflows()
        
        print("\n" + "="*80)
        print("✅ DEMO COMPLETED SUCCESSFULLY")
        print("="*80)
    
    async def demo_session_management(self):
        """Demonstrate agent session management"""
        
        print("\n🔐 1. AGENT SESSION MANAGEMENT")
        print("-" * 50)
        
        # Create LLM agent workflow for session management
        workflow = WorkflowBuilder()
        
        workflow.add_node("LLMAgentNode", "session_agent", {
            "provider": "ollama",
            "model": "llama3.2",
            "messages": [
                {"role": "system", "content": "You are an AI agent that manages MCP server sessions. Create and manage your session with the production MCP server."},
                {"role": "user", "content": "Create a new session with the MCP server and get session information."}
            ],
            "mcp_servers": [self.mcp_server_config],
            "auto_discover_tools": True,
            "auto_execute_tools": True,
            "tools_to_use": ["create_agent_session"],
            "tool_parameters": {
                "create_agent_session": {
                    "agent_id": self.agent_id,
                    "agent_info": {
                        "type": "llm_agent",
                        "model": "llama3.2",
                        "capabilities": ["dataflow_operations", "analysis", "reporting"],
                        "version": "1.0.0"
                    },
                    "auth_context": {
                        "permissions": ["dataflow:*", "tools:*"]
                    }
                }
            }
        })
        
        runtime = LocalRuntime()
        
        try:
            print("   Creating agent session...")
            results, run_id = runtime.execute(workflow.build())
            
            session_result = results.get("session_agent", {})
            if session_result.get("success"):
                self.session_id = session_result.get("session_id")
                print(f"   ✅ Session created: {self.session_id}")
                print(f"   🤖 Agent ID: {self.agent_id}")
                print(f"   📊 Run ID: {run_id}")
            else:
                print(f"   ❌ Session creation failed: {session_result.get('error')}")
        
        except Exception as e:
            print(f"   ❌ Session management demo failed: {e}")
    
    async def demo_tool_discovery(self):
        """Demonstrate dynamic tool discovery"""
        
        print("\n🔍 2. DYNAMIC TOOL DISCOVERY")
        print("-" * 50)
        
        workflow = WorkflowBuilder()
        
        workflow.add_node("LLMAgentNode", "discovery_agent", {
            "provider": "ollama",
            "model": "llama3.2",
            "messages": [
                {"role": "system", "content": "You are an AI agent that discovers and analyzes available MCP tools. Discover all available tools and categorize them."},
                {"role": "user", "content": "Discover all available tools in the MCP server and provide a summary of capabilities."}
            ],
            "mcp_servers": [self.mcp_server_config],
            "auto_discover_tools": True,
            "auto_execute_tools": True,
            "tools_to_use": ["get_available_tools"]
        })
        
        runtime = LocalRuntime()
        
        try:
            print("   Discovering available tools...")
            results, run_id = runtime.execute(workflow.build())
            
            discovery_result = results.get("discovery_agent", {})
            
            if discovery_result.get("success"):
                tools = discovery_result.get("tools", [])
                categories = discovery_result.get("categories", [])
                models = discovery_result.get("models", [])
                
                print(f"   ✅ Discovered {len(tools)} tools")
                print(f"   📂 Categories: {', '.join(categories)}")
                print(f"   🗃️  Models: {', '.join(models)}")
                
                # Show top 10 tools
                print("   🔧 Sample Tools:")
                for i, tool in enumerate(tools[:10]):
                    print(f"      {i+1}. {tool['name']} - {tool['description'][:60]}...")
                
            else:
                print(f"   ❌ Tool discovery failed: {discovery_result.get('error')}")
        
        except Exception as e:
            print(f"   ❌ Tool discovery demo failed: {e}")
    
    async def demo_dataflow_operations(self):
        """Demonstrate DataFlow operations through MCP"""
        
        print("\n📊 3. DATAFLOW OPERATIONS")
        print("-" * 50)
        
        # Test different DataFlow operations
        operations = [
            {
                "name": "Create Company",
                "tool": "Company_create",
                "parameters": {
                    "data": {
                        "name": "AI Innovations Inc.",
                        "industry": "artificial_intelligence",
                        "is_active": True
                    },
                    "_session_id": self.session_id,
                    "_agent_id": self.agent_id
                }
            },
            {
                "name": "List Companies",
                "tool": "Company_list",
                "parameters": {
                    "limit": 5,
                    "filters": {"is_active": True},
                    "_session_id": self.session_id,
                    "_agent_id": self.agent_id
                }
            },
            {
                "name": "Create Product Classification",
                "tool": "ProductClassification_create",
                "parameters": {
                    "data": {
                        "product_id": 12345,
                        "unspsc_code": "43233204",
                        "etim_class_id": "EC001234",
                        "confidence_score": 0.95,
                        "classification_method": "ai_hybrid"
                    },
                    "_session_id": self.session_id,
                    "_agent_id": self.agent_id
                }
            }
        ]
        
        for operation in operations:
            print(f"   {operation['name']}...")
            
            workflow = WorkflowBuilder()
            
            workflow.add_node("LLMAgentNode", "dataflow_agent", {
                "provider": "ollama",
                "model": "llama3.2",
                "messages": [
                    {"role": "system", "content": f"You are an AI agent performing DataFlow operations. Execute the {operation['name']} operation."},
                    {"role": "user", "content": f"Execute {operation['name']} with the provided parameters."}
                ],
                "mcp_servers": [self.mcp_server_config],
                "auto_discover_tools": True,
                "auto_execute_tools": True,
                "tools_to_use": [operation['tool']],
                "tool_parameters": {
                    operation['tool']: operation['parameters']
                }
            })
            
            runtime = LocalRuntime()
            
            try:
                results, run_id = runtime.execute(workflow.build())
                
                dataflow_result = results.get("dataflow_agent", {})
                
                if dataflow_result.get("success"):
                    execution_time = dataflow_result.get("metadata", {}).get("execution_time_ms", 0)
                    print(f"      ✅ Completed in {execution_time}ms")
                else:
                    error = dataflow_result.get("error", {})
                    print(f"      ❌ Failed: {error.get('message', 'Unknown error')}")
            
            except Exception as e:
                print(f"      ❌ Operation failed: {e}")
            
            # Small delay between operations
            await asyncio.sleep(0.5)
    
    async def demo_agent_collaboration(self):
        """Demonstrate multi-agent collaboration"""
        
        print("\n🤝 4. MULTI-AGENT COLLABORATION")
        print("-" * 50)
        
        # Create second agent session
        print("   Creating second agent for collaboration...")
        
        workflow = WorkflowBuilder()
        
        workflow.add_node("LLMAgentNode", "collaboration_setup", {
            "provider": "ollama",
            "model": "llama3.2",
            "messages": [
                {"role": "system", "content": "You are setting up agent collaboration. Create a second agent session."},
                {"role": "user", "content": "Create a second agent session for collaboration demonstration."}
            ],
            "mcp_servers": [self.mcp_server_config],
            "auto_discover_tools": True,
            "auto_execute_tools": True,
            "tools_to_use": ["create_agent_session"],
            "tool_parameters": {
                "create_agent_session": {
                    "agent_id": "demo_ai_agent_002",
                    "agent_info": {
                        "type": "llm_agent",
                        "model": "llama3.2",
                        "capabilities": ["analysis", "reporting"],
                        "version": "1.0.0"
                    }
                }
            }
        })
        
        runtime = LocalRuntime()
        
        try:
            results, run_id = runtime.execute(workflow.build())
            
            collaboration_result = results.get("collaboration_setup", {})
            
            if collaboration_result.get("success"):
                partner_session_id = collaboration_result.get("session_id")
                print(f"   ✅ Second agent session created: {partner_session_id}")
                
                # Enable collaboration
                print("   Enabling collaboration between agents...")
                
                collab_workflow = WorkflowBuilder()
                
                collab_workflow.add_node("LLMAgentNode", "enable_collaboration", {
                    "provider": "ollama",
                    "model": "llama3.2",
                    "messages": [
                        {"role": "system", "content": "You are enabling collaboration between two AI agents."},
                        {"role": "user", "content": "Enable collaboration between the two agent sessions."}
                    ],
                    "mcp_servers": [self.mcp_server_config],
                    "auto_discover_tools": True,
                    "auto_execute_tools": True,
                    "tools_to_use": ["enable_agent_collaboration"],
                    "tool_parameters": {
                        "enable_agent_collaboration": {
                            "session_id": self.session_id,
                            "partner_session_id": partner_session_id
                        }
                    }
                })
                
                collab_results, _ = runtime.execute(collab_workflow.build())
                
                collab_result = collab_results.get("enable_collaboration", {})
                
                if collab_result.get("success"):
                    print("   ✅ Agent collaboration enabled")
                    collab_context = collab_result.get("collaboration_context", {})
                    print(f"   🤝 Active collaborations: {collab_context.get('active_collaborations', 0)}")
                else:
                    print(f"   ❌ Collaboration failed: {collab_result.get('error')}")
            
            else:
                print(f"   ❌ Second agent session creation failed: {collaboration_result.get('error')}")
        
        except Exception as e:
            print(f"   ❌ Collaboration demo failed: {e}")
    
    async def demo_performance_monitoring(self):
        """Demonstrate performance monitoring and metrics"""
        
        print("\n📈 5. PERFORMANCE MONITORING")
        print("-" * 50)
        
        workflow = WorkflowBuilder()
        
        workflow.add_node("LLMAgentNode", "metrics_agent", {
            "provider": "ollama",
            "model": "llama3.2",
            "messages": [
                {"role": "system", "content": "You are an AI agent monitoring MCP server performance. Collect and analyze server metrics."},
                {"role": "user", "content": "Get comprehensive server metrics and performance data."}
            ],
            "mcp_servers": [self.mcp_server_config],
            "auto_discover_tools": True,
            "auto_execute_tools": True,
            "tools_to_use": ["get_server_metrics"]
        })
        
        runtime = LocalRuntime()
        
        try:
            print("   Collecting server metrics...")
            results, run_id = runtime.execute(workflow.build())
            
            metrics_result = results.get("metrics_agent", {})
            
            if metrics_result.get("success"):
                server_metrics = metrics_result.get("server_metrics", {})
                session_analytics = metrics_result.get("session_analytics", {})
                
                print("   ✅ Metrics collected successfully")
                print(f"   📊 Total requests: {server_metrics.get('total_requests', 0)}")
                print(f"   ⚡ Avg response time: {server_metrics.get('average_response_time_ms', 0):.1f}ms")
                print(f"   📈 Error rate: {server_metrics.get('error_rate_percent', 0):.1f}%")
                print(f"   🔧 Active tools: {server_metrics.get('total_tools_registered', 0)}")
                print(f"   🤖 Active sessions: {session_analytics.get('active_sessions', 0)}")
                print(f"   💾 Memory usage: {server_metrics.get('memory_usage_mb', 0):.1f}MB")
                
                # Show most used tools
                most_used = server_metrics.get('most_used_tools', {})
                if most_used:
                    print("   🔝 Most used tools:")
                    for tool, count in list(most_used.items())[:5]:
                        print(f"      • {tool}: {count} times")
            
            else:
                print(f"   ❌ Metrics collection failed: {metrics_result.get('error')}")
        
        except Exception as e:
            print(f"   ❌ Performance monitoring demo failed: {e}")
    
    async def demo_complex_workflows(self):
        """Demonstrate complex multi-step workflows"""
        
        print("\n🔄 6. COMPLEX WORKFLOW ORCHESTRATION")
        print("-" * 50)
        
        # Complex workflow: Create customer, add classification, generate report
        print("   Executing complex multi-step workflow...")
        
        workflow = WorkflowBuilder()
        
        # Step 1: Create customer
        workflow.add_node("LLMAgentNode", "step1_customer", {
            "provider": "ollama",
            "model": "llama3.2",
            "messages": [
                {"role": "system", "content": "You are creating a new customer record as part of a complex workflow."},
                {"role": "user", "content": "Create a new customer record for the workflow."}
            ],
            "mcp_servers": [self.mcp_server_config],
            "auto_discover_tools": True,
            "auto_execute_tools": True,
            "tools_to_use": ["Customer_create"],
            "tool_parameters": {
                "Customer_create": {
                    "data": {
                        "name": "TechFlow Solutions",
                        "email": "contact@techflow.com",
                        "industry": "technology",
                        "is_active": True
                    },
                    "_session_id": self.session_id,
                    "_agent_id": self.agent_id
                }
            }
        })
        
        # Step 2: Create quote
        workflow.add_node("LLMAgentNode", "step2_quote", {
            "provider": "ollama",
            "model": "llama3.2",
            "messages": [
                {"role": "system", "content": "You are creating a quote for the customer."},
                {"role": "user", "content": "Create a quote for the customer."}
            ],
            "mcp_servers": [self.mcp_server_config],
            "auto_discover_tools": True,
            "auto_execute_tools": True,
            "tools_to_use": ["Quote_create"],
            "tool_parameters": {
                "Quote_create": {
                    "data": {
                        "customer_id": 1,  # Would be from previous step in real scenario
                        "total_amount": 50000.00,
                        "status": "draft",
                        "valid_until": "2024-12-31"
                    },
                    "_session_id": self.session_id,
                    "_agent_id": self.agent_id
                }
            }
        })
        
        # Step 3: Get analytics
        workflow.add_node("LLMAgentNode", "step3_analytics", {
            "provider": "ollama",
            "model": "llama3.2",
            "messages": [
                {"role": "system", "content": "You are generating analytics for the workflow completion."},
                {"role": "user", "content": "Generate server metrics as workflow completion analytics."}
            ],
            "mcp_servers": [self.mcp_server_config],
            "auto_discover_tools": True,
            "auto_execute_tools": True,
            "tools_to_use": ["get_server_metrics"]
        })
        
        # Connect workflow steps
        workflow.connect("step1_customer", "step2_quote")
        workflow.connect("step2_quote", "step3_analytics")
        
        runtime = LocalRuntime()
        
        try:
            start_time = time.time()
            results, run_id = runtime.execute(workflow.build())
            execution_time = time.time() - start_time
            
            print(f"   ✅ Complex workflow completed in {execution_time:.2f}s")
            print(f"   📊 Run ID: {run_id}")
            
            # Show results from each step
            for step_name in ["step1_customer", "step2_quote", "step3_analytics"]:
                step_result = results.get(step_name, {})
                if step_result.get("success"):
                    print(f"   ✅ {step_name}: Success")
                else:
                    error = step_result.get("error", {})
                    print(f"   ❌ {step_name}: {error.get('message', 'Failed')}")
        
        except Exception as e:
            print(f"   ❌ Complex workflow demo failed: {e}")
    
    async def demo_health_check(self):
        """Demonstrate server health monitoring"""
        
        print("\n🏥 HEALTH CHECK")
        print("-" * 50)
        
        workflow = WorkflowBuilder()
        
        workflow.add_node("LLMAgentNode", "health_agent", {
            "provider": "ollama",
            "model": "llama3.2",
            "messages": [
                {"role": "system", "content": "You are performing a health check on the MCP server."},
                {"role": "user", "content": "Perform a comprehensive health check of the server."}
            ],
            "mcp_servers": [self.mcp_server_config],
            "auto_discover_tools": True,
            "auto_execute_tools": True,
            "tools_to_use": ["health_check"]
        })
        
        runtime = LocalRuntime()
        
        try:
            print("   Performing health check...")
            results, run_id = runtime.execute(workflow.build())
            
            health_result = results.get("health_agent", {})
            
            if health_result.get("success"):
                health_status = health_result.get("health_status", "unknown")
                components = health_result.get("components", {})
                
                print(f"   ✅ Health check completed")
                print(f"   🎯 Overall status: {health_status.upper()}")
                
                for component, info in components.items():
                    status = info.get("status", "unknown")
                    print(f"   • {component}: {status.upper()}")
                    if info.get("error"):
                        print(f"     Error: {info['error']}")
            
            else:
                print(f"   ❌ Health check failed: {health_result.get('error')}")
        
        except Exception as e:
            print(f"   ❌ Health check demo failed: {e}")

async def main():
    """Main demo function"""
    
    if not MCP_AVAILABLE:
        print("❌ MCP client not available. Please install kailash[mcp] to run this demo.")
        return
    
    demo = MCPAgentDemo()
    
    try:
        await demo.demonstrate_agent_workflows()
        await demo.demo_health_check()
        
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
