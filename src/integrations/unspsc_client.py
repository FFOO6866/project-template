"""UNSPSC (United Nations Standard Products and Services Code) Client.

This module provides integration with the UNSPSC classification system.
UNSPSC is a global classification system for products and services.

IMPORTANT: This uses REAL UNSPSC data sources only.
- Official UNSPSC code lists (purchased from unspsc.org)
- NO hardcoded codes
- NO mock data

Official UNSPSC Resources:
- Website: https://www.unspsc.org/
- Purchase: https://www.unspsc.org/purchase-unspsc
- Cost: Approximately $500 USD for commercial license
- Format: Excel/CSV files with full code hierarchy

UNSPSC Hierarchy:
- Segment (2 digits): 10000000 - Highest level
- Family (4 digits):  10100000 - Second level
- Class (6 digits):   10101500 - Third level
- Commodity (8 digits): 10101501 - Lowest level

Usage:
    # Import from official UNSPSC CSV:
    client = UNSPSCClient()
    codes = client.import_from_csv("UNSPSC_v24.csv")

    # Search for codes:
    results = client.search("safety equipment")
"""

import os
import csv
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)


@dataclass
class UNSPSCCode:
    """UNSPSC code data structure."""
    code: str
    segment: str
    family: str
    class_code: str
    commodity: str
    title: str
    definition: Optional[str] = None
    level: int = 0  # 1=Segment, 2=Family, 3=Class, 4=Commodity

    @property
    def segment_code(self) -> str:
        """Get 2-digit segment code."""
        return self.code[:2] + '000000'

    @property
    def family_code(self) -> str:
        """Get 4-digit family code."""
        return self.code[:4] + '0000'

    @property
    def class_full_code(self) -> str:
        """Get 6-digit class code."""
        return self.code[:6] + '00'

    @property
    def commodity_code(self) -> str:
        """Get full 8-digit commodity code."""
        return self.code


