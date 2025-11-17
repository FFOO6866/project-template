"""
Automated Backup Verification System

Verifies database backups by:
1. Checking if backup files exist
2. Validating backup file integrity
3. Testing backup restoration (optional)
4. Logging verification results
"""

import logging
import os
import gzip
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import subprocess

from sqlalchemy import create_engine, text

from job_pricing.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BackupVerificationError(Exception):
    """Raised when backup verification fails"""
    pass


class BackupVerifier:
    """
    Verifies database backups.

    Features:
    - File existence checks
    - Integrity validation
    - Age verification
    - Size validation
    - Optional restoration testing
    """

    def __init__(
        self,
        backup_dir: str = "/app/backups",
        max_age_days: int = 7,
        min_size_mb: float = 0.1
    ):
        """
        Initialize backup verifier.

        Args:
            backup_dir: Directory containing backups
            max_age_days: Maximum age for backups (days)
            min_size_mb: Minimum backup file size (MB)
        """
        self.backup_dir = Path(backup_dir)
        self.max_age_days = max_age_days
        self.min_size_bytes = int(min_size_mb * 1024 * 1024)

    def verify_all_backups(self) -> Dict[str, any]:
        """
        Verify all backups in backup directory.

        Returns:
            Dict with verification results
        """
        logger.info(f"Starting backup verification in {self.backup_dir}")

        results = {
            "success": False,
            "timestamp": datetime.utcnow().isoformat(),
            "backup_dir": str(self.backup_dir),
            "backups_found": 0,
            "backups_valid": 0,
            "backups_invalid": 0,
            "latest_backup": None,
            "errors": [],
            "warnings": []
        }

        try:
            # Check if backup directory exists
            if not self.backup_dir.exists():
                results["errors"].append(f"Backup directory does not exist: {self.backup_dir}")
                return results

            # Find all backup files
            backup_files = self._find_backup_files()
            results["backups_found"] = len(backup_files)

            if not backup_files:
                results["warnings"].append("No backup files found")
                return results

            # Verify each backup
            valid_backups = []
            for backup_file in backup_files:
                try:
                    if self._verify_backup_file(backup_file):
                        valid_backups.append(backup_file)
                        results["backups_valid"] += 1
                    else:
                        results["backups_invalid"] += 1
                except Exception as e:
                    logger.error(f"Error verifying {backup_file}: {e}")
                    results["errors"].append(f"{backup_file.name}: {str(e)}")
                    results["backups_invalid"] += 1

            # Find latest valid backup
            if valid_backups:
                latest = max(valid_backups, key=lambda f: f.stat().st_mtime)
                results["latest_backup"] = {
                    "filename": latest.name,
                    "size_mb": latest.stat().st_size / (1024 * 1024),
                    "created": datetime.fromtimestamp(latest.stat().st_mtime).isoformat(),
                    "age_hours": (datetime.now() - datetime.fromtimestamp(latest.stat().st_mtime)).total_seconds() / 3600
                }

            # Check if we have recent backups
            if results["latest_backup"]:
                age_hours = results["latest_backup"]["age_hours"]
                if age_hours > (self.max_age_days * 24):
                    results["warnings"].append(
                        f"Latest backup is {age_hours:.1f} hours old (max: {self.max_age_days * 24})"
                    )

            # Mark as successful if we have at least one valid backup
            results["success"] = results["backups_valid"] > 0

            logger.info(
                f"Backup verification complete: {results['backups_valid']}/{results['backups_found']} valid"
            )

        except Exception as e:
            logger.error(f"Backup verification failed: {e}", exc_info=True)
            results["errors"].append(str(e))

        return results

    def _find_backup_files(self) -> List[Path]:
        """
        Find all backup files in backup directory.

        Returns:
            List of backup file paths
        """
        patterns = ["*.sql", "*.sql.gz", "*.dump", "*.backup"]
        backup_files = []

        for pattern in patterns:
            backup_files.extend(self.backup_dir.glob(pattern))

        return sorted(backup_files, key=lambda f: f.stat().st_mtime, reverse=True)

    def _verify_backup_file(self, backup_file: Path) -> bool:
        """
        Verify a single backup file.

        Args:
            backup_file: Path to backup file

        Returns:
            True if backup is valid

        Raises:
            BackupVerificationError: If backup is invalid
        """
        logger.debug(f"Verifying backup: {backup_file.name}")

        # Check file exists
        if not backup_file.exists():
            raise BackupVerificationError(f"Backup file does not exist: {backup_file}")

        # Check file size
        file_size = backup_file.stat().st_size
        if file_size < self.min_size_bytes:
            raise BackupVerificationError(
                f"Backup file too small: {file_size} bytes (min: {self.min_size_bytes})"
            )

        # Check file age
        file_age = datetime.now() - datetime.fromtimestamp(backup_file.stat().st_mtime)
        if file_age > timedelta(days=self.max_age_days):
            logger.warning(f"Backup file is old: {file_age.days} days")

        # Verify gzip integrity if compressed
        if backup_file.suffix == ".gz":
            try:
                with gzip.open(backup_file, 'rb') as f:
                    # Read first few bytes to verify it's valid gzip
                    f.read(100)
            except gzip.BadGzipFile:
                raise BackupVerificationError("Invalid gzip file")

        # Verify SQL syntax (basic check)
        if backup_file.suffix in [".sql", ".gz"]:
            content = self._read_backup_content(backup_file, max_bytes=1000)
            if not any(keyword in content.upper() for keyword in ["CREATE", "INSERT", "COPY", "ALTER"]):
                raise BackupVerificationError("Backup file does not appear to contain SQL statements")

        logger.debug(f"Backup verified successfully: {backup_file.name}")
        return True

    def _read_backup_content(self, backup_file: Path, max_bytes: int = 1000) -> str:
        """
        Read first few bytes of backup file.

        Args:
            backup_file: Path to backup file
            max_bytes: Maximum bytes to read

        Returns:
            Content string
        """
        if backup_file.suffix == ".gz":
            with gzip.open(backup_file, 'rt') as f:
                return f.read(max_bytes)
        else:
            with open(backup_file, 'r') as f:
                return f.read(max_bytes)

    def test_backup_restoration(self, backup_file: Path, test_db_url: str) -> bool:
        """
        Test backup restoration to a test database.

        Args:
            backup_file: Path to backup file
            test_db_url: Test database URL

        Returns:
            True if restoration successful
        """
        logger.info(f"Testing restoration of {backup_file.name}")

        try:
            # Create test database if needed
            engine = create_engine(test_db_url)

            # Read backup content
            if backup_file.suffix == ".gz":
                with gzip.open(backup_file, 'rt') as f:
                    sql_content = f.read()
            else:
                with open(backup_file, 'r') as f:
                    sql_content = f.read()

            # Execute backup SQL
            with engine.connect() as conn:
                conn.execute(text(sql_content))
                conn.commit()

            # Verify tables exist
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT COUNT(*)
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                """))
                table_count = result.fetchone()[0]

                if table_count == 0:
                    raise BackupVerificationError("No tables found after restoration")

            logger.info(f"Backup restoration successful: {table_count} tables restored")
            return True

        except Exception as e:
            logger.error(f"Backup restoration failed: {e}")
            raise BackupVerificationError(f"Restoration failed: {str(e)}")

        finally:
            if 'engine' in locals():
                engine.dispose()


def run_backup_verification() -> Dict[str, any]:
    """
    Run backup verification and return results.

    This function can be called as a Celery task or standalone script.

    Returns:
        Verification results
    """
    verifier = BackupVerifier(
        backup_dir=os.getenv("BACKUP_DIR", "/app/backups"),
        max_age_days=settings.BACKUP_RETENTION_DAYS,
        min_size_mb=0.1
    )

    results = verifier.verify_all_backups()

    # Log results
    if results["success"]:
        logger.info(f"✅ Backup verification passed: {results['backups_valid']} valid backups")
    else:
        logger.error(f"❌ Backup verification failed: {results}")

    return results


if __name__ == "__main__":
    # Run verification from command line
    import sys
    import json

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    results = run_backup_verification()
    print(json.dumps(results, indent=2))

    # Exit with error code if verification failed
    sys.exit(0 if results["success"] else 1)
