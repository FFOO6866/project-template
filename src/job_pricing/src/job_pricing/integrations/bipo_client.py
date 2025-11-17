"""
BIPO Cloud HRIS API Client

Integrates with BIPO Cloud API to fetch employee data.
API Documentation: https://ap9.bipocloud.com/IMC
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests
from requests.exceptions import RequestException

from job_pricing.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class BIPOAPIException(Exception):
    """Exception raised for BIPO API errors."""
    pass


class BIPOClient:
    """
    BIPO Cloud HRIS API Client

    Provides methods to authenticate and fetch employee data from BIPO Cloud.

    Attributes:
        base_url: Base URL for BIPO API
        username: BIPO username (usually 'AzureAD')
        password: BIPO password
        client_id: OAuth2 client ID
        client_secret: OAuth2 client secret
        access_token: Current access token (cached)

    Example:
        ```python
        client = BIPOClient()
        employees = client.get_employee_data()
        for emp in employees:
            print(f"{emp['EmployeeNumber']}: {emp['EmployeeName']}")
        ```
    """

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
    ):
        """
        Initialize BIPO Client with credentials.

        Args:
            username: BIPO username (defaults to settings.BIPO_USERNAME)
            password: BIPO password (defaults to settings.BIPO_PASSWORD)
            client_id: OAuth2 client ID (defaults to settings.BIPO_CLIENT_ID)
            client_secret: OAuth2 client secret (defaults to settings.BIPO_CLIENT_SECRET)
        """
        self.base_url = settings.BIPO_API_BASE_URL
        self.username = username or settings.BIPO_USERNAME
        self.password = password or settings.BIPO_PASSWORD
        self.client_id = client_id or settings.BIPO_CLIENT_ID
        self.client_secret = client_secret or settings.BIPO_CLIENT_SECRET
        self.access_token: Optional[str] = None

        if not all([self.username, self.password, self.client_id, self.client_secret]):
            raise ValueError(
                "Missing BIPO credentials. Set BIPO_USERNAME, BIPO_PASSWORD, "
                "BIPO_CLIENT_ID, BIPO_CLIENT_SECRET in environment variables."
            )

    def get_access_token(self) -> str:
        """
        Authenticate and get access token from BIPO API.

        Returns:
            Access token string

        Raises:
            BIPOAPIException: If authentication fails
        """
        url = f"{self.base_url}/oauth2/webapi/token"
        data = {
            "UserName": self.username,
            "Password": self.password,
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }

        try:
            logger.info("Authenticating with BIPO API...")
            response = requests.post(url, data=data, timeout=30)
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data["access_token"]

            logger.info("Successfully authenticated with BIPO API")
            return self.access_token

        except RequestException as e:
            logger.error(f"Failed to authenticate with BIPO API: {e}")
            raise BIPOAPIException(f"Authentication failed: {e}")
        except KeyError:
            logger.error("Invalid response format from BIPO token endpoint")
            raise BIPOAPIException("Invalid token response format")

    def _make_api_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make authenticated request to BIPO API.

        Args:
            endpoint: API endpoint URL
            data: Request payload

        Returns:
            API response as dictionary

        Raises:
            BIPOAPIException: If request fails
        """
        if not self.access_token:
            self.get_access_token()

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"bearer {self.access_token}",
        }

        response = None
        try:
            response = requests.post(endpoint, json=data, headers=headers, timeout=60)
            response.raise_for_status()
            return response.json()

        except RequestException as e:
            logger.error(f"BIPO API request failed: {e}")

            # Retry once with new token if authentication failed (only if we got a response)
            if response is not None and response.status_code == 401:
                logger.info("Token expired, refreshing...")
                self.get_access_token()

                headers["Authorization"] = f"bearer {self.access_token}"
                response = requests.post(endpoint, json=data, headers=headers, timeout=60)
                response.raise_for_status()
                return response.json()

            raise BIPOAPIException(f"API request failed: {e}")

    def get_employee_data(
        self,
        view_name: str = "BIPO-AZURE-EMP",
        date_from: str = "1900-01-01",
        date_to: Optional[str] = None,
        is_active: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Fetch employee data from BIPO API.

        Args:
            view_name: BIPO view name (default: "BIPO-AZURE-EMP")
            date_from: Start date for updateon filter (ISO format)
            date_to: End date for updateon filter (defaults to today)
            is_active: Filter for active employees only

        Returns:
            List of employee records as dictionaries

        Raises:
            BIPOAPIException: If request fails

        Example:
            ```python
            client = BIPOClient()
            employees = client.get_employee_data(is_active=True)
            print(f"Found {len(employees)} active employees")
            ```
        """
        if not date_to:
            date_to = datetime.now().strftime("%Y-%m-%d")

        data = {
            "ViewName": view_name,
            "updateonFrom": date_from,
            "updateonTo": date_to,
            "isActive": str(is_active).lower(),
        }

        url = f"{self.base_url}/api2/BIPOExport/GetView"

        logger.info(f"Fetching employee data from BIPO (view: {view_name}, active: {is_active})")

        try:
            response = self._make_api_request(url, data)

            # Extract employee records from response
            # BIPO API response format may vary - adjust based on actual response
            if isinstance(response, dict) and "data" in response:
                employees = response["data"]
            elif isinstance(response, list):
                employees = response
            else:
                employees = []

            logger.info(f"Successfully fetched {len(employees)} employees from BIPO")
            return employees

        except Exception as e:
            logger.error(f"Failed to fetch employee data: {e}")
            raise BIPOAPIException(f"Failed to fetch employee data: {e}")

    def get_company_list(self) -> List[Dict[str, Any]]:
        """
        Fetch company list from BIPO.

        Returns:
            List of company records
        """
        data = {"InterfaceCode": "BIPO-CO"}
        url = f"{self.base_url}/api2/BIPOExport/GetListItem"

        logger.info("Fetching company list from BIPO")
        response = self._make_api_request(url, data)

        companies = response.get("data", []) if isinstance(response, dict) else response
        logger.info(f"Fetched {len(companies)} companies")
        return companies

    def get_department_list(self) -> List[Dict[str, Any]]:
        """
        Fetch department list from BIPO.

        Returns:
            List of department records
        """
        data = {"InterfaceCode": "BIPO-DP"}
        url = f"{self.base_url}/api2/BIPOExport/GetListItem"

        logger.info("Fetching department list from BIPO")
        response = self._make_api_request(url, data)

        departments = response.get("data", []) if isinstance(response, dict) else response
        logger.info(f"Fetched {len(departments)} departments")
        return departments

    def get_designation_list(self) -> List[Dict[str, Any]]:
        """
        Fetch designation/job title list from BIPO.

        Returns:
            List of designation records
        """
        data = {"InterfaceCode": "BIPO-DS"}
        url = f"{self.base_url}/api2/BIPOExport/GetListItem"

        logger.info("Fetching designation list from BIPO")
        response = self._make_api_request(url, data)

        designations = response.get("data", []) if isinstance(response, dict) else response
        logger.info(f"Fetched {len(designations)} designations")
        return designations
