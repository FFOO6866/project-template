"""
HRIS Repository

Provides data access for internal employee data, grade salary bands, and applicants.
Includes privacy-protected queries for PDPA compliance.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, date

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func

from job_pricing.models import (
    InternalEmployee,
    GradeSalaryBand,
    Applicant,
)
from .base import BaseRepository


class HRISRepository(BaseRepository[InternalEmployee]):
    """
    Repository for internal HRIS data operations.

    Provides methods for querying employee benchmarking data,
    salary bands, and applicant expectations with PDPA compliance.
    """

    def __init__(self, session: Session):
        """Initialize with Internal Employee model."""
        super().__init__(InternalEmployee, session)

    def get_by_grade(
        self, grade: str, skip: int = 0, limit: int = 100
    ) -> List[InternalEmployee]:
        """
        Get all employees at a specific grade level.

        Args:
            grade: Grade level (e.g., "M4", "P1", "E3")
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of InternalEmployee instances

        Example:
            mid_level = repo.get_by_grade("M4")
        """
        return (
            self.session.query(InternalEmployee)
            .filter(InternalEmployee.grade == grade)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_job_family(
        self, job_family: str, skip: int = 0, limit: int = 100
    ) -> List[InternalEmployee]:
        """
        Get all employees in a specific job family.

        Args:
            job_family: Job family name
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of InternalEmployee instances

        Example:
            hr_employees = repo.get_by_job_family("Human Resources")
        """
        return (
            self.session.query(InternalEmployee)
            .filter(InternalEmployee.job_family == job_family)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_by_department(
        self, department: str, skip: int = 0, limit: int = 100
    ) -> List[InternalEmployee]:
        """
        Get all employees in a specific department.

        Args:
            department: Department name
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of InternalEmployee instances

        Example:
            it_employees = repo.get_by_department("Information Technology")
        """
        return (
            self.session.query(InternalEmployee)
            .filter(InternalEmployee.department == department)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_salary_statistics(
        self,
        grade: Optional[str] = None,
        job_family: Optional[str] = None,
        department: Optional[str] = None,
        anonymize: bool = True,
    ) -> Dict[str, Any]:
        """
        Get salary statistics for internal employees.

        Args:
            grade: Optional grade filter
            job_family: Optional job family filter
            department: Optional department filter
            anonymize: If True, return None if fewer than 5 records (PDPA compliance)

        Returns:
            Dictionary with salary statistics:
            - count: Number of employees
            - avg_salary: Average salary
            - median_salary: Median salary
            - p25, p75: 25th and 75th percentiles
            - min_salary, max_salary: Salary range
            - None if anonymize=True and count < 5

        Example:
            stats = repo.get_salary_statistics(grade="M4", job_family="Engineering")
            if stats:
                print(f"Average: {stats['avg_salary']}")
        """
        query = self.session.query(InternalEmployee)

        if grade:
            query = query.filter(InternalEmployee.grade == grade)

        if job_family:
            query = query.filter(InternalEmployee.job_family == job_family)

        if department:
            query = query.filter(InternalEmployee.department == department)

        employees = query.all()

        # PDPA compliance: Return None if fewer than 5 records
        if anonymize and len(employees) < 5:
            return None

        if not employees:
            return {
                "count": 0,
                "avg_salary": None,
                "median_salary": None,
                "p25": None,
                "p75": None,
                "min_salary": None,
                "max_salary": None,
            }

        salaries = [emp.current_salary for emp in employees if emp.current_salary]

        if not salaries:
            return {
                "count": len(employees),
                "avg_salary": None,
                "median_salary": None,
                "p25": None,
                "p75": None,
                "min_salary": None,
                "max_salary": None,
            }

        # Calculate statistics
        def percentile(data: List[float], p: float) -> Optional[float]:
            sorted_data = sorted(data)
            k = (len(sorted_data) - 1) * p
            f = int(k)
            c = k - f
            if f + 1 < len(sorted_data):
                return sorted_data[f] + c * (sorted_data[f + 1] - sorted_data[f])
            return sorted_data[f]

        return {
            "count": len(employees),
            "avg_salary": sum(salaries) / len(salaries),
            "median_salary": percentile(salaries, 0.5),
            "p25": percentile(salaries, 0.25),
            "p75": percentile(salaries, 0.75),
            "min_salary": min(salaries),
            "max_salary": max(salaries),
        }

    def get_grade_progression(self, employee_id: str) -> List[InternalEmployee]:
        """
        Get historical grade progression for an employee.

        Note: This assumes historical records exist. Current implementation
        returns single record. Extend if historical tracking is implemented.

        Args:
            employee_id: Employee ID

        Returns:
            List of InternalEmployee records (historical)

        Example:
            history = repo.get_grade_progression("EMP001")
        """
        return (
            self.session.query(InternalEmployee)
            .filter(InternalEmployee.employee_id == employee_id)
            .order_by(InternalEmployee.hire_date)
            .all()
        )

    def get_all_job_families(self) -> List[str]:
        """
        Get a list of all unique job families.

        Returns:
            List of unique job family names

        Example:
            families = repo.get_all_job_families()
        """
        results = (
            self.session.query(InternalEmployee.job_family)
            .distinct()
            .filter(InternalEmployee.job_family.isnot(None))
            .order_by(InternalEmployee.job_family)
            .all()
        )
        return [r[0] for r in results]

    def get_all_departments(self) -> List[str]:
        """
        Get a list of all unique departments.

        Returns:
            List of unique department names

        Example:
            departments = repo.get_all_departments()
        """
        results = (
            self.session.query(InternalEmployee.department)
            .distinct()
            .filter(InternalEmployee.department.isnot(None))
            .order_by(InternalEmployee.department)
            .all()
        )
        return [r[0] for r in results]

    def get_salary_band_by_grade(self, grade: str) -> Optional[GradeSalaryBand]:
        """
        Get the salary band for a specific grade.

        Args:
            grade: Grade level

        Returns:
            GradeSalaryBand instance or None if not found

        Example:
            band = repo.get_salary_band_by_grade("M4")
            if band:
                print(f"Range: {band.salary_min} - {band.salary_max}")
        """
        return (
            self.session.query(GradeSalaryBand)
            .filter(GradeSalaryBand.grade == grade)
            .first()
        )

    def get_all_salary_bands(
        self, skip: int = 0, limit: int = 100
    ) -> List[GradeSalaryBand]:
        """
        Get all salary bands ordered by grade.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of GradeSalaryBand instances

        Example:
            all_bands = repo.get_all_salary_bands()
        """
        return (
            self.session.query(GradeSalaryBand)
            .order_by(GradeSalaryBand.grade)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create_salary_band(
        self,
        grade: str,
        salary_min: float,
        salary_max: float,
        midpoint: float,
        **kwargs,
    ) -> GradeSalaryBand:
        """
        Create a new salary band.

        Args:
            grade: Grade level
            salary_min: Minimum salary for the grade
            salary_max: Maximum salary for the grade
            midpoint: Salary midpoint
            **kwargs: Additional fields (market_position, currency, etc.)

        Returns:
            Created GradeSalaryBand instance

        Example:
            band = repo.create_salary_band(
                grade="M4",
                salary_min=5000,
                salary_max=8000,
                midpoint=6500,
                market_position="P50",
                currency="SGD"
            )
        """
        salary_band = GradeSalaryBand(
            grade=grade,
            salary_min=salary_min,
            salary_max=salary_max,
            midpoint=midpoint,
            **kwargs,
        )
        return self.create(salary_band)

    def update_salary_band(
        self, grade: str, **updates
    ) -> Optional[GradeSalaryBand]:
        """
        Update a salary band by grade.

        Args:
            grade: Grade level
            **updates: Fields to update

        Returns:
            Updated GradeSalaryBand instance or None if not found

        Example:
            updated = repo.update_salary_band(
                grade="M4",
                salary_min=5500,
                salary_max=8500
            )
        """
        band = self.get_salary_band_by_grade(grade)
        if band:
            for key, value in updates.items():
                if hasattr(band, key):
                    setattr(band, key, value)
            self.session.flush()
            self.session.refresh(band)
        return band

    def get_applicants_by_status(
        self, status: str, skip: int = 0, limit: int = 100
    ) -> List[Applicant]:
        """
        Get applicants by application status.

        Args:
            status: Application status (e.g., 'applied', 'interviewed', 'offered')
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Applicant instances

        Example:
            offered = repo.get_applicants_by_status("offered")
        """
        return (
            self.session.query(Applicant)
            .filter(Applicant.application_status == status)
            .order_by(desc(Applicant.application_date))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_applicants_by_position(
        self, position_title: str, skip: int = 0, limit: int = 100
    ) -> List[Applicant]:
        """
        Get applicants for a specific position.

        Args:
            position_title: Position title (partial match)
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Applicant instances

        Example:
            analyst_applicants = repo.get_applicants_by_position("Analyst")
        """
        return (
            self.session.query(Applicant)
            .filter(Applicant.applied_job_title.ilike(f"%{position_title}%"))
            .order_by(desc(Applicant.application_date))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_all_applicants(
        self, skip: int = 0, limit: int = 100, job_family: Optional[str] = None
    ) -> List[Applicant]:
        """
        Get all applicants with optional filtering.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            job_family: Optional job family filter

        Returns:
            List of Applicant instances

        Example:
            all_applicants = repo.get_all_applicants()
            hr_applicants = repo.get_all_applicants(job_family="HR")
        """
        query = self.session.query(Applicant)

        if job_family:
            query = query.filter(Applicant.job_family.ilike(f"%{job_family}%"))

        return (
            query.order_by(desc(Applicant.application_date))
            .offset(skip)
            .limit(limit)
            .all()
        )

    def get_applicant_salary_statistics(
        self,
        position_title: Optional[str] = None,
        anonymize: bool = True,
    ) -> Dict[str, Any]:
        """
        Get salary expectation statistics from applicants.

        Args:
            position_title: Optional position filter
            anonymize: If True, return None if fewer than 5 records (PDPA compliance)

        Returns:
            Dictionary with salary expectation statistics or None if < 5 records

        Example:
            stats = repo.get_applicant_salary_statistics(position_title="Engineer")
        """
        query = self.session.query(Applicant).filter(
            Applicant.expected_salary.isnot(None)
        )

        if position_title:
            query = query.filter(
                Applicant.applied_job_title.ilike(f"%{position_title}%")
            )

        applicants = query.all()

        # PDPA compliance: Return None if fewer than 5 records
        if anonymize and len(applicants) < 5:
            return None

        if not applicants:
            return {
                "count": 0,
                "avg_expected": None,
                "median_expected": None,
                "p25": None,
                "p75": None,
                "min_expected": None,
                "max_expected": None,
            }

        expectations = [
            app.expected_salary for app in applicants if app.expected_salary
        ]

        if not expectations:
            return {
                "count": len(applicants),
                "avg_expected": None,
                "median_expected": None,
                "p25": None,
                "p75": None,
                "min_expected": None,
                "max_expected": None,
            }

        # Calculate statistics
        def percentile(data: List[float], p: float) -> Optional[float]:
            sorted_data = sorted(data)
            k = (len(sorted_data) - 1) * p
            f = int(k)
            c = k - f
            if f + 1 < len(sorted_data):
                return sorted_data[f] + c * (sorted_data[f + 1] - sorted_data[f])
            return sorted_data[f]

        return {
            "count": len(applicants),
            "avg_expected": sum(expectations) / len(expectations),
            "median_expected": percentile(expectations, 0.5),
            "p25": percentile(expectations, 0.25),
            "p75": percentile(expectations, 0.75),
            "min_expected": min(expectations),
            "max_expected": max(expectations),
        }

    def create_applicant(
        self,
        applicant_id: str,
        applied_job_title: str,
        application_date: date,
        expected_salary: Optional[float] = None,
        application_status: str = "Applied",
        **kwargs,
    ) -> Applicant:
        """
        Create a new applicant record.

        Args:
            applicant_id: Unique applicant ID
            applied_job_title: Position title applied for
            application_date: Date of application
            expected_salary: Expected salary (monthly, optional)
            application_status: Application status
            **kwargs: Additional fields (name, current_organisation, etc.)

        Returns:
            Created Applicant instance

        Example:
            applicant = repo.create_applicant(
                applicant_id="APP-2024-001",
                applied_job_title="Software Engineer",
                application_date=date.today(),
                expected_salary=6000,
                application_status="Applied",
                years_of_experience=3,
                name="John Doe"
            )
        """
        applicant = Applicant(
            applicant_id=applicant_id,
            applied_job_title=applied_job_title,
            application_date=application_date,
            expected_salary=expected_salary,
            application_status=application_status,
            **kwargs,
        )
        self.session.add(applicant)
        self.session.flush()
        self.session.refresh(applicant)
        return applicant

    def update_applicant_status(
        self, applicant_id: int, status: str
    ) -> Optional[Applicant]:
        """
        Update an applicant's application status.

        Args:
            applicant_id: Applicant ID
            status: New application status

        Returns:
            Updated Applicant instance or None if not found

        Example:
            updated = repo.update_applicant_status(123, "interviewed")
        """
        return self.update_by_id(applicant_id, application_status=status)
