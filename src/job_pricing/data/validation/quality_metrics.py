"""
Data Quality Metrics

Calculate and report data quality metrics for all data sources.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


def calculate_quality_metrics(session: Session) -> Dict[str, Any]:
    """
    Calculate comprehensive data quality metrics.

    Args:
        session: SQLAlchemy database session

    Returns:
        Dictionary with quality metrics for all data sources

    Example:
        >>> metrics = calculate_quality_metrics(session)
        >>> print(f"Mercer embedding coverage: {metrics['mercer']['embedding_coverage']:.1%}")
    """
    metrics = {
        "generated_at": datetime.now().isoformat(),
        "mercer": _calculate_mercer_metrics(session),
        "ssg": _calculate_ssg_metrics(session),
        "scraped": _calculate_scraped_metrics(session),
        "hris": _calculate_hris_metrics(session),
        "overall": {}
    }

    # Calculate overall metrics
    metrics["overall"] = _calculate_overall_metrics(metrics)

    return metrics


def _calculate_mercer_metrics(session: Session) -> Dict[str, Any]:
    """
    Calculate quality metrics for Mercer data.

    Args:
        session: Database session

    Returns:
        Dictionary with Mercer metrics
    """
    try:
        # Import models here to avoid circular imports
        from src.job_pricing.models.mercer import MercerJobLibrary, MercerMarketData

        # Total jobs
        total_jobs = session.query(MercerJobLibrary).count()

        # Jobs with embeddings
        with_embeddings = session.query(MercerJobLibrary).filter(
            MercerJobLibrary.embedding.isnot(None)
        ).count()

        # Jobs with complete IPE data
        with_complete_ipe = session.query(MercerJobLibrary).filter(
            MercerJobLibrary.ipe_minimum.isnot(None),
            MercerJobLibrary.ipe_midpoint.isnot(None),
            MercerJobLibrary.ipe_maximum.isnot(None)
        ).count()

        # Market data records
        market_data_count = session.query(MercerMarketData).count()

        # Jobs with market data
        jobs_with_market_data = session.query(MercerJobLibrary).filter(
            MercerJobLibrary.market_data.any()
        ).count()

        return {
            "total_jobs": total_jobs,
            "with_embeddings": with_embeddings,
            "embedding_coverage": with_embeddings / total_jobs if total_jobs > 0 else 0,
            "with_complete_ipe": with_complete_ipe,
            "ipe_coverage": with_complete_ipe / total_jobs if total_jobs > 0 else 0,
            "market_data_records": market_data_count,
            "jobs_with_market_data": jobs_with_market_data,
            "market_data_coverage": jobs_with_market_data / total_jobs if total_jobs > 0 else 0,
        }

    except Exception as e:
        logger.error(f"Error calculating Mercer metrics: {e}")
        return {"error": str(e)}


def _calculate_ssg_metrics(session: Session) -> Dict[str, Any]:
    """
    Calculate quality metrics for SSG Skills Framework data.

    Args:
        session: Database session

    Returns:
        Dictionary with SSG metrics
    """
    try:
        from src.job_pricing.models.ssg import SSGJobRoles, SSGTSC, SSGJobRoleTSCMapping

        # Job roles
        total_roles = session.query(SSGJobRoles).count()

        # TSC
        total_tsc = session.query(SSGTSC).count()

        # Mappings
        total_mappings = session.query(SSGJobRoleTSCMapping).count()

        # Critical skills
        critical_mappings = session.query(SSGJobRoleTSCMapping).filter(
            SSGJobRoleTSCMapping.is_critical == True
        ).count()

        # Average skills per role
        avg_skills_per_role = total_mappings / total_roles if total_roles > 0 else 0

        # Roles with no skills
        roles_without_skills = session.query(SSGJobRoles).filter(
            ~SSGJobRoles.tsc_mappings.any()
        ).count()

        return {
            "total_job_roles": total_roles,
            "total_tsc": total_tsc,
            "total_mappings": total_mappings,
            "critical_mappings": critical_mappings,
            "avg_skills_per_role": avg_skills_per_role,
            "roles_without_skills": roles_without_skills,
            "roles_with_skills_coverage": (total_roles - roles_without_skills) / total_roles if total_roles > 0 else 0,
        }

    except Exception as e:
        logger.error(f"Error calculating SSG metrics: {e}")
        return {"error": str(e)}


def _calculate_scraped_metrics(session: Session) -> Dict[str, Any]:
    """
    Calculate quality metrics for scraped job data.

    Args:
        session: Database session

    Returns:
        Dictionary with scraped data metrics
    """
    try:
        from src.job_pricing.models.scraping import ScrapedJobListings

        # Total listings
        total_listings = session.query(ScrapedJobListings).count()

        # Active listings (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        active_listings = session.query(ScrapedJobListings).filter(
            ScrapedJobListings.last_seen_date >= thirty_days_ago
        ).count()

        # Listings with salary data
        with_salary = session.query(ScrapedJobListings).filter(
            ScrapedJobListings.salary_min.isnot(None),
            ScrapedJobListings.salary_max.isnot(None)
        ).count()

        # Listings with skills
        with_skills = session.query(ScrapedJobListings).filter(
            ScrapedJobListings.skills.isnot(None)
        ).count()

        # By source
        from sqlalchemy import func
        by_source = dict(
            session.query(
                ScrapedJobListings.source,
                func.count(ScrapedJobListings.id)
            ).group_by(ScrapedJobListings.source).all()
        )

        return {
            "total_listings": total_listings,
            "active_listings": active_listings,
            "active_rate": active_listings / total_listings if total_listings > 0 else 0,
            "with_salary": with_salary,
            "salary_coverage": with_salary / total_listings if total_listings > 0 else 0,
            "with_skills": with_skills,
            "skills_coverage": with_skills / total_listings if total_listings > 0 else 0,
            "by_source": by_source,
        }

    except Exception as e:
        logger.error(f"Error calculating scraped metrics: {e}")
        return {"error": str(e)}


def _calculate_hris_metrics(session: Session) -> Dict[str, Any]:
    """
    Calculate quality metrics for internal HR data.

    Args:
        session: Database session

    Returns:
        Dictionary with HRIS metrics
    """
    try:
        from src.job_pricing.models.hris import InternalEmployees, GradeSalaryBands

        # Total employees
        total_employees = session.query(InternalEmployees).count()

        # Salary bands
        total_bands = session.query(GradeSalaryBands).count()

        # Employees by grade
        from sqlalchemy import func
        by_grade = dict(
            session.query(
                InternalEmployees.grade,
                func.count(InternalEmployees.id)
            ).group_by(InternalEmployees.grade).all()
        )

        return {
            "total_employees": total_employees,
            "total_salary_bands": total_bands,
            "employees_by_grade": by_grade,
        }

    except Exception as e:
        logger.error(f"Error calculating HRIS metrics: {e}")
        return {"error": str(e)}


def _calculate_overall_metrics(metrics: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate overall data quality metrics.

    Args:
        metrics: Dictionary with all source metrics

    Returns:
        Dictionary with overall metrics
    """
    mercer = metrics.get("mercer", {})
    ssg = metrics.get("ssg", {})
    scraped = metrics.get("scraped", {})
    hris = metrics.get("hris", {})

    total_records = (
        mercer.get("total_jobs", 0) +
        mercer.get("market_data_records", 0) +
        ssg.get("total_job_roles", 0) +
        ssg.get("total_tsc", 0) +
        ssg.get("total_mappings", 0) +
        scraped.get("total_listings", 0) +
        hris.get("total_employees", 0)
    )

    # Overall quality score (weighted average)
    quality_scores = []

    if mercer.get("embedding_coverage") is not None:
        quality_scores.append(mercer["embedding_coverage"])

    if ssg.get("roles_with_skills_coverage") is not None:
        quality_scores.append(ssg["roles_with_skills_coverage"])

    if scraped.get("salary_coverage") is not None:
        quality_scores.append(scraped["salary_coverage"])

    overall_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

    return {
        "total_records": total_records,
        "overall_quality_score": overall_quality,
        "quality_grade": _get_quality_grade(overall_quality),
    }


