"""Check for missing dependencies in test infrastructure."""

import sys

def check_dependencies():
    """Check for missing test dependencies."""
    required_packages = [
        'neo4j',
        'chromadb', 
        'openai',
        'psycopg2',
        'redis'
    ]
    
    missing = []
    installed = []
    
    for package in required_packages:
        try:
            __import__(package)
            installed.append(package)
        except ImportError:
            missing.append(package)
    
    print(f"Missing dependencies: {missing}")
    print(f"Installed dependencies: {installed}")
    
    return missing, installed

if __name__ == "__main__":
    check_dependencies()