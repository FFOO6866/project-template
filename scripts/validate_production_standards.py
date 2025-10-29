#!/usr/bin/env python3
"""
Production Standards Validation Script
Enforces ZERO tolerance for mocks, hardcoding, and fallback data

Usage:
    uv run python scripts/validate_production_standards.py

Exit codes:
    0 - All checks passed
    1 - Violations found
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass

@dataclass
class Violation:
    """Represents a code violation"""
    file_path: str
    line_number: int
    line_content: str
    violation_type: str
    severity: str  # CRITICAL, HIGH, MEDIUM

class ProductionStandardsValidator:
    """Validates production code quality standards"""

    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.violations: List[Violation] = []

        # Define violation patterns
        self.critical_patterns = {
            'mock_data': [
                r"return\s+\[\s*\{.*['\"](mock|fake|dummy|sample|test)_",
                r"MOCK_DATA\s*=",
                r"FAKE_.*=.*\{",
                r"# Mock implementation",
                r"# Dummy data",
            ],
            'hardcoded_credentials': [
                r"password\s*=\s*['\"](?!.*\$\{).*['\"]",  # Not env var
                r"api_key\s*=\s*['\"]sk-.*['\"]",
                r"secret\s*=\s*['\"](?!.*\$\{).*['\"]",
                r"token\s*=\s*['\"](?!.*\$\{).*['\"]",
            ],
            'hardcoded_urls': [
                r"redis://localhost",
                r"bolt://localhost",
                r"http://localhost(?!:\$\{)",  # Allow ${PORT}
                r"postgresql://.*:.*@localhost",
            ],
            'hardcoded_config': [
                r"admin@example\.com",
                r"password\s*==\s*['\"]admin['\"]",
            ],
        }

        self.high_severity_patterns = {
            'fallback_data': [
                r"except.*:.*return\s+\{",
                r"except.*:.*return\s+\[",
                r"if.*is None:.*return\s+(FALLBACK|DEFAULT)",
                r"or\s+\{\}$",  # data or {}
                r"or\s+\[\]$",  # data or []
            ],
            'mock_responses': [
                r"'status':\s*'ok'.*# Without",
                r"return.*# Mock",
                r"# Simulated response",
            ],
        }

    def scan_file(self, file_path: Path) -> None:
        """Scan a single Python file for violations"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, start=1):
                # Check critical patterns
                for violation_type, patterns in self.critical_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            self.violations.append(Violation(
                                file_path=str(file_path),
                                line_number=line_num,
                                line_content=line.strip(),
                                violation_type=violation_type,
                                severity='CRITICAL'
                            ))

                # Check high severity patterns
                for violation_type, patterns in self.high_severity_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            self.violations.append(Violation(
                                file_path=str(file_path),
                                line_number=line_num,
                                line_content=line.strip(),
                                violation_type=violation_type,
                                severity='HIGH'
                            ))

        except Exception as e:
            print(f"⚠️  Error scanning {file_path}: {e}")

    def scan_directory(self, directory: Path, exclude_dirs: List[str] = None) -> None:
        """Recursively scan directory for Python files"""
        if exclude_dirs is None:
            exclude_dirs = ['venv', '.venv', 'node_modules', '__pycache__', '.git', 'tests']

        for item in directory.rglob('*.py'):
            # Skip excluded directories
            if any(excluded in item.parts for excluded in exclude_dirs):
                continue

            # Only check production files strictly
            if 'production' in item.name or 'src' in item.parts:
                self.scan_file(item)

    def check_duplicate_files(self) -> List[Tuple[str, str]]:
        """Check for duplicate functionality (similar filenames)"""
        duplicates = []
        files = {}

        for py_file in self.root_dir.rglob('src/**/*.py'):
            base_name = py_file.stem
            if base_name in files:
                duplicates.append((str(files[base_name]), str(py_file)))
            else:
                files[base_name] = py_file

        return duplicates

    def validate_directory_structure(self) -> List[str]:
        """Validate proper directory structure"""
        required_dirs = [
            'src/core',
            'src/repositories',
            'src/services',
            'src/api',
            'src/models',
            'tests/unit',
            'tests/integration',
        ]

        missing_dirs = []
        for req_dir in required_dirs:
            if not (self.root_dir / req_dir).exists():
                missing_dirs.append(req_dir)

        return missing_dirs

    def generate_report(self) -> int:
        """Generate validation report and return exit code"""
        print("=" * 80)
        print("🔍 HORME POV PRODUCTION STANDARDS VALIDATION")
        print("=" * 80)
        print()

        # Group violations by severity
        critical_violations = [v for v in self.violations if v.severity == 'CRITICAL']
        high_violations = [v for v in self.violations if v.severity == 'HIGH']

        # Report critical violations
        if critical_violations:
            print("❌ CRITICAL VIOLATIONS (MUST FIX IMMEDIATELY):")
            print("-" * 80)
            for v in critical_violations:
                print(f"  File: {v.file_path}:{v.line_number}")
                print(f"  Type: {v.violation_type}")
                print(f"  Code: {v.line_content[:100]}")
                print()

        # Report high severity violations
        if high_violations:
            print("⚠️  HIGH SEVERITY VIOLATIONS:")
            print("-" * 80)
            for v in high_violations:
                print(f"  File: {v.file_path}:{v.line_number}")
                print(f"  Type: {v.violation_type}")
                print(f"  Code: {v.line_content[:100]}")
                print()

        # Check for duplicates
        duplicates = self.check_duplicate_files()
        if duplicates:
            print("⚠️  DUPLICATE FILES DETECTED:")
            print("-" * 80)
            for file1, file2 in duplicates:
                print(f"  {file1}")
                print(f"  {file2}")
                print()

        # Check directory structure
        missing_dirs = self.validate_directory_structure()
        if missing_dirs:
            print("⚠️  MISSING REQUIRED DIRECTORIES:")
            print("-" * 80)
            for missing_dir in missing_dirs:
                print(f"  {missing_dir}")
            print()

        # Summary
        print("=" * 80)
        print("📊 VALIDATION SUMMARY")
        print("=" * 80)
        print(f"  Critical Violations: {len(critical_violations)}")
        print(f"  High Severity Violations: {len(high_violations)}")
        print(f"  Duplicate Files: {len(duplicates)}")
        print(f"  Missing Directories: {len(missing_dirs)}")
        print()

        # Determine exit code
        if critical_violations:
            print("❌ VALIDATION FAILED - Critical violations must be fixed")
            return 1
        elif high_violations or duplicates:
            print("⚠️  VALIDATION WARNING - High severity issues detected")
            return 1
        else:
            print("✅ VALIDATION PASSED - All production standards met")
            return 0

def main():
    """Main validation entry point"""
    validator = ProductionStandardsValidator()

    print("Scanning production code for standards violations...")
    validator.scan_directory(validator.root_dir / 'src')

    exit_code = validator.generate_report()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