class UNSPSCClient:
    """Client for UNSPSC classification system.

    IMPORTANT: This client requires purchasing UNSPSC code lists.

    Purchase Information:
    - Cost: ~$500 USD for commercial license
    - Purchase URL: https://www.unspsc.org/purchase-unspsc
    - Format: Excel/CSV files
    - Updates: Annual updates available

    Environment Variables:
    - UNSPSC_DATA_PATH: Path to UNSPSC CSV file (optional)
    - UNSPSC_VERSION: UNSPSC version (e.g., "24.0")
    """

    def __init__(self, data_path: Optional[str] = None, version: Optional[str] = None):
        """Initialize UNSPSC client.

        Args:
            data_path: Path to UNSPSC CSV file (or use UNSPSC_DATA_PATH env var)
            version: UNSPSC version (or use UNSPSC_VERSION env var)
        """
        self.data_path = data_path or os.getenv('UNSPSC_DATA_PATH')
        self.version = version or os.getenv('UNSPSC_VERSION', '24.0')
        self._codes_cache: Optional[List[UNSPSCCode]] = None

    def import_from_csv(self, csv_path: str) -> List[UNSPSCCode]:
        """Import UNSPSC codes from official CSV file.

        IMPORTANT: CSV files must be purchased from https://www.unspsc.org/

        Expected CSV format (from official UNSPSC download):
        - Code,Segment,Family,Class,Commodity,Title,Definition
        - 10000000,Live Plant and Animal Material and Accessories and Supplies,,,,Live animals,...
        - 10100000,,Live animals,,,Live animals,...
        - 10101500,,,Livestock,,,Livestock animals...
        - 10101501,,,,Cattle,,Bovine animals...

        Args:
            csv_path: Path to UNSPSC CSV file (purchased from unspsc.org)

        Returns:
            List of UNSPSC codes

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV format is invalid
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(
                f"UNSPSC CSV file not found: {csv_path}\n"
                f"Please purchase from: https://www.unspsc.org/purchase-unspsc\n"
                f"Cost: Approximately $500 USD for commercial license"
            )

        codes = []
        with open(csv_path, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
            reader = csv.DictReader(f)

            # Validate required fields
            required_fields = {'Code', 'Title'}
            fieldnames = set(reader.fieldnames or [])

            if not required_fields.issubset(fieldnames):
                raise ValueError(
                    f"Invalid UNSPSC CSV format. Required fields: {required_fields}\n"
                    f"Found fields: {reader.fieldnames}\n"
                    f"Please ensure you're using the official UNSPSC CSV format."
                )

            for row in reader:
                code = row['Code'].strip()

                # Validate UNSPSC code format (8 digits)
                if not self.validate_code_format(code):
                    logger.warning(f"Invalid UNSPSC code format: {code}")
                    continue

                # Determine hierarchy level based on which fields are filled
                level = self._determine_level(row)

                unspsc_code = UNSPSCCode(
                    code=code,
                    segment=row.get('Segment', '').strip(),
                    family=row.get('Family', '').strip(),
                    class_code=row.get('Class', '').strip(),
                    commodity=row.get('Commodity', '').strip(),
                    title=row['Title'].strip(),
                    definition=row.get('Definition', '').strip() or None,
                    level=level
                )
                codes.append(unspsc_code)

        logger.info(f"Imported {len(codes)} UNSPSC codes from {csv_path}")
        self._codes_cache = codes
        return codes

    def validate_code_format(self, code: str) -> bool:
        """Validate UNSPSC code format.

        UNSPSC codes are 8 digits, with trailing zeros for higher levels:
        - Segment: XX000000
        - Family:  XXXX0000
        - Class:   XXXXXX00
        - Commodity: XXXXXXXX

        Args:
            code: UNSPSC code to validate

        Returns:
            True if valid format, False otherwise
        """
        if not code or len(code) != 8:
            return False

        try:
            int(code)
            return True
        except ValueError:
            return False

    def get_segment(self, code: str) -> Optional[UNSPSCCode]:
        """Get segment for a given UNSPSC code.

        Args:
            code: UNSPSC code (any level)

        Returns:
            Segment code object or None
        """
        if not self._codes_cache:
            return None

        segment_code = code[:2] + '000000'
        for unspsc_code in self._codes_cache:
            if unspsc_code.code == segment_code:
                return unspsc_code
        return None

    def get_family(self, code: str) -> Optional[UNSPSCCode]:
        """Get family for a given UNSPSC code.

        Args:
            code: UNSPSC code (any level)

        Returns:
            Family code object or None
        """
        if not self._codes_cache:
            return None

        family_code = code[:4] + '0000'
        for unspsc_code in self._codes_cache:
            if unspsc_code.code == family_code:
                return unspsc_code
        return None

    def search(self, query: str, level: Optional[int] = None) -> List[UNSPSCCode]:
        """Search UNSPSC codes by title or definition.

        Args:
            query: Search query
            level: Optional level filter (1-4)

        Returns:
            List of matching UNSPSC codes
        """
        if not self._codes_cache:
            return []

        query_lower = query.lower()
        results = []

        for code in self._codes_cache:
            # Check if level filter applies
            if level is not None and code.level != level:
                continue

            # Search in title and definition
            if query_lower in code.title.lower():
                results.append(code)
            elif code.definition and query_lower in code.definition.lower():
                results.append(code)

        return results

    def get_hierarchy(self, code: str) -> Dict[str, Optional[UNSPSCCode]]:
        """Get full hierarchy for a UNSPSC code.

        Args:
            code: UNSPSC code (any level)

        Returns:
            Dictionary with segment, family, class, commodity
        """
        return {
            'segment': self.get_segment(code),
            'family': self.get_family(code),
            'class': self._get_class(code),
            'commodity': self._get_commodity(code)
        }

    def _get_class(self, code: str) -> Optional[UNSPSCCode]:
        """Get class for a given UNSPSC code."""
        if not self._codes_cache:
            return None

        class_code = code[:6] + '00'
        for unspsc_code in self._codes_cache:
            if unspsc_code.code == class_code:
                return unspsc_code
        return None

    def _get_commodity(self, code: str) -> Optional[UNSPSCCode]:
        """Get commodity for a given UNSPSC code."""
        if not self._codes_cache or len(code) != 8:
            return None

        for unspsc_code in self._codes_cache:
            if unspsc_code.code == code:
                return unspsc_code
        return None

    def _determine_level(self, row: Dict[str, str]) -> int:
        """Determine hierarchy level from CSV row.

        Returns:
            1=Segment, 2=Family, 3=Class, 4=Commodity
        """
        if row.get('Commodity', '').strip():
            return 4
        elif row.get('Class', '').strip():
            return 3
        elif row.get('Family', '').strip():
            return 2
        else:
            return 1


def get_unspsc_client() -> UNSPSCClient:
    """Factory function to get configured UNSPSC client.

    Returns:
        Configured UNSPSC client instance
    """
    client = UNSPSCClient()

    if not client.data_path:
        logger.warning(
            "UNSPSC data path not configured. "
            "Please purchase UNSPSC codes from: https://www.unspsc.org/purchase-unspsc"
        )

    return client


# Example usage documentation
if __name__ == "__main__":
    print("""
UNSPSC Client Usage Examples
============================

IMPORTANT: UNSPSC code lists must be purchased.
Purchase from: https://www.unspsc.org/purchase-unspsc
Cost: Approximately $500 USD for commercial license

Method 1: Import from CSV (after purchase)
------------------------------------------
client = UNSPSCClient()
codes = client.import_from_csv("UNSPSC_v24.csv")

Method 2: Search codes
---------------------
client = UNSPSCClient()
client.import_from_csv("UNSPSC_v24.csv")
results = client.search("safety equipment")

Method 3: Database Loading
--------------------------
# Use scripts/load_classification_data.py to load into PostgreSQL
python scripts/load_classification_data.py --unspsc-csv UNSPSC_v24.csv

UNSPSC Hierarchy:
- Segment (2 digits): 10000000 - Live Plant and Animal Material
- Family (4 digits):  10100000 - Live animals
- Class (6 digits):   10101500 - Livestock
- Commodity (8 digits): 10101501 - Cattle

For more information:
- Purchase: https://www.unspsc.org/purchase-unspsc
- Documentation: https://www.unspsc.org/resources
- Support: support@unspsc.org
""")
