"""
Skill Extraction Service using OpenAI

Extracts technical skills and competencies from job descriptions
using OpenAI's GPT models with structured output.
"""

import json
import logging
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

import openai

from job_pricing.core.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class ExtractedSkill:
    """Represents a skill extracted from a job description."""

    skill_name: str
    skill_category: str
    is_required: bool = True
    proficiency_level: Optional[str] = None


class SkillExtractionService:
    """
    Service for extracting skills from job descriptions using OpenAI.

    Uses structured prompts and JSON output to reliably extract:
    - Technical skills (programming languages, frameworks, tools)
    - Domain skills (industry-specific knowledge)
    - Soft skills (leadership, communication, etc.)
    """

    # Skill categories we want to extract
    SKILL_CATEGORIES = [
        "Programming Language",
        "Framework/Library",
        "Database",
        "Cloud Platform",
        "DevOps/Tools",
        "Data Science/ML",
        "Domain Knowledge",
        "Soft Skills",
        "Certification",
        "Other Technical",
    ]

    def __init__(self):
        """Initialize skill extraction service with OpenAI configuration."""
        self.settings = get_settings()
        openai.api_key = self.settings.OPENAI_API_KEY
        self.model = self.settings.OPENAI_MODEL_DEFAULT
        self.temperature = self.settings.OPENAI_TEMPERATURE
        self.max_tokens = self.settings.OPENAI_MAX_TOKENS

    def extract_skills(
        self, job_title: str, job_description: str
    ) -> List[ExtractedSkill]:
        """
        Extract skills from a job title and description.

        Uses OpenAI to identify and categorize skills mentioned in the job posting.

        Args:
            job_title: Job title
            job_description: Full job description text

        Returns:
            List of ExtractedSkill objects

        Example:
            >>> service = SkillExtractionService()
            >>> skills = service.extract_skills(
            ...     "Senior Data Scientist",
            ...     "We need a data scientist with Python, SQL, and ML experience..."
            ... )
            >>> for skill in skills:
            ...     print(f"{skill.skill_name} ({skill.skill_category})")
        """
        prompt = self._build_extraction_prompt(job_title, job_description)

        try:
            # Try with JSON mode first (for newer models)
            try:
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": self._get_system_prompt(),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"},
                )
            except Exception as json_mode_error:
                # Fall back to regular mode for older models
                logger.info(f"JSON mode not supported, using regular mode: {json_mode_error}")
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": self._get_system_prompt() + "\n\nIMPORTANT: Return ONLY valid JSON, no other text.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )

            # Parse response
            content = response.choices[0].message.content

            # Extract JSON if wrapped in markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            skills_data = json.loads(content)

            # Convert to ExtractedSkill objects
            extracted_skills = []
            for skill_dict in skills_data.get("skills", []):
                skill = ExtractedSkill(
                    skill_name=skill_dict["skill_name"],
                    skill_category=skill_dict["skill_category"],
                    is_required=skill_dict.get("is_required", True),
                    proficiency_level=skill_dict.get("proficiency_level"),
                )
                extracted_skills.append(skill)

            return extracted_skills

        except Exception as e:
            logger.error(f"Error extracting skills with OpenAI: {e}", exc_info=True)
            # Return empty list on error rather than failing completely
            return []

    def _get_system_prompt(self) -> str:
        """Get the system prompt for skill extraction."""
        categories_str = ", ".join(self.SKILL_CATEGORIES)

        return f"""You are an expert at analyzing job descriptions and extracting technical skills and competencies.

Your task is to:
1. Read the job title and description carefully
2. Identify ALL skills mentioned (technical, domain, and soft skills)
3. Categorize each skill into one of these categories: {categories_str}
4. Determine if each skill is required or preferred
5. Estimate proficiency level if mentioned (Basic, Intermediate, Advanced)

Guidelines:
- Extract specific skills (e.g., "Python" not just "programming")
- Include frameworks, tools, methodologies, and certifications
- For soft skills, only include those explicitly mentioned or clearly required
- Normalize skill names (e.g., "Javascript" -> "JavaScript", "ML" -> "Machine Learning")
- Don't infer skills that aren't mentioned or clearly implied

Output Format:
Return a JSON object with a "skills" array. Each skill should have:
{{
  "skills": [
    {{
      "skill_name": "Python",
      "skill_category": "Programming Language",
      "is_required": true,
      "proficiency_level": "Advanced"
    }},
    ...
  ]
}}"""

    def _build_extraction_prompt(
        self, job_title: str, job_description: str
    ) -> str:
        """Build the extraction prompt from job details."""
        return f"""Extract all skills from this job posting:

**Job Title:** {job_title}

**Job Description:**
{job_description}

Please extract and categorize all skills mentioned in this job posting. Return the result in JSON format as specified."""

    def extract_skills_simple(
        self, job_title: str, job_description: str
    ) -> List[Tuple[str, str]]:
        """
        Simplified version that returns (skill_name, skill_category) tuples.

        Useful for direct integration with SkillMatchingService.

        Args:
            job_title: Job title
            job_description: Full job description text

        Returns:
            List of (skill_name, skill_category) tuples

        Example:
            >>> service = SkillExtractionService()
            >>> skills = service.extract_skills_simple("Data Analyst", "Requires SQL and Python")
            >>> print(skills)
            [("SQL", "Database"), ("Python", "Programming Language")]
        """
        extracted_skills = self.extract_skills(job_title, job_description)
        return [(skill.skill_name, skill.skill_category) for skill in extracted_skills]

    def get_statistics(self, skills: List[ExtractedSkill]) -> Dict[str, any]:
        """
        Get statistics about extracted skills.

        Args:
            skills: List of extracted skills

        Returns:
            Dictionary with statistics:
            - total_skills: Total number of skills
            - by_category: Count by category
            - required_count: Number of required skills
            - proficiency_levels: Count by proficiency level
        """
        total_skills = len(skills)
        by_category = {}
        required_count = 0
        proficiency_levels = {}

        for skill in skills:
            # Count by category
            category = skill.skill_category
            by_category[category] = by_category.get(category, 0) + 1

            # Count required
            if skill.is_required:
                required_count += 1

            # Count by proficiency
            if skill.proficiency_level:
                level = skill.proficiency_level
                proficiency_levels[level] = proficiency_levels.get(level, 0) + 1

        return {
            "total_skills": total_skills,
            "by_category": by_category,
            "required_count": required_count,
            "preferred_count": total_skills - required_count,
            "proficiency_levels": proficiency_levels,
        }


# Convenience function for quick extraction
def extract_skills_from_job(
    job_title: str, job_description: str
) -> List[Tuple[str, str]]:
    """
    Convenience function to extract skills from a job posting.

    Args:
        job_title: Job title
        job_description: Full job description

    Returns:
        List of (skill_name, skill_category) tuples

    Example:
        >>> from job_pricing.services.skill_extraction_service import extract_skills_from_job
        >>> skills = extract_skills_from_job("Software Engineer", "Python, Django, PostgreSQL required")
        >>> print(skills)
        [("Python", "Programming Language"), ("Django", "Framework/Library"), ("PostgreSQL", "Database")]
    """
    service = SkillExtractionService()
    return service.extract_skills_simple(job_title, job_description)
