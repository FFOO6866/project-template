#!/usr/bin/env python3
"""Quick SDK import test for infrastructure gap analysis."""

print("=== Kailash SDK Import Analysis ===")

# Test basic SDK import
try:
    import kailash
    print("✓ Kailash SDK available")
    print(f"  Version: {getattr(kailash, '__version__', 'unknown')}")
except Exception as e:
    print(f"✗ Kailash SDK import failed: {e}")

# Test Node import (critical for compatibility)
try:
    from kailash.nodes.base import Node
    print("✓ Node import: SUCCESS")
except Exception as e:
    print(f"✗ Node import error: {e}")

# Test Node import (newer pattern)
try:
    from kailash.nodes.base import Node
    print("✓ Node import: SUCCESS")
except Exception as e:
    print(f"✗ Node import error: {e}")

# Test critical dependencies
dependencies = [
    ('neo4j', 'neo4j'),
    ('chromadb', 'chromadb'),
    ('pandas', 'pandas'),
    ('PyPDF2', 'PyPDF2'),
    ('python-docx', 'docx'),
    ('pillow', 'PIL'),
    ('openpyxl', 'openpyxl'),
    ('asyncpg', 'asyncpg'),
    ('redis', 'redis'),
    ('httpx', 'httpx')
]

print("\n=== Critical Dependencies Check ===")
missing_deps = []
for name, module in dependencies:
    try:
        __import__(module)
        print(f"✓ {name}")
    except ImportError:
        print(f"✗ {name} - MISSING")
        missing_deps.append(name)

# Test Docker availability
print("\n=== Docker Infrastructure Check ===")
import subprocess
try:
    result = subprocess.run(['docker', '--version'], capture_output=True, text=True, timeout=10)
    if result.returncode == 0:
        print("✓ Docker available")
        print(f"  {result.stdout.strip()}")
    else:
        print("✗ Docker not working")
except (subprocess.TimeoutExpired, FileNotFoundError):
    print("✗ Docker not found")

# Test WSL2 capability (Windows specific)
import platform
if platform.system() == "Windows":
    print("\n=== WSL2 Check ===")
    try:
        result = subprocess.run(['wsl', '--list', '--verbose'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ WSL2 available")
            print(f"  {result.stdout}")
        else:
            print("✗ WSL2 not working")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("✗ WSL2 not found")

print(f"\n=== Summary ===")
print(f"Missing dependencies: {len(missing_deps)}")
if missing_deps:
    print(f"Missing: {', '.join(missing_deps)}")