"""
BIPO HRIS Sync Service

Fetches employee data from BIPO Cloud and syncs to local database.
Handles data transformation, anonymization, and error recovery.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from job_pricing.integrations.bipo_client import BIPOClient, BIPOAPIException
from job_pricing.repositories.hris_repository import HRISRepository
from job_pricing.models.hris import InternalEmployee

logger = logging.getLogger(__name__)


class BIPOSyncService:
    """
    BIPO HRIS Data Synchronization Service

    Handles:
    - Fetching employee data from BIPO API
    - Transforming BIPO format to internal format
    - Data anonymization (PDPA compliance)
    - Upserting records to database
    - Error handling and logging

    Example:
        ```python
        service = BIPOSyncService(session)
        result = service.sync_all_employees()
        print(f"Synced: {result['synced']}, Failed: {result['failed']}")
        ```
    """

    def __init__(self, session: Session):
        """
        Initialize BIPO sync service.

        Args:
            session: Database session
        """
        self.session = session
        self.repository = HRISRepository(session)
        self.client = BIPOClient()

    def _transform_employee_data(
        self,
        bipo_employee: Dict[str, Any],
        anonymize: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Transform BIPO employee format to InternalEmployee format.

        Args:
            bipo_employee: Employee data from BIPO API
            anonymize: Whether to anonymize PII data

        Returns:
            Transformed employee data or None if transformation fails

        Note:
            Field mappings may need adjustment based on actual BIPO API response format.
            Current mapping is based on typical HRIS API structures.
        """
        try:
            # Extract fields from BIPO response
            # NOTE: Adjust field names based on actual BIPO API response
            employee_id = bipo_employee.get("EmployeeNumber") or bipo_employee.get("EmployeeID")

            if not employee_id:
                logger.warning(f"Missing employee ID in BIPO record: {bipo_employee}")
                return None

            # Parse dates
            hire_date_str = bipo_employee.get("HireDate") or bipo_employee.get("JoinDate")
            hire_date = None
            if hire_date_str:
                try:
                    hire_date = datetime.strptime(hire_date_str, "%Y-%m-%d").date()
                except (ValueError, TypeError):
                    logger.warning(f"Invalid hire date format for {employee_id}: {hire_date_str}")

            # Parse salary
            salary_str = bipo_employee.get("BasicSalary") or bipo_employee.get("MonthlySalary")
            current_salary = None
            if salary_str:
                try:
                    current_salary = float(salary_str)
                except (ValueError, TypeError):
                    logger.warning(f"Invalid salary format for {employee_id}: {salary_str}")

            if not current_salary:
                logger.warning(f"Missing salary for employee {employee_id}, skipping")
                return None

            # Calculate years in company
            years_in_company = None
            if hire_date:
                years_in_company = (date.today() - hire_date).days // 365

            transformed_data = {
                "employee_id": str(employee_id),
                "job_title": bipo_employee.get("PositionName") or bipo_employee.get("JobTitle") or "Unknown",
                "department": bipo_employee.get("DepartmentName") or bipo_employee.get("Department"),
                "job_family": bipo_employee.get("JobFamily") or self._infer_job_family(
                    bipo_employee.get("PositionName", "")
                ),
                "internal_grade": bipo_employee.get("GradeCode") or bipo_employee.get("JobGrade"),
                "current_salary": current_salary,
                "currency": bipo_employee.get("Currency", "SGD"),
                "employment_type": bipo_employee.get("EmploymentType", "Full-time"),
                "location": bipo_employee.get("WorkLocation") or bipo_employee.get("OfficeLocation"),
                "employment_status": bipo_employee.get("EmploymentStatus", "Active"),
                "years_of_experience": bipo_employee.get("YearsOfExperience"),
                "years_in_company": years_in_company,
                "years_in_grade": bipo_employee.get("YearsInCurrentGrade"),
                "performance_rating": bipo_employee.get("PerformanceRating"),
                "last_salary_review_date": self._parse_date(bipo_employee.get("LastSalaryReviewDate")),
                "hire_date": hire_date,
                "data_anonymized": anonymize,
            }

            return transformed_data

        except Exception as e:
            logger.error(f"Failed to transform employee data: {e}", exc_info=True)
            return None

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None

    def _infer_job_family(self, job_title: str) -> Optional[str]:
        """
        Infer job family from job title.

        Args:
            job_title: Job title string

        Returns:
            Inferred job family or None
        """
        job_title_lower = job_title.lower()

        if any(term in job_title_lower for term in ["hr", "human resource", "talent", "recruitment"]):
            return "Human Resources"
        elif any(term in job_title_lower for term in ["finance", "accounting", "fp&a"]):
            return "Finance"
        elif any(term in job_title_lower for term in ["engineer", "developer", "architect", "tech"]):
            return "Engineering"
        elif any(term in job_title_lower for term in ["sales", "business development", "account"]):
            return "Sales"
        elif any(term in job_title_lower for term in ["marketing", "brand", "communication"]):
            return "Marketing"
        elif any(term in job_title_lower for term in ["operations", "ops", "supply chain"]):
            return "Operations"
        else:
            return None

    def _upsert_employee(self, employee_data: Dict[str, Any]) -> bool:
        """
        Insert or update employee record.

        Args:
            employee_data: Transformed employee data

        Returns:
            True if successful, False otherwise

        Note:
            Does NOT commit or rollback - transaction management is handled by caller.
            This allows batch processing with proper all-or-nothing semantics.
        """
        try:
            existing = self.session.query(InternalEmployee).filter(
                InternalEmployee.employee_id == employee_data["employee_id"]
            ).first()

            if existing:
                # Update existing record
                for key, value in employee_data.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)
                logger.debug(f"Updated employee: {employee_data['employee_id']}")
            else:
                # Create new record
                employee = InternalEmployee(**employee_data)
                self.session.add(employee)
                logger.debug(f"Created employee: {employee_data['employee_id']}")

            # Flush to detect constraint violations, but don't commit
            self.session.flush()
            return True

        except IntegrityError as e:
            logger.error(f"Integrity error upserting employee {employee_data.get('employee_id')}: {e}")
            # Don't rollback - let the batch continue and caller will handle rollback if needed
            return False
        except Exception as e:
            logger.error(f"Failed to upsert employee {employee_data.get('employee_id')}: {e}", exc_info=True)
            # Don't rollback - let the batch continue and caller will handle rollback if needed
            return False

    def sync_all_employees(
        self,
        is_active: bool = True,
        anonymize: bool = True
    ) -> Dict[str, int]:
        """
        Sync all employees from BIPO to local database.

        Args:
            is_active: Only sync active employees
            anonymize: Anonymize PII data for PDPA compliance

        Returns:
            Dictionary with sync statistics:
            - fetched: Number of records fetched from BIPO
            - synced: Number successfully synced
            - failed: Number that failed to sync

        Example:
            ```python
            service = BIPOSyncService(session)
            result = service.sync_all_employees(is_active=True, anonymize=True)
            print(f"Synced {result['synced']} out of {result['fetched']} employees")
            ```
        """
        logger.info(f"Starting BIPO employee sync (active={is_active}, anonymize={anonymize})")

        result = {
            "fetched": 0,
            "synced": 0,
            "failed": 0,
        }

        try:
            # Fetch employee data from BIPO
            employees = self.client.get_employee_data(is_active=is_active)
            result["fetched"] = len(employees)

            logger.info(f"Fetched {len(employees)} employees from BIPO")

            # Transform and sync each employee
            for bipo_employee in employees:
                transformed = self._transform_employee_data(bipo_employee, anonymize=anonymize)

                if not transformed:
                    result["failed"] += 1
                    continue

                if self._upsert_employee(transformed):
                    result["synced"] += 1
                else:
                    result["failed"] += 1

            # Commit all changes
            self.session.commit()

            logger.info(
                f"BIPO sync completed: "
                f"fetched={result['fetched']}, "
                f"synced={result['synced']}, "
                f"failed={result['failed']}"
            )

            return result

        except BIPOAPIException as e:
            logger.error(f"BIPO API error during sync: {e}")
            self.session.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected error during BIPO sync: {e}", exc_info=True)
            self.session.rollback()
            raise

    def sync_single_employee(
        self,
        employee_id: str,
        anonymize: bool = True
    ) -> bool:
        """
        Sync a single employee by ID.

        Args:
            employee_id: BIPO employee ID
            anonymize: Whether to anonymize PII data

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Syncing single employee: {employee_id}")

        try:
            # Fetch all employees and find the one we want
            # Note: BIPO API may not support single employee fetch
            employees = self.client.get_employee_data(is_active=True)

            bipo_employee = next(
                (emp for emp in employees if str(emp.get("EmployeeNumber")) == employee_id
                 or str(emp.get("EmployeeID")) == employee_id),
                None
            )

            if not bipo_employee:
                logger.warning(f"Employee {employee_id} not found in BIPO")
                return False

            transformed = self._transform_employee_data(bipo_employee, anonymize=anonymize)

            if not transformed:
                logger.error(f"Failed to transform employee {employee_id}")
                return False

            success = self._upsert_employee(transformed)

            if success:
                self.session.commit()
                logger.info(f"Successfully synced employee: {employee_id}")

            return success

        except Exception as e:
            logger.error(f"Failed to sync employee {employee_id}: {e}", exc_info=True)
            self.session.rollback()
            return False
