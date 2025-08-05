#!/usr/bin/env python3
"""
MY FIRST WORKING WORKFLOW
=========================

A complete working workflow using:
1. SQLite database (already created by previous tests)
2. Kailash SDK with correct node names
3. Real business logic processing
4. Actual useful output

This workflow reads data from your SQLite database and processes it.
"""

import sys
import sqlite3
from pathlib import Path

# Apply Windows compatibility
try:
    import windows_sdk_compatibility
    print("[INFO] Windows SDK compatibility applied")
except ImportError:
    print("[WARNING] Windows SDK compatibility not available")

def create_working_workflow():
    """Create a workflow that actually works with your data"""
    
    print("Creating My First Working Workflow")
    print("="*40)
    
    try:
        from kailash.workflow.builder import WorkflowBuilder
        from kailash.runtime.local import LocalRuntime
        
        print("[SUCCESS] SDK imports successful")
        
        # Check if database exists
        db_path = Path("immediate_test.db")
        if not db_path.exists():
            print("[INFO] Database not found, creating it first...")
            # Run the immediate test to create database
            import subprocess
            result = subprocess.run([sys.executable, "test_immediate_working_pattern.py"], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("[ERROR] Could not create database")
                return False
        
        print(f"[SUCCESS] Database found: {db_path}")
        
        # Create workflow
        workflow = WorkflowBuilder()
        
        # Node 1: Read data from SQLite database
        workflow.add_node("PythonCodeNode", "read_products", {
            "code": '''
import sqlite3
import json

# Connect to database
conn = sqlite3.connect("immediate_test.db")
cursor = conn.cursor()

# Get all products with classifications
cursor.execute("""
    SELECT p.name, p.unspsc_code, 
           COUNT(cr.id) as classification_count,
           AVG(cr.confidence) as avg_confidence
    FROM products p
    LEFT JOIN classification_results cr ON p.id = cr.product_id
    GROUP BY p.id, p.name, p.unspsc_code
    ORDER BY avg_confidence DESC
""")

products = cursor.fetchall()
conn.close()

# Format results
result = {
    "products": [
        {
            "name": row[0],
            "unspsc_code": row[1], 
            "classification_count": row[2],
            "avg_confidence": float(row[3]) if row[3] else 0.0
        }
        for row in products
    ],
    "total_products": len(products)
}

print(f"Loaded {len(products)} products from database")
'''
        })
        
        # Node 2: Process and analyze the data
        workflow.add_node("PythonCodeNode", "analyze_data", {
            "code": '''
# Get data from previous node
products_data = inputs.get("read_products", {}).get("result", {})
products = products_data.get("products", [])

if not products:
    result = {"error": "No products found"}
else:
    # Analyze product data
    total_products = len(products)
    classified_products = [p for p in products if p["classification_count"] > 0]
    high_confidence = [p for p in products if p["avg_confidence"] > 0.9]
    
    # Calculate statistics
    total_classifications = sum(p["classification_count"] for p in products)
    avg_confidence_overall = sum(p["avg_confidence"] for p in products) / total_products if total_products > 0 else 0
    
    result = {
        "analysis": {
            "total_products": total_products,
            "classified_products": len(classified_products),
            "high_confidence_products": len(high_confidence),
            "total_classifications": total_classifications,
            "overall_avg_confidence": round(avg_confidence_overall, 3),
            "classification_rate": round(len(classified_products) / total_products * 100, 1) if total_products > 0 else 0
        },
        "top_products": sorted(products, key=lambda x: x["avg_confidence"], reverse=True)[:3]
    }
    
    print(f"Analysis complete: {total_products} products, {len(classified_products)} classified")
'''
        })
        
        # Node 3: Generate business report
        workflow.add_node("PythonCodeNode", "generate_report", {
            "code": '''
import json
from datetime import datetime

# Get analysis from previous node
analysis_data = inputs.get("analyze_data", {}).get("result", {})
analysis = analysis_data.get("analysis", {})
top_products = analysis_data.get("top_products", [])

if "error" in analysis_data:
    result = {"report": "Error: No data to analyze"}
else:
    # Generate business report
    report_lines = [
        "BUSINESS INTELLIGENCE REPORT",
        "=" * 30,
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "PRODUCT CLASSIFICATION SUMMARY:",
        f"  Total Products: {analysis.get('total_products', 0)}",
        f"  Classified Products: {analysis.get('classified_products', 0)}",
        f"  Classification Rate: {analysis.get('classification_rate', 0)}%",
        f"  High Confidence Products: {analysis.get('high_confidence_products', 0)}",
        f"  Overall Average Confidence: {analysis.get('overall_avg_confidence', 0)}",
        "",
        "TOP PERFORMING PRODUCTS:",
    ]
    
    for i, product in enumerate(top_products, 1):
        report_lines.append(f"  {i}. {product['name']} (Confidence: {product['avg_confidence']:.3f})")
    
    report_lines.extend([
        "",
        "RECOMMENDATIONS:",
        "- Focus on improving low-confidence classifications",
        "- Review products without UNSPSC codes",
        "- Consider automated classification for new products"
    ])
    
    result = {
        "report": "\\n".join(report_lines),
        "metrics": analysis,
        "timestamp": datetime.now().isoformat()
    }
    
    print("Business report generated successfully")
'''
        })
        
        print("\n[SUCCESS] Workflow built with 3 nodes:")
        print("  1. read_products - Reads from SQLite database")
        print("  2. analyze_data - Processes and analyzes data")  
        print("  3. generate_report - Creates business intelligence report")
        
        # Execute the workflow
        print("\n[EXECUTING] Running workflow...")
        runtime = LocalRuntime()
        results, run_id = runtime.execute(workflow.build())
        
        print(f"\n[SUCCESS] Workflow executed successfully!")
        print(f"Run ID: {run_id}")
        
        # Display the business report
        if "generate_report" in results:
            report_data = results["generate_report"].get("result", {})
            if "report" in report_data:
                print("\n" + "="*60)
                print("BUSINESS INTELLIGENCE REPORT OUTPUT")
                print("="*60)
                print(report_data["report"])
                print("="*60)
                
                # Show metrics
                metrics = report_data.get("metrics", {})
                print(f"\nKEY METRICS:")
                print(f"  Classification Rate: {metrics.get('classification_rate', 0)}%")
                print(f"  Average Confidence: {metrics.get('overall_avg_confidence', 0)}")
                print(f"  High Confidence Products: {metrics.get('high_confidence_products', 0)}")
            else:
                print("\n[WARNING] Report generated but content not found")
        else:
            print("\n[WARNING] Report generation step not found in results")
        
        # Show all results for debugging
        print(f"\n[DEBUG] Available result keys: {list(results.keys())}")
        for key, value in results.items():
            if isinstance(value, dict) and "result" in value:
                result_content = value["result"]
                if isinstance(result_content, dict):
                    print(f"  {key}: {list(result_content.keys())}")
                else:
                    print(f"  {key}: {type(result_content)}")
        
        return True
        
    except ImportError as e:
        print(f"[ERROR] SDK not available: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the working workflow"""
    
    print("MY FIRST WORKING WORKFLOW")
    print("="*30)
    print("Demonstrating: SQLite + SDK + Business Logic")
    
    success = create_working_workflow()
    
    if success:
        print(f"\n[SUCCESS] Your first workflow is working!")
        print(f"\nNEXT STEPS:")
        print(f"1. Modify the SQL queries in the nodes")
        print(f"2. Add more business logic")
        print(f"3. Connect to external APIs")
        print(f"4. Add more sophisticated analysis")
        print(f"5. Save results to files or databases")
        return 0
    else:
        print(f"\n[FAIL] Workflow needs attention")
        return 1

if __name__ == "__main__":
    sys.exit(main())