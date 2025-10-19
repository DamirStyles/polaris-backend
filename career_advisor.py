# career_advisor.py
"""
LLM-powered career analysis using Google Gemini

Provides AI capabilities for:
- Tech role validation and metrics estimation
- Skills suggestions for roles
- Role detail page generation
"""

import os
import logging
import json
from typing import Dict, List, Any, Optional
import google.generativeai as genai


class LLMCareerAnalyzer:
    """Career analyzer using Google Gemini AI for role insights"""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the LLM analyzer with Google Gemini.
        
        Args:
            api_key: Google API key (defaults to GOOGLE_API_KEY env var)
        """
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable must be set")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash-exp")
        self._setup_logging()

    def _setup_logging(self):
        """Configure logging"""
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    def suggest_skills_for_role(self, role: str) -> Dict[str, Any]:
        """
        Suggest the 12 most important skills for a job role.
        
        Args:
            role: Job title (e.g., "Software Engineer")
        
        Returns:
            dict: {"role": str, "skills": List[str]}
        """
        prompt = f"""List the 12 most important skills for this job role: "{role}"

Respond with JSON in this exact format:
{{
  "role": "{role}",
  "skills": ["Skill1", "Skill2", "Skill3", ...]
}}

Guidelines:
- Include both technical and soft skills
- List skills in order of importance
- Use common, recognizable skill names
- Include exactly 12 skills
- Skills should be concise (1-3 words each)

Examples:
- Technical: Python, JavaScript, SQL, React, AWS, Git
- Soft: Communication, Leadership, Problem Solving, Teamwork

Provide ONLY the JSON response, no other text."""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Extract JSON from markdown code blocks if present
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0].strip()
            
            result = json.loads(result_text)
            result['role'] = role
            result['skills'] = result.get('skills', [])[:12]
            
            self.logger.info(f"Suggested {len(result['skills'])} skills for '{role}'")
            return result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error for role '{role}': {e}")
            return {"role": role, "skills": []}
        except Exception as e:
            self.logger.error(f"Error suggesting skills for '{role}': {e}")
            return {"role": role, "skills": []}

    def validate_tech_role_and_get_metrics(self, role: str) -> Dict[str, Any]:
        """
        Validate if a role is tech-related and estimate work style metrics.
        Used for roles not in the database.
        
        Args:
            role: Job title to analyze
        
        Returns:
            dict: {
                "role": str,
                "is_tech_role": bool,
                "confidence": float (0-1),
                "technical": int (1-10),
                "creative": int (1-10),
                "business": int (1-10),
                "customer": int (1-10)
            }
        """
        prompt = f"""Determine if this is a technology role and estimate work style metrics.

Role: "{role}"

Respond with JSON in this exact format:
{{
  "role": "{role}",
  "is_tech_role": true/false,
  "confidence": 0.0-1.0,
  "technical": 1-10,
  "creative": 1-10,
  "business": 1-10,
  "customer": 1-10
}}

A technology role is:
- Software development, engineering, IT, data, DevOps, QA, security, etc.
- Any role primarily involving software, systems, or technical infrastructure
- Technical product/project management roles
- NOT: General sales, marketing, HR, finance (unless highly technical like "Sales Engineer")

Work Style Metrics (rate 1-10):
- technical: How technical/coding-focused (1=none, 10=pure engineering)
- creative: How much creative/design thinking (1=none, 10=highly creative)
- business: How much business/strategy focus (1=none, 10=executive level)
- customer: How much direct customer interaction (1=none, 10=constant contact)

Examples:
- Software Engineer: is_tech_role=true, technical=9, creative=7, business=7, customer=5
- Product Manager (Tech): is_tech_role=true, technical=5, creative=9, business=10, customer=8
- Data Scientist: is_tech_role=true, technical=9, creative=9, business=6, customer=5
- DevOps Engineer: is_tech_role=true, technical=9, creative=8, business=5, customer=3
- Marketing Manager: is_tech_role=false, technical=2, creative=7, business=9, customer=8

