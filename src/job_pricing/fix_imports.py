"""
Automated Import Path Fixer

Converts all imports from 'src.job_pricing' to 'job_pricing' pattern.
This fixes the import inconsistency blocking tests and scrapers.
"""

import os
import re
from pathlib import Path

def fix_imports_in_file(file_path: Path) -> tuple[bool, int]:
    """
    Fix imports in a single file.

    Returns:
        (changed, num_fixes) - Whether file was modified and how many fixes made
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Replace 'from src.job_pricing' with 'from job_pricing'
        content = re.sub(
            r'from src\.job_pricing',
            'from job_pricing',
            content
        )

        # Replace 'import src.job_pricing' with 'import job_pricing'
        content = re.sub(
            r'import src\.job_pricing',
            'import job_pricing',
            content
        )

        if content != original_content:
            # Count how many replacements were made
            num_fixes = original_content.count('from src.job_pricing')
            num_fixes += original_content.count('import src.job_pricing')

            # Write back
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return True, num_fixes

        return False, 0

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False, 0


def fix_all_imports(root_dir: Path) -> dict:
    """
    Fix imports in all Python files under root_dir.

    Returns:
        Statistics dict
    """
    stats = {
        'files_scanned': 0,
        'files_modified': 0,
        'total_fixes': 0,
        'modified_files': []
    }

    # Find all Python files
    for py_file in root_dir.rglob('*.py'):
        # Skip __pycache__ and other cache directories
        if '__pycache__' in str(py_file) or '.pytest_cache' in str(py_file):
            continue

        stats['files_scanned'] += 1

        changed, num_fixes = fix_imports_in_file(py_file)

        if changed:
            stats['files_modified'] += 1
            stats['total_fixes'] += num_fixes
            stats['modified_files'].append(str(py_file.relative_to(root_dir)))

    return stats


def main():
    """Run the import fixer."""
    print("=" * 80)
    print("IMPORT PATH FIXER")
    print("Fixing: 'from src.job_pricing' -> 'from job_pricing'")
    print("=" * 80)
    print()

    # Get the src/job_pricing directory
    script_dir = Path(__file__).parent
    src_dir = script_dir / 'src' / 'job_pricing'

    if not src_dir.exists():
        # Try alternate path
        src_dir = script_dir / 'job_pricing'

    if not src_dir.exists():
        print(f"ERROR: Could not find source directory")
        print(f"Looked in: {script_dir / 'src' / 'job_pricing'}")
        print(f"       and: {script_dir / 'job_pricing'}")
        return

    print(f"Processing directory: {src_dir}")
    print()

    # Run the fixer
    stats = fix_all_imports(src_dir)

    # Print results
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Files scanned:  {stats['files_scanned']}")
    print(f"Files modified: {stats['files_modified']}")
    print(f"Total fixes:    {stats['total_fixes']}")
    print()

    if stats['modified_files']:
        print("Modified files:")
        for file_path in sorted(stats['modified_files'])[:20]:  # Show first 20
            print(f"  - {file_path}")

        if len(stats['modified_files']) > 20:
            print(f"  ... and {len(stats['modified_files']) - 20} more")

    print()
    print("=" * 80)
    if stats['files_modified'] > 0:
        print("[SUCCESS] IMPORT PATHS FIXED!")
        print("Scrapers and tests should now work correctly.")
    else:
        print("[INFO] No files needed modification.")
    print("=" * 80)


if __name__ == '__main__':
    main()
