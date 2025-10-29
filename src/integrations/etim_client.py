"""ETIM (Electro-Technical Information Model) API Client.

This module provides integration with the ETIM classification system.
ETIM is an international standard for classifying electro-technical products.

IMPORTANT: This uses REAL ETIM data sources only.
- ETIM API (requires membership/authentication)
- Official ETIM CSV/XML exports
- NO hardcoded translations
- NO mock data

Official ETIM Resources:
- Website: https://www.etim-international.com/
- API Documentation: https://portal.etim-international.com/
- Membership: Required for API access and data downloads
- Data Format: XML/CSV exports available for members

Usage:
    # For ETIM members with API access:
    client = ETIMClient(api_key="your_api_key")
    classes = client.get_classes(version="9.0")

    # For CSV import (members only):
    client = ETIMClient()
    client.import_from_csv("path/to/etim_classes_9.0.csv")
"""

import os
import csv
import json
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import requests
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ETIMClass:
    """ETIM product class data structure."""
    class_code: str
    version: str
    description_en: str
    description_de: Optional[str] = None
    description_fr: Optional[str] = None
    description_nl: Optional[str] = None
    parent_class: Optional[str] = None
    features: Optional[Dict] = None
    valid_from: Optional[datetime] = None
    valid_to: Optional[datetime] = None


