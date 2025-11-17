"""
Salary Recommendation Service

Provides salary recommendations by:
1. Matching user job to Mercer job library using semantic search
2. Retrieving Mercer market salary data for matched jobs
3. Applying location cost-of-living adjustments
4. Generating salary bands with confidence scores
"""

import logging
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from ..models.mercer import MercerJobLibrary, MercerMarketData
from ..models.supporting import LocationIndex
from ..utils.database import get_db_context
from .job_matching_service import JobMatchingService

logger = logging.getLogger(__name__)


class SalaryRecommendationService:
    """Service for generating salary recommendations based on market data."""

    def __init__(self, session: Optional[Session] = None):
        """Initialize salary recommendation service."""
        self.session = session
        self.job_matcher = JobMatchingService(session)

    def recommend_salary(
        self,
        job_title: str,
        job_description: str = "",
        location: str = "Central Business District",
        job_family: Optional[str] = None,
        career_level: Optional[str] = None
    ) -> Dict:
        """
        Generate salary recommendation for a job.

        Args:
            job_title: Job title to price
            job_description: Job description for better matching
            location: Singapore location for cost-of-living adjustment
            job_family: Optional family filter (e.g., "HRM", "ICT")
            career_level: Optional level filter (e.g., "M5", "ET2")

        Returns:
            Comprehensive salary recommendation with confidence scores
        """
        # Step 1: Find similar Mercer jobs using semantic search
        similar_jobs = self.job_matcher.find_similar_jobs(
            job_title=job_title,
            job_description=job_description,
            job_family=job_family,
            career_level=career_level,
            top_k=3
        )

        if not similar_jobs:
            return {
                "success": False,
                "error": "No similar jobs found in Mercer library",
                "recommendation": None
            }

        # Step 2: Get market salary data for matched jobs
        market_data = self._get_market_data_for_jobs(
            [job["job_code"] for job in similar_jobs]
        )

        if not market_data:
            return {
                "success": False,
                "error": "No market salary data found for matched jobs",
                "matched_jobs": similar_jobs,
                "recommendation": None
            }

        # Step 3: Calculate weighted salary percentiles
        salary_data = self._calculate_weighted_salaries(
            similar_jobs, market_data
        )

        # Step 4: Apply location cost-of-living adjustment
        location_index = self._get_location_index(location)
        adjusted_salaries = self._adjust_for_location(salary_data, location_index)

        # Step 5: Generate recommendation
        recommendation = self._generate_recommendation(
            job_title=job_title,
            location=location,
            matched_jobs=similar_jobs,
            market_data=market_data,
            salary_data=adjusted_salaries,
            location_index=location_index
        )

        return {
            "success": True,
            "recommendation": recommendation
        }

    def _get_market_data_for_jobs(self, job_codes: List[str]) -> List[Dict]:
        """Retrieve market salary data for given Mercer job codes."""
        market_data = []

        if self.session:
            results = self.session.query(MercerMarketData).filter(
                MercerMarketData.job_code.in_(job_codes)
            ).all()
            # Convert to dict within the session
            for row in results:
                market_data.append({
                    "job_code": row.job_code,
                    "p25": float(row.p25) if row.p25 else None,
                    "p50": float(row.p50) if row.p50 else None,
                    "p75": float(row.p75) if row.p75 else None,
                    "sample_size": row.sample_size,
                    "survey_date": row.survey_date,
                    "currency": row.currency
                })
        else:
            with get_db_context() as session:
                results = session.query(MercerMarketData).filter(
                    MercerMarketData.job_code.in_(job_codes)
                ).all()
                # Convert to dict within the session
                for row in results:
                    market_data.append({
                        "job_code": row.job_code,
                        "p25": float(row.p25) if row.p25 else None,
                        "p50": float(row.p50) if row.p50 else None,
                        "p75": float(row.p75) if row.p75 else None,
                        "sample_size": row.sample_size,
                        "survey_date": row.survey_date,
                        "currency": row.currency
                    })

        return market_data

    def _calculate_weighted_salaries(
        self,
        matched_jobs: List[Dict],
        market_data: List[Dict]
    ) -> Dict:
        """
        Calculate weighted salary percentiles based on match confidence.

        Jobs with higher similarity scores get higher weights.
        """
        # Create mapping of job_code to market data
        market_map = {m["job_code"]: m for m in market_data}

        weighted_p25 = 0.0
        weighted_p50 = 0.0
        weighted_p75 = 0.0
        total_weight = 0.0

        for job in matched_jobs:
            job_code = job["job_code"]
            if job_code not in market_map:
                continue

            market = market_map[job_code]
            if not market["p50"]:  # Skip if no salary data
                continue

            # Weight = similarity score
            weight = job["similarity_score"]

            weighted_p25 += (market["p25"] or market["p50"]) * weight
            weighted_p50 += market["p50"] * weight
            weighted_p75 += (market["p75"] or market["p50"]) * weight
            total_weight += weight

        if total_weight == 0:
            return None

        return {
            "p25": round(weighted_p25 / total_weight, 2),
            "p50": round(weighted_p50 / total_weight, 2),
            "p75": round(weighted_p75 / total_weight, 2),
            "data_points": len([j for j in matched_jobs if j["job_code"] in market_map])
        }

    def _get_location_index(self, location: str) -> float:
        """Get cost-of-living index for location."""
        if self.session:
            result = self.session.query(LocationIndex).filter(
                LocationIndex.location_name == location
            ).first()
        else:
            with get_db_context() as session:
                result = session.query(LocationIndex).filter(
                    LocationIndex.location_name == location
                ).first()

        if result:
            return float(result.cost_of_living_index)

        # Default index if location not found
        return 0.90  # Conservative estimate

    def _adjust_for_location(self, salary_data: Dict, location_index: float) -> Dict:
        """Apply location cost-of-living adjustment to salaries."""
        if not salary_data:
            return None

        return {
            "p25": round(salary_data["p25"] * location_index, 2),
            "p50": round(salary_data["p50"] * location_index, 2),
            "p75": round(salary_data["p75"] * location_index, 2),
            "data_points": salary_data["data_points"]
        }

    def _calculate_confidence_score(
        self,
        matched_jobs: List[Dict],
        market_data: List[Dict],
        data_points: int
    ) -> Dict:
        """
        Calculate confidence score for the recommendation.

        Factors:
        1. Job match quality (highest similarity score)
        2. Number of data points
        3. Sample sizes in market data
        """
        # Factor 1: Best match quality (0-30 points)
        best_match_score = matched_jobs[0]["similarity_score"] if matched_jobs else 0
        match_points = best_match_score * 30

        # Factor 2: Data points adequacy (0-35 points)
        if data_points >= 3:
            data_points_score = 35
        elif data_points == 2:
            data_points_score = 25
        elif data_points == 1:
            data_points_score = 15
        else:
            data_points_score = 0

        # Factor 3: Sample sizes (0-35 points)
        total_sample_size = sum([m.get("sample_size", 0) or 0 for m in market_data])
        if total_sample_size >= 100:
            sample_points = 35
        elif total_sample_size >= 50:
            sample_points = 25
        elif total_sample_size >= 20:
            sample_points = 15
        else:
            sample_points = 5

        # Total confidence
        total_confidence = match_points + data_points_score + sample_points

        # Classify confidence level
        if total_confidence >= 75:
            level = "High"
            recommendation = "Proceed with confidence"
        elif total_confidence >= 50:
            level = "Medium"
            recommendation = "Review recommended range carefully"
        else:
            level = "Low"
            recommendation = "Manual review recommended - limited data"

        return {
            "score": round(total_confidence, 2),
            "level": level,
            "recommendation": recommendation,
            "factors": {
                "job_match": round(match_points, 2),
                "data_points": data_points_score,
                "sample_size": sample_points
            }
        }

    def _generate_recommendation(
        self,
        job_title: str,
        location: str,
        matched_jobs: List[Dict],
        market_data: List[Dict],
        salary_data: Dict,
        location_index: float
    ) -> Dict:
        """Generate final salary recommendation output."""

        confidence = self._calculate_confidence_score(
            matched_jobs, market_data, salary_data["data_points"]
        )

        return {
            "job_title": job_title,
            "location": location,
            "currency": "SGD",
            "period": "annual",

            # Salary recommendation (P25-P75 range)
            "recommended_range": {
                "min": salary_data["p25"],
                "max": salary_data["p75"],
                "target": salary_data["p50"]
            },

            # Full distribution
            "percentiles": {
                "p25": salary_data["p25"],
                "p50": salary_data["p50"],
                "p75": salary_data["p75"]
            },

            # Confidence metrics
            "confidence": confidence,

            # Matched jobs (top 3)
            "matched_jobs": [
                {
                    "job_code": j["job_code"],
                    "job_title": j["job_title"],
                    "similarity": f"{j['similarity_score']:.1%}",
                    "confidence": j["confidence"]
                }
                for j in matched_jobs
            ],

            # Data sources
            "data_sources": {
                "mercer_market_data": {
                    "jobs_matched": len(market_data),
                    "total_sample_size": sum([m.get("sample_size", 0) or 0 for m in market_data]),
                    "survey": "2024 Singapore Total Remuneration Survey"
                }
            },

            # Location adjustment
            "location_adjustment": {
                "location": location,
                "cost_of_living_index": location_index,
                "note": f"Salaries adjusted by {location_index:.0%} for {location} location"
            },

            # Explanation
            "summary": (
                f"Based on analysis of {len(market_data)} Mercer benchmark jobs "
                f"with {len(matched_jobs)} similar matches, the recommended salary range "
                f"for {job_title} in {location} is SGD {salary_data['p25']:,.0f} - "
                f"{salary_data['p75']:,.0f} annually (target: SGD {salary_data['p50']:,.0f}). "
                f"Confidence level: {confidence['level']}."
            )
        }


# Example usage
if __name__ == "__main__":
    service = SalaryRecommendationService()

    # Test recommendation
    result = service.recommend_salary(
        job_title="HR Director, Total Rewards",
        job_description="Responsible for designing and managing compensation strategy",
        location="Central Business District",
        job_family="HRM"
    )

    if result["success"]:
        rec = result["recommendation"]
        logger.info(f"\nSalary Recommendation for: {rec['job_title']}")
        logger.info(f"Location: {rec['location']}")
        logger.info(f"\nRecommended Range: SGD {rec['recommended_range']['min']:,.0f} - {rec['recommended_range']['max']:,.0f}")
        logger.info(f"Target Salary: SGD {rec['recommended_range']['target']:,.0f}")
        logger.info(f"\nConfidence: {rec['confidence']['level']} ({rec['confidence']['score']:.0f}/100)")
        logger.info(f"\nMatched to: {rec['matched_jobs'][0]['job_title']} ({rec['matched_jobs'][0]['similarity']})")
    else:
        logger.error(f"Error: {result['error']}")