Provide ONLY the JSON response, no other text."""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Extract JSON from markdown code blocks if present
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0].strip()
            
            result = json.loads(result_text)
            
            # Validate and normalize
            result['role'] = role
            result['is_tech_role'] = bool(result.get('is_tech_role', False))
            result['confidence'] = float(result.get('confidence', 0.5))
            result['technical'] = max(1, min(10, int(result.get('technical', 5))))
            result['creative'] = max(1, min(10, int(result.get('creative', 5))))
            result['business'] = max(1, min(10, int(result.get('business', 5))))
            result['customer'] = max(1, min(10, int(result.get('customer', 5))))
            
            self.logger.info(
                f"Validated '{role}': tech_role={result['is_tech_role']}, "
                f"confidence={result['confidence']}, metrics: T={result['technical']} "
                f"C={result['creative']} B={result['business']} Cu={result['customer']}"
            )
            
            return result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error for role '{role}': {e}")
            return {
                "role": role,
                "is_tech_role": False,
                "confidence": 0.0,
                "technical": 5,
                "creative": 5,
                "business": 5,
                "customer": 5
            }
        except Exception as e:
            self.logger.error(f"Error validating role '{role}': {e}")
            return {
                "role": role,
                "is_tech_role": False,
                "confidence": 0.0,
                "technical": 5,
                "creative": 5,
                "business": 5,
                "customer": 5
            }

    def generate_role_pages(
        self, 
        role_name: str, 
        current_role: str, 
        metrics: Dict[str, int],
        user_skills: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate AI-powered content for 4 role detail pages.
        
        Args:
            role_name: Target role to generate content for
            current_role: User's current role for personalization
            metrics: Work style metrics for current role
            user_skills: List of user's selected skills
        
        Returns:
            dict: {"pages": [...]} with 4 pages of content
        """
        user_skills = user_skills or []
        skills_context = ""
        if user_skills:
            skills_context = f"\nUser's selected skills: {', '.join(user_skills)}"
        
        prompt = f"""Generate personalized content for these 4 pages about the {role_name} role for someone currently in {current_role}.

Current role metrics: Technical={metrics.get('technical', 5)}, Creative={metrics.get('creative', 5)}, Business={metrics.get('business', 5)}, Customer={metrics.get('customer', 5)}{skills_context}

CRITICAL LENGTH REQUIREMENTS - MUST BE FOLLOWED EXACTLY:
- Overview description: 120-150 characters maximum
- Day in life tasks: EXACTLY 5 tasks, each 80-100 characters
- Sweet spots explanation: 120-150 characters maximum  
- Areas for growth explanation: 120-150 characters maximum
- Skill names: 2-4 words each, NO LONGER

Respond with JSON:
{{
  "pages": [
    {{
      "type": "overview",
      "description": "Role overview (120-150 chars)",
      "salary": "$XXk - $XXk",
      "degree": "Bachelor's degree in X",
      "source": "U.S. Bureau of Labor Statistics"
    }},
    {{
      "type": "day_in_life",
      "tasks": ["Task 1 (80-100 chars)", "Task 2 (80-100 chars)", ... EXACTLY 5 tasks]
    }},
    {{
      "type": "sweet_spots",
      "skills": ["Skill1", "Skill2", ... EXACTLY 7 skills, 2-4 words each],
      "explanation": "How their skills transfer (120-150 chars)"
    }},
    {{
      "type": "areas_for_growth",
      "skills": ["Skill1", "Skill2", ... EXACTLY 7 skills, 2-4 words each],
      "explanation": "Skills to develop (120-150 chars)"
    }}
  ]
}}

Content Guidelines:
- Be specific to {current_role} → {role_name} transition
- SWEET SPOTS: If user provided skills, show which of THEIR skills transfer. Only skills they selected or typical for {current_role}
- AREAS FOR GROWTH: Show NEW skills {role_name} needs that user likely doesn't have
- Start each task with an action verb
- Be concise and scannable

STRICT VALIDATION:
- Count every character carefully
- If description/explanation exceeds 150 chars, rewrite shorter
- Each task must be 80-100 chars - no exceptions
- Skills must be 2-4 words - if longer, abbreviate
- Exactly 5 tasks, exactly 7 skills per section

Provide ONLY the JSON response, no other text."""

        try:
            response = self.model.generate_content(prompt)
            result_text = response.text.strip()
            
            # Extract JSON from markdown code blocks if present
            if '```json' in result_text:
                result_text = result_text.split('```json')[1].split('```')[0].strip()
            elif '```' in result_text:
                result_text = result_text.split('```')[1].split('```')[0].strip()
            
            result = json.loads(result_text)
            result = self._enforce_content_limits(result)
            
            self.logger.info(f"Generated 4 pages for '{role_name}'")
            return result
            
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON parsing error for '{role_name}': {e}")
            return self._get_fallback_pages(role_name, current_role, user_skills)
        except Exception as e:
            self.logger.error(f"Error generating pages for '{role_name}': {e}")
            return self._get_fallback_pages(role_name, current_role, user_skills)

    def _enforce_content_limits(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce character limits on generated content as a safety net."""
        pages = result.get('pages', [])
        
        for page in pages:
            if not isinstance(page, dict):
                continue
            
            if page.get('type') == 'overview':
                desc = page.get('description', '')
                if len(desc) > 150:
                    page['description'] = desc[:147] + '...'
            
            if page.get('type') == 'day_in_life':
                tasks = page.get('tasks', [])
                truncated_tasks = []
                for task in tasks[:5]:
                    if len(task) > 100:
                        truncated_tasks.append(task[:97] + '...')
                    else:
                        truncated_tasks.append(task)
                
                while len(truncated_tasks) < 5:
                    truncated_tasks.append("Collaborate with team members on projects and tasks.")
                
                page['tasks'] = truncated_tasks
            
            if page.get('type') in ['sweet_spots', 'areas_for_growth']:
                skills = page.get('skills', [])
                truncated_skills = []
                for skill in skills[:7]:
                    words = skill.split()
                    if len(words) > 4:
                        truncated_skills.append(' '.join(words[:4]))
                    else:
                        truncated_skills.append(skill)
                
                while len(truncated_skills) < 7:
                    truncated_skills.append("Core Skills")
                
                page['skills'] = truncated_skills
                
                explanation = page.get('explanation', '')
                if len(explanation) > 150:
                    page['explanation'] = explanation[:147] + '...'
        
        return result

    def _get_fallback_pages(self, role_name: str, current_role: str, user_skills: List[str]) -> Dict[str, Any]:
        """Generate fallback pages when LLM fails."""
        user_skills = user_skills or []
        
        if user_skills:
            sweet_spot_skills = user_skills[:5]
            sweet_spot_explanation = f"Your skills in {', '.join(sweet_spot_skills[:3])} provide a strong foundation for {role_name}."
        else:
            sweet_spot_skills = ["Problem Solving", "Communication", "Technical Skills", "Collaboration", "Analytical Thinking"]
            sweet_spot_explanation = f"Your background in {current_role} provides foundational skills that transfer to {role_name}."
        
        while len(sweet_spot_skills) < 7:
            sweet_spot_skills.append("Core Skills")
        
        return {
            "pages": [
                {
                    "type": "overview",
                    "description": f"A {role_name} is a professional role in the tech industry.",
                    "salary": "$80k - $120k",
                    "degree": "Bachelor's degree",
                    "source": "Bureau of Labor Statistics"
                },
                {
                    "type": "day_in_life",
                    "tasks": [
                        "Complete assigned tasks and projects",
                        "Collaborate with team members",
                        "Participate in meetings and reviews",
                        "Document work and progress",
                        "Solve technical problems"
                    ]
                },
                {
                    "type": "sweet_spots",
                    "skills": sweet_spot_skills[:7],
                    "explanation": sweet_spot_explanation[:150]
                },
                {
                    "type": "areas_for_growth",
                    "skills": ["Advanced Technical", "Industry Knowledge", "Leadership", "Project Management", "Strategic Thinking", "Communication", "Analytics"],
                    "explanation": f"To excel as a {role_name}, develop expertise in specialized areas beyond {current_role}."[:150]
                }
            ]
        }