class ETIMClient:
    """Client for ETIM classification system.

    IMPORTANT: This client requires ETIM membership for data access.

    Authentication Methods:
    1. API Key (for API access)
    2. CSV/XML Import (for members with data export access)

    Environment Variables:
    - ETIM_API_KEY: API key for ETIM portal (optional)
    - ETIM_API_URL: ETIM API base URL (optional)
    - ETIM_MEMBER_ID: ETIM organization member ID (optional)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        member_id: Optional[str] = None
    ):
        """Initialize ETIM client.

        Args:
            api_key: ETIM API key (or use ETIM_API_KEY env var)
            api_url: ETIM API base URL (or use ETIM_API_URL env var)
            member_id: ETIM member organization ID (or use ETIM_MEMBER_ID env var)
        """
        self.api_key = api_key or os.getenv('ETIM_API_KEY')
        self.api_url = api_url or os.getenv('ETIM_API_URL', 'https://portal.etim-international.com/api/v1')
        self.member_id = member_id or os.getenv('ETIM_MEMBER_ID')

        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            })

    def check_authentication(self) -> bool:
        """Check if ETIM authentication is configured.

        Returns:
            True if API key is configured, False otherwise.
        """
        return bool(self.api_key)

    def get_classes(self, version: str = "9.0", language: str = "en") -> List[ETIMClass]:
        """Retrieve ETIM classes from API.

        IMPORTANT: Requires ETIM API access (membership).

        Args:
            version: ETIM version (e.g., "9.0", "8.0")
            language: Language code (en, de, fr, nl, etc.)

        Returns:
            List of ETIM classes

        Raises:
            ValueError: If API key not configured
            requests.HTTPError: If API request fails
        """
        if not self.api_key:
            raise ValueError(
                "ETIM API key not configured. "
                "Please set ETIM_API_KEY environment variable or provide api_key parameter. "
                "ETIM membership required: https://www.etim-international.com/"
            )

        try:
            response = self.session.get(
                f"{self.api_url}/classes",
                params={
                    'version': version,
                    'language': language
                }
            )
            response.raise_for_status()

            data = response.json()
            return [self._parse_etim_class(cls_data) for cls_data in data.get('classes', [])]

        except requests.RequestException as e:
            logger.error(f"ETIM API request failed: {e}")
            raise

    def import_from_csv(self, csv_path: str, version: str = "9.0") -> List[ETIMClass]:
        """Import ETIM classes from CSV file.

        IMPORTANT: CSV files are only available to ETIM members.
        Download from: https://portal.etim-international.com/

        Expected CSV format:
        - ClassCode,ParentClass,DescriptionEN,DescriptionDE,DescriptionFR,DescriptionNL
        - EC000001,,Building automation,Gebäudeautomation,Automatisation du bâtiment,Gebouwautomatisering

        Args:
            csv_path: Path to ETIM CSV file (member export)
            version: ETIM version for this data

        Returns:
            List of ETIM classes

        Raises:
            FileNotFoundError: If CSV file doesn't exist
            ValueError: If CSV format is invalid
        """
        if not os.path.exists(csv_path):
            raise FileNotFoundError(
                f"ETIM CSV file not found: {csv_path}\n"
                f"Please download from ETIM member portal: https://portal.etim-international.com/\n"
                f"ETIM membership required."
            )

        classes = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            required_fields = {'ClassCode', 'DescriptionEN'}
            if not required_fields.issubset(reader.fieldnames or []):
                raise ValueError(
                    f"Invalid ETIM CSV format. Required fields: {required_fields}\n"
                    f"Found fields: {reader.fieldnames}"
                )

            for row in reader:
                etim_class = ETIMClass(
                    class_code=row['ClassCode'],
                    version=version,
                    description_en=row['DescriptionEN'],
                    description_de=row.get('DescriptionDE'),
                    description_fr=row.get('DescriptionFR'),
                    description_nl=row.get('DescriptionNL'),
                    parent_class=row.get('ParentClass') or None
                )
                classes.append(etim_class)

        logger.info(f"Imported {len(classes)} ETIM classes from {csv_path}")
        return classes

    def import_from_xml(self, xml_path: str) -> List[ETIMClass]:
        """Import ETIM classes from XML file.

        IMPORTANT: XML files are only available to ETIM members.
        Download from: https://portal.etim-international.com/

        Args:
            xml_path: Path to ETIM XML file (member export)

        Returns:
            List of ETIM classes

        Raises:
            FileNotFoundError: If XML file doesn't exist
            NotImplementedError: XML parsing not yet implemented
        """
        if not os.path.exists(xml_path):
            raise FileNotFoundError(
                f"ETIM XML file not found: {xml_path}\n"
                f"Please download from ETIM member portal: https://portal.etim-international.com/\n"
                f"ETIM membership required."
            )

        raise NotImplementedError(
            "XML import not yet implemented. Please use CSV import or API access."
        )

    def search_class(self, query: str, language: str = "en") -> List[ETIMClass]:
        """Search ETIM classes by description.

        IMPORTANT: Requires ETIM API access (membership).

        Args:
            query: Search query
            language: Language code for search

        Returns:
            List of matching ETIM classes

        Raises:
            ValueError: If API key not configured
        """
        if not self.api_key:
            raise ValueError(
                "ETIM API key not configured. "
                "ETIM membership required: https://www.etim-international.com/"
            )

        try:
            response = self.session.get(
                f"{self.api_url}/classes/search",
                params={
                    'query': query,
                    'language': language
                }
            )
            response.raise_for_status()

            data = response.json()
            return [self._parse_etim_class(cls_data) for cls_data in data.get('results', [])]

        except requests.RequestException as e:
            logger.error(f"ETIM search failed: {e}")
            raise

    def _parse_etim_class(self, data: Dict) -> ETIMClass:
        """Parse ETIM class from API response."""
        return ETIMClass(
            class_code=data['class_code'],
            version=data.get('version', '9.0'),
            description_en=data['description']['en'],
            description_de=data.get('description', {}).get('de'),
            description_fr=data.get('description', {}).get('fr'),
            description_nl=data.get('description', {}).get('nl'),
            parent_class=data.get('parent_class'),
            features=data.get('features')
        )

    def validate_class_code(self, class_code: str) -> bool:
        """Validate ETIM class code format.

        ETIM class codes follow pattern: EC######
        where # is a digit (e.g., EC000001)

        Args:
            class_code: ETIM class code to validate

        Returns:
            True if valid format, False otherwise
        """
        if not class_code or len(class_code) != 8:
            return False

        if not class_code.startswith('EC'):
            return False

        try:
            int(class_code[2:])
            return True
        except ValueError:
            return False


def get_etim_client() -> ETIMClient:
    """Factory function to get configured ETIM client.

    Returns:
        Configured ETIM client instance

    Raises:
        ValueError: If ETIM is not properly configured
    """
    client = ETIMClient()

    if not client.check_authentication():
        logger.warning(
            "ETIM API not configured. "
            "CSV import is available for ETIM members. "
            "Visit: https://www.etim-international.com/"
        )

    return client


# Example usage documentation
if __name__ == "__main__":
    print("""
ETIM Client Usage Examples
==========================

IMPORTANT: ETIM membership required for all data access methods.
Visit: https://www.etim-international.com/

Method 1: API Access (requires API key)
---------------------------------------
export ETIM_API_KEY="your_api_key_here"
export ETIM_MEMBER_ID="your_org_id"

client = ETIMClient()
classes = client.get_classes(version="9.0")

Method 2: CSV Import (requires member download)
----------------------------------------------
# Download CSV from: https://portal.etim-international.com/
client = ETIMClient()
classes = client.import_from_csv("etim_classes_9.0.csv")

Method 3: Database Loading
--------------------------
# Use scripts/load_classification_data.py to load into PostgreSQL
python scripts/load_classification_data.py --etim-csv etim_classes_9.0.csv

For more information:
- ETIM membership: https://www.etim-international.com/become-a-member/
- API documentation: https://portal.etim-international.com/api-docs
- Data downloads: https://portal.etim-international.com/downloads
""")
