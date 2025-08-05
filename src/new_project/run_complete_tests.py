#\!/usr/bin/env python3
import sys
import subprocess
import time
from pathlib import Path

# Apply Windows compatibility patch
import platform
if platform.system() == 'Windows':
    import windows_patch

def main():
    project_root = Path(__file__).parent
    
    print('Complete Test Suite for DATA-001: UNSPSC/ETIM Integration')
    print('SDK Compliance Fixes Validation')
    
    test_suites = [
        ('simple_test_runner.py', 'SDK Compliance Tests'),
        ('test_classification_functionality.py', 'Classification Functionality Tests')
    ]
    
    total_suites = 0
    passed_suites = 0
    
    for test_file, description in test_suites:
        print(f'\n{"="*60}')
        print(f'Running {description}')
        print('='*60)
        
        total_suites += 1
        try:
            result = subprocess.run([sys.executable, test_file], 
                                  capture_output=True, text=True, 
                                  cwd=project_root)
            
            print(result.stdout)
            if result.stderr:
                print('STDERR:', result.stderr)
            
            if result.returncode == 0:
                passed_suites += 1
                print(f'{description} PASSED')
            else:
                print(f'{description} FAILED')
                
        except Exception as e:
            print(f'Error running {description}: {e}')
    
    print(f'\n{"="*60}')
    print('COMPLETE TEST SUITE SUMMARY')
    print('='*60)
    print(f'Test suites run: {total_suites}')
    print(f'Suites passed: {passed_suites}')
    print(f'Success rate: {(passed_suites/total_suites*100):.1f}%')
    
    if passed_suites == total_suites:
        print('ALL TEST SUITES PASSED\!')
        print('SDK compliance violations FIXED')
        print('Ready for production use')
        return 0
    else:
        print(f'{total_suites - passed_suites} TEST SUITE(S) FAILED')
        return 1

if __name__ == '__main__':
    sys.exit(main())

