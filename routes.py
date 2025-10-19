# routes.py - API endpoints for Polaris Career Path Navigator
# Handles industry inference, role recommendations, and AI-generated content

import json
import random
from pathlib import Path
from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any
from difflib import get_close_matches

from services.role_database import RoleDatabase
from services.role_recommender import RoleRecommender

api = Blueprint('api', __name__, url_prefix='/api')

# Global singletons (loaded once at startup)
_role_database = None
_role_recommender = None


def get_role_database():
    """Get singleton role database instance"""
    global _role_database
    if _role_database is None:
        roles_file = Path(__file__).parent / 'data' / 'roles_technology.json'
        _role_database = RoleDatabase(roles_file)
    return _role_database


def get_role_recommender():
    """Get singleton role recommender instance"""
    global _role_recommender
    if _role_recommender is None:
        _role_recommender = RoleRecommender(get_role_database())
    return _role_recommender


def init_role_database():
    """Initialize role database at app startup"""
    db = get_role_database()
    print(f"✓ Loaded {len(db.roles_normalized)} tech roles into database")
    print(f"✓ Calculated overlaps for {len(db.overlaps)} roles")


def get_llm_analyzer():
    """Get LLM analyzer from Flask app config"""
    return current_app.config['LLM_ANALYZER']


def error_response(message: str, status_code: int = 400) -> tuple:
    """Return standardized error response"""
    return jsonify({'error': message}), status_code


# API Endpoints

@api.route('/infer-industry', methods=['POST'])
def infer_industry():
    """Infer industry from role title using 3-layer optimization"""
    try:
        data = request.get_json()
        
        if not data or 'role' not in data:
            return error_response("Missing required field: role")
        
        role = data['role']
        normalized = role.lower().strip()
        
        if len(normalized) < 2:
            return error_response("Role name too short")
        
        if len(normalized) > 100:
            return error_response("Role name too long")
        
        db = get_role_database()
        
        # Layer 1: Exact match in database
        if normalized in db.roles_normalized:
            canonical_role = db.roles_normalized[normalized]
            role_obj = next((r for r in db.all_roles if r['name'] == canonical_role), None)
            
            if role_obj:
                return jsonify({
                    "role": canonical_role,
                    "industry": "Technology",
                    "confidence": 1.0,
                    "source": "database",
                    "technical": role_obj.get('technical', 5),
                    "creative": role_obj.get('creative', 5),
                    "business": role_obj.get('business', 5),
                    "customer": role_obj.get('customer', 5)
                })
        
        # Layer 2: Fuzzy match for typos
        fuzzy_matches = get_close_matches(
            normalized, 
            db.roles_normalized.keys(), 
            n=1, 
            cutoff=0.85
        )
        
        if fuzzy_matches:
            matched_role = db.roles_normalized[fuzzy_matches[0]]
            role_obj = next((r for r in db.all_roles if r['name'] == matched_role), None)
            
            if role_obj:
                return jsonify({
                    "role": matched_role,
                    "industry": "Technology",
                    "confidence": 0.95,
                    "source": "fuzzy_match",
                    "original_input": role,
                    "technical": role_obj.get('technical', 5),
                    "creative": role_obj.get('creative', 5),
                    "business": role_obj.get('business', 5),
                    "customer": role_obj.get('customer', 5)
                })
        
        # Layer 3: AI inference for unknown roles
        llm_analyzer = get_llm_analyzer()
        result = llm_analyzer.infer_industry(role)
        result['source'] = 'ai'
        
        if result.get('confidence', 0) < 0.75:
            return error_response(
                "Could not identify role. Please enter a specific job title.",
                400
            )
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error in infer_industry: {e}")
        return error_response(str(e), 500)


@api.route('/map/roles', methods=['POST'])
def get_map_roles():
    """Get 27 personalized roles for the interactive map"""
    try:
        data = request.get_json()
        current_role = data.get('current_role') if data else None
        metrics = data.get('metrics') if data else None
        
        recommender = get_role_recommender()
        result = recommender.get_personalized_roles(
            current_role=current_role,
            metrics=metrics,
            count=27
        )
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error in get_map_roles: {e}")
        return error_response(str(e), 500)


@api.route('/role/<role_name>/pages', methods=['POST'])
def get_role_pages(role_name):
    """Generate 4 pages of AI content for a specific role"""
    try:
        data = request.get_json()
        current_role = data.get('current_role')
        metrics = data.get('metrics')
        user_skills = data.get('user_skills', [])
        
        llm_analyzer = get_llm_analyzer()
        result = llm_analyzer.generate_role_pages(
            role_name, 
            current_role, 
            metrics,
            user_skills
        )
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error in get_role_pages: {e}")
        return error_response(str(e), 500)


@api.route('/suggest-skills', methods=['POST'])
def suggest_skills():
    """Suggest relevant skills for a given role using AI"""
    try:
        data = request.get_json()
        
        if not data or 'role' not in data:
            return error_response("Missing required field: role")
        
        role = data['role']
        
        llm_analyzer = get_llm_analyzer()
        result = llm_analyzer.suggest_skills_for_role(role)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error in suggest_skills: {e}")
        return error_response(str(e), 500)