def _get_quality_grade(score: float) -> str:
    """
    Convert quality score to letter grade.

    Args:
        score: Quality score (0-1)

    Returns:
        Letter grade (A-F)
    """
    if score >= 0.95:
        return "A+"
    elif score >= 0.90:
        return "A"
    elif score >= 0.85:
        return "A-"
    elif score >= 0.80:
        return "B+"
    elif score >= 0.75:
        return "B"
    elif score >= 0.70:
        return "B-"
    elif score >= 0.65:
        return "C+"
    elif score >= 0.60:
        return "C"
    elif score >= 0.55:
        return "C-"
    elif score >= 0.50:
        return "D"
    else:
        return "F"


def generate_quality_report(
    session: Session,
    output_format: str = "text"
) -> str:
    """
    Generate human-readable quality report.

    Args:
        session: Database session
        output_format: Output format ("text" or "html")

    Returns:
        Formatted quality report string

    Example:
        >>> report = generate_quality_report(session, output_format="text")
        >>> print(report)
    """
    metrics = calculate_quality_metrics(session)

    if output_format == "html":
        return _generate_html_report(metrics)
    else:
        return _generate_text_report(metrics)


def _generate_text_report(metrics: Dict[str, Any]) -> str:
    """Generate text-formatted quality report."""
    report = []
    report.append("=" * 70)
    report.append("DATA QUALITY REPORT")
    report.append("=" * 70)
    report.append(f"Generated: {metrics['generated_at']}")
    report.append("")

    # Overall
    overall = metrics.get("overall", {})
    report.append("OVERALL METRICS")
    report.append("-" * 70)
    report.append(f"Total Records: {overall.get('total_records', 0):,}")
    report.append(f"Quality Score: {overall.get('overall_quality_score', 0):.1%}")
    report.append(f"Quality Grade: {overall.get('quality_grade', 'N/A')}")
    report.append("")

    # Mercer
    mercer = metrics.get("mercer", {})
    if "error" not in mercer:
        report.append("MERCER JOB LIBRARY")
        report.append("-" * 70)
        report.append(f"Total Jobs: {mercer.get('total_jobs', 0):,}")
        report.append(f"Embedding Coverage: {mercer.get('embedding_coverage', 0):.1%}")
        report.append(f"IPE Coverage: {mercer.get('ipe_coverage', 0):.1%}")
        report.append(f"Market Data Records: {mercer.get('market_data_records', 0):,}")
        report.append(f"Market Data Coverage: {mercer.get('market_data_coverage', 0):.1%}")
        report.append("")

    # SSG
    ssg = metrics.get("ssg", {})
    if "error" not in ssg:
        report.append("SSG SKILLS FRAMEWORK")
        report.append("-" * 70)
        report.append(f"Job Roles: {ssg.get('total_job_roles', 0):,}")
        report.append(f"TSC (Skills): {ssg.get('total_tsc', 0):,}")
        report.append(f"Mappings: {ssg.get('total_mappings', 0):,}")
        report.append(f"Avg Skills per Role: {ssg.get('avg_skills_per_role', 0):.1f}")
        report.append(f"Roles with Skills: {ssg.get('roles_with_skills_coverage', 0):.1%}")
        report.append("")

    # Scraped
    scraped = metrics.get("scraped", {})
    if "error" not in scraped:
        report.append("SCRAPED JOB LISTINGS")
        report.append("-" * 70)
        report.append(f"Total Listings: {scraped.get('total_listings', 0):,}")
        report.append(f"Active (30 days): {scraped.get('active_listings', 0):,}")
        report.append(f"Salary Coverage: {scraped.get('salary_coverage', 0):.1%}")
        report.append(f"Skills Coverage: {scraped.get('skills_coverage', 0):.1%}")
        report.append("")

    report.append("=" * 70)

    return "\n".join(report)


def _generate_html_report(metrics: Dict[str, Any]) -> str:
    """Generate HTML-formatted quality report."""
    # NOTE: Basic HTML implementation using preformatted text.
    # Enhanced HTML styling can be added as needed.
    text_report = _generate_text_report(metrics)
    return f"<pre>{text_report}</pre>"
