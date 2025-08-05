# 🚀 Quickstart - Start Here!

Welcome to Kailash SDK! This is your starting point for building workflow automation.

## 📋 Getting Started in 3 Steps

### 1. Installation
```bash
pip install kailash
```


### 2. Your First Workflow
```python
from kailash.workflow.builder import WorkflowBuilder
from kailash.runtime.local import LocalRuntime

# Create a simple workflow
workflow = WorkflowBuilder()
workflow.add_node("PythonCodeNode", "hello", {
    "code": """
result = {
    'status': 'success',
    'message': 'Hello, Kailash!',
    'timestamp': '2025-08-05T05:30:00Z'
}
"""
})

# Execute it
runtime = LocalRuntime()
results, run_id = runtime.execute(workflow.build())

# Access the result (note the nested structure)
actual_result = results["hello"]["result"]
print(actual_result["message"])  # "Hello, Kailash!"
print(f"Status: {actual_result['status']}")  # "Status: success"
```

✅ **Validated**: This exact example tested and working.

### 3. Common Patterns

#### Database Operations (Working Pattern)
```python
# SQLite database operations - validated working pattern
workflow = WorkflowBuilder()

# Create table
workflow.add_node("SQLDatabaseNode", "create_table", {
    "connection_string": "sqlite:///my_database.db",
    "query": """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            price DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """
})

# Insert data
workflow.add_node("SQLDatabaseNode", "insert_data", {
    "connection_string": "sqlite:///my_database.db", 
    "query": """
        INSERT INTO products (name, category, price) VALUES 
        ('Safety Helmet', 'safety', 25.99),
        ('Power Drill', 'tools', 89.50)
    """
})

# Query data
workflow.add_node("SQLDatabaseNode", "query_data", {
    "connection_string": "sqlite:///my_database.db",
    "query": "SELECT * FROM products WHERE category = 'safety'"
})

# Execute workflow
runtime = LocalRuntime()
results, run_id = runtime.execute(workflow.build())

# Access database results
db_results = results["query_data"]
print(f"Found {db_results['row_count']} safety products")
print(f"Columns: {db_results['columns']}")
for row in db_results['data']:
    print(f"- {row['name']}: ${row['price']}")
```

✅ **Validated**: This exact database pattern tested and working with SQLite.

#### File Operations (Advanced)
```python
# For file operations, ensure proper data formatting
workflow = WorkflowBuilder()
workflow.add_node("CSVReaderNode", "read", {"file_path": "data.csv"})
# Note: CSV data comes as list of dictionaries
workflow.add_node("PythonCodeNode", "count", {
    "code": "result = len(data)"  # Count rows
})

workflow.add_connection("read", "data", "count", "data")

runtime = LocalRuntime()
results, run_id = runtime.execute(workflow.build())
print(f"CSV contains {results['count']['result']} rows")
```

#### AI Analysis
```python
workflow = WorkflowBuilder()
workflow.add_node("LLMAgentNode", "analyzer", {
    "provider": "openai",
    "model": "gpt-4",
    "prompt": "Analyze this data: {data}",
    "temperature": 0.7,
    "max_tokens": 1000
})
```

⚠️ **Note**: Current LLM node implementation shows parameter warnings. The workflow structure is valid but some parameters may be ignored. This is a known limitation being addressed.

## 📚 Next Steps

- **Learn Concepts**: Head to [2-core-concepts/](../2-core-concepts/) to understand nodes and workflows
- **Build Apps**: Check [3-development/](../3-development/) for complete development guides
- **See Examples**: Browse [examples/](../examples/) for real-world workflows

## ⚠️ Common Mistakes to Avoid

1. **Wrong API**: Use string-based node creation, not instances
   ```python
   # ❌ DON'T
   workflow.add_node(CSVReaderNode(), "reader", {})  # Using class instance

   # ✅ DO
   workflow.add_node("CSVReaderNode", "reader", {})
   ```

2. **Wrong Connections**: Use proper output/input names
   ```python
   # ❌ DON'T
   workflow.add_connection("source", "target")  # Missing output/input specification

   # ✅ DO
   workflow.add_connection("source", "result", "target", "input_data")
   ```

3. **Missing Build**: Always call .build() on workflow
   ```python
   # ❌ DON'T
   runtime.execute(workflow)  # Missing .build()

   # ✅ DO
   runtime.execute(workflow.build())
   ```

## 🐳 Docker Deployment

### Running with Docker
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Production Deployment
The SDK is designed for cloud-native deployment:
- **Containerized**: All services run in Docker containers
- **Scalable**: Kubernetes-ready with auto-scaling support
- **Cloud-Agnostic**: Deploy to AWS, GCP, Azure, or on-premises
- **Production-Ready**: Health checks, monitoring, and logging included

## 🔗 Quick Links

- [Installation Guide](installation.md)
- [First Workflow Tutorial](first-workflow.md)
- [Common Patterns](common-patterns.md)
- [Node Selection Guide](../2-core-concepts/nodes/node-selection-guide.md)
- [Troubleshooting](../3-development/troubleshooting.md)
