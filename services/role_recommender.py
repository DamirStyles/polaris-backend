"""
Role recommendation service
Handles role similarity calculations and personalized recommendations
"""

from typing import Dict, List, Any, Tuple
import random


class RoleRecommender:
    """
    Recommends similar roles based on work style metrics.
    Uses Euclidean distance in 4D metric space.
    """
    
    # Configuration for role recommendations
    TOTAL_MAP_ROLES = 27
    CLOSE_MATCHES_COUNT = 20   # Similar roles for focused exploration
    ODDBALL_COUNT = 7          # Diverse roles for broader exploration
    
    def __init__(self, role_database):
        """
        Initialize recommender with role database.
        
        Args:
            role_database: RoleDatabase instance
        """
        self.role_db = role_database
    
    def get_personalized_roles(
        self, 
        current_role: str, 
        metrics: Dict[str, int] = None,
        count: int = 27
    ) -> Dict[str, Any]:
        """
        Get personalized role recommendations.
        
        Args:
            current_role: User's current role name
            metrics: Work style metrics (technical, creative, business, customer)
            count: Number of roles to return (default 27)
        
        Returns:
            Dict with roles list and metadata
        """
        if not current_role:
            roles_to_show = random.sample(
                self.role_db.all_roles, 
                min(count, len(self.role_db.all_roles))
            )
            return {
                "roles": roles_to_show,
                "personalized": False
            }
        
        normalized = current_role.lower().strip()
        
        if normalized in self.role_db.roles_normalized:
            return self._get_roles_from_database(normalized, count)
        
        if metrics:
            return self._get_roles_from_metrics(metrics, current_role, count)
        
        roles_to_show = random.sample(
            self.role_db.all_roles, 
            min(count, len(self.role_db.all_roles))
        )
        return {
            "roles": roles_to_show,
            "personalized": False
        }
    
    def _get_roles_from_database(self, normalized_role: str, count: int) -> Dict[str, Any]:
        """
        Get roles using pre-calculated overlaps from database.
        
        Args:
            normalized_role: Normalized role name
            count: Number of roles to return
        
        Returns:
            Dict with personalized roles
        """
        canonical_role = self.role_db.roles_normalized[normalized_role]
        overlaps = self.role_db.overlaps.get(canonical_role)
        
        if not overlaps:
            return {"roles": [], "personalized": False}
        
        close = overlaps.get('close', [])
        oddball = overlaps.get('oddball', [])
        
        # Mix close and oddball matches for diverse recommendations
        selected_close = random.sample(close, min(self.CLOSE_MATCHES_COUNT, len(close)))
        selected_oddball = random.sample(oddball, min(self.ODDBALL_COUNT, len(oddball)))
        
        selected_roles = selected_close + selected_oddball
        random.shuffle(selected_roles)
        
        # Convert to full role objects with distance values
        roles_to_show = []
        for sel in selected_roles[:count]:
            role_name = sel['name']
            distance = sel['distance']
            
            role_obj = next(
                (r for r in self.role_db.all_roles if r['name'] == role_name), 
                None
            )
            if role_obj:
                role_with_distance = role_obj.copy()
                role_with_distance['distance'] = distance
                roles_to_show.append(role_with_distance)
        
        return {
            "roles": roles_to_show,
            "personalized": True,
            "current_role": canonical_role
        }
    
    def _get_roles_from_metrics(
        self, 
        metrics: Dict[str, int], 
        current_role: str,
        count: int
    ) -> Dict[str, Any]:
        """
        Get roles by calculating overlaps on-the-fly using AI-estimated metrics.
        
        This is used for edge cases where the role isn't in our database,
        but we have AI-inferred metrics. We calculate similarities dynamically
        instead of using pre-cached overlaps.
        
        Args:
            metrics: Work style metrics dict
            current_role: Original role name
            count: Number of roles to return
        
        Returns:
            Dict with personalized roles
        """
        role_metrics_tuple = (
            metrics.get('technical', 5),
            metrics.get('creative', 5),
            metrics.get('business', 5),
            metrics.get('customer', 5)
        )
        
        overlaps = self.calculate_overlaps_on_fly(role_metrics_tuple)
        
        close = overlaps.get('close', [])
        oddball = overlaps.get('oddball', [])
        
        selected_close = random.sample(close, min(self.CLOSE_MATCHES_COUNT, len(close)))
        selected_oddball = random.sample(oddball, min(self.ODDBALL_COUNT, len(oddball)))
        
        selected_roles = selected_close + selected_oddball
        random.shuffle(selected_roles)
        
        # Convert to full role objects with distance values
        roles_to_show = []
        for sel in selected_roles[:count]:
            role_name = sel['name']
            distance = sel['distance']
            
            role_obj = next(
                (r for r in self.role_db.all_roles if r['name'] == role_name), 
                None
            )
            if role_obj:
                role_with_distance = role_obj.copy()
                role_with_distance['distance'] = distance
                roles_to_show.append(role_with_distance)
        
        return {
            "roles": roles_to_show,
            "personalized": True,
            "current_role": current_role,
            "edge_case": True
        }
    
    def calculate_overlaps_on_fly(
        self,
        role_metrics: Tuple[int, int, int, int],
        close_count: int = None,
        oddball_count: int = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Calculate role overlaps for roles not in database.
        
        Args:
            role_metrics: Work style metrics tuple (technical, creative, business, customer)
            close_count: Number of close matches to return (default: CLOSE_MATCHES_COUNT)
            oddball_count: Number of diverse matches to return (default: ODDBALL_COUNT)
        
        Returns:
            Dict with 'close' and 'oddball' lists
        """
        # Use class constants as defaults
        if close_count is None:
            close_count = self.CLOSE_MATCHES_COUNT
        if oddball_count is None:
            oddball_count = self.ODDBALL_COUNT
        
        distances = []
        
        for other in self.role_db.all_roles:
            other_metrics = (
                other.get('technical', 5),
                other.get('creative', 5),
                other.get('business', 5),
                other.get('customer', 5)
            )
            
            distance = self.calculate_distance(role_metrics, other_metrics)
            distances.append((other['name'], distance))
        
        distances.sort(key=lambda x: x[1])
        
        # Close matches: lowest distances
        close_matches = [
            {'name': d[0], 'distance': d[1]} 
            for d in distances[:close_count]
        ]
        
        # Oddball: highest distances for diversity
        oddball_candidates = [
            {'name': d[0], 'distance': d[1]} 
            for d in distances[-10:]
        ]
        oddball = oddball_candidates[:oddball_count]
        
        return {
            'close': close_matches,
            'oddball': oddball
        }
    
    def calculate_distance(
        self, 
        metrics1: Tuple[int, int, int, int],
        metrics2: Tuple[int, int, int, int]
    ) -> float:
        """
        Calculate Euclidean distance between two metric vectors.
        
        Args:
            metrics1: First metric tuple (technical, creative, business, customer)
            metrics2: Second metric tuple
        
        Returns:
            Euclidean distance
        """
        return sum((a - b)**2 for a, b in zip(metrics1, metrics2)) ** 0.5