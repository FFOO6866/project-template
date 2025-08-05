"""
Python Command Alias Setup for Windows
======================================

This script provides a solution for the 'python' command not being available
on Windows, where only 'py' works. This creates a consistent development environment.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def check_python_commands():
    """Check which Python commands are available"""
    results = {}
    
    for cmd in ['python', 'py', 'python3']:
        try:
            result = subprocess.run([cmd, '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                results[cmd] = result.stdout.strip()
                print(f"OK {cmd}: {results[cmd]}")
            else:
                results[cmd] = None
                print(f"FAIL {cmd}: Command failed")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            results[cmd] = None
            print(f"FAIL {cmd}: Not found")
    
    return results


def create_python_alias_batch():
    """Create a batch file alias for python command"""
    project_root = Path(__file__).parent
    alias_file = project_root / "python.bat"
    
    batch_content = '''@echo off
REM Python command alias - redirects to py command
py %*
'''
    
    with open(alias_file, 'w') as f:
        f.write(batch_content)
    
    print(f"Created python.bat alias at: {alias_file}")
    print("To use: Add this directory to your PATH or run scripts from this directory")
    return alias_file


def create_activation_script():
    """Create a script to set up the development environment"""
    project_root = Path(__file__).parent
    setup_file = project_root / "setup_dev_env.bat"
    
    batch_content = f'''@echo off
REM Development Environment Setup for Kailash SDK
echo Setting up Kailash SDK development environment...

REM Add current directory to PATH for python alias
set PATH={project_root};%PATH%

REM Apply Windows compatibility patch
echo Applying Windows compatibility patch...
py -c "import sys; sys.path.insert(0, r'{project_root}'); from windows_patch import mock_resource; print('Windows patch applied')"

REM Verify installations
echo.
echo Verifying installations:
python --version
echo Kailash SDK: 
py -c "from kailash.workflow.builder import WorkflowBuilder; print('OK Core SDK available')"
echo DataFlow:
py -c "from dataflow import DataFlow; print('OK DataFlow available')"

echo.
echo Development environment ready!
echo Use 'python' or 'py' commands interchangeably.
'''
    
    with open(setup_file, 'w') as f:
        f.write(batch_content)
    
    print(f"Created setup script at: {setup_file}")
    return setup_file


def main():
    """Main setup function"""
    print("Python Command Alias Setup")
    print("=" * 30)
    
    # Check current state
    print("\n1. Checking available Python commands:")
    results = check_python_commands()
    
    # Create solutions
    print("\n2. Creating solutions:")
    
    if not results.get('python'):
        print("Python command not available - creating alias...")
        alias_file = create_python_alias_batch()
        
        # Test the alias
        try:
            test_result = subprocess.run([str(alias_file.parent / "python.bat"), '--version'], 
                                       capture_output=True, text=True, timeout=5)
            if test_result.returncode == 0:
                print(f"OK Alias works: {test_result.stdout.strip()}")
            else:
                print("FAIL Alias test failed")
        except Exception as e:
            print(f"FAIL Alias test error: {e}")
    else:
        print("Python command already available")
    
    # Create setup script
    setup_file = create_activation_script()
    
    print("\n3. Next Steps:")
    print(f"   - Run {setup_file} to set up your development environment")
    print("   - Or add this directory to your system PATH for permanent access")
    print("   - Use 'python' or 'py' commands interchangeably")
    
    return True


if __name__ == "__main__":
    main()