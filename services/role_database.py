"""
Role database management
Handles loading and caching of role data from JSON files
"""

import json
from pathlib import Path
from typing import Dict, List, Any


class RoleDatabase:
    """
    Manages role data and pre-calculated overlaps.
    Initialized once at app startup for O(1) lookups.
    """
    
    # Configuration for pre-calculating role overlaps
    CLOSE_POOL_SIZE = 15   # Number of close matches to pre-calculate
    ODDBALL_POOL_SIZE = 5  # Number of diverse matches to pre-calculate
    
    def __init__(self, roles_file_path: Path):
        """
        Initialize role database with path to roles JSON file.
        
        Args:
            roles_file_path: Path to roles_technology.json
        """
        self.roles_file = roles_file_path
        self._roles_normalized = None
        self._overlaps = None
        self._all_roles = None
    
    @property
    def roles_normalized(self) -> Dict[str, str]:
        """
        Get normalized role name mapping.
        Lazy-loads on first access.
        
        Returns:
            Dict mapping lowercase role names to proper case names
            Example: {"software engineer": "Software Engineer"}
        """
        if self._roles_normalized is None:
            self._roles_normalized = self._load_normalized()
        return self._roles_normalized
    
    @property
    def overlaps(self) -> Dict[str, Any]:
        """
        Get pre-calculated role overlaps.
        Lazy-loads on first access.
        
        Returns:
            Dict mapping role names to similar roles
            Example: {"Software Engineer": {"close": [...], "oddball": [...]}}
        """
        if self._overlaps is None:
            self._overlaps = self._calculate_overlaps()
        return self._overlaps
    
    @property
    def all_roles(self) -> List[Dict[str, Any]]:
        """
        Get all roles with metrics.
        Lazy-loads on first access.
        
        Returns:
            List of role objects with name, technical, creative, business, customer scores
        """
        if self._all_roles is None:
            self._all_roles = self._load_all_roles()
        return self._all_roles
    
    def _load_normalized(self) -> Dict[str, str]:
        """
        Load all technology roles and create normalized name lookup.
        
        Returns:
            Dict mapping normalized (lowercase) names to original names
        """
        if not self.roles_file.exists():
            print(f"Warning: {self.roles_file} not found")
            return {}
        
        with open(self.roles_file, 'r') as f:
            data = json.load(f)
        
        role_map = {}
        for role_obj in data.get('roles', []):
            role_name = role_obj['name']
            normalized = role_name.lower().strip()
            role_map[normalized] = role_name
        
        return role_map
    
    def _load_all_roles(self) -> List[Dict[str, Any]]:
        """
        Load all roles with their work style metrics.
        
        Returns:
            List of role objects with metrics
        """
        if not self.roles_file.exists():
            return []
        
        with open(self.roles_file, 'r') as f:
            data = json.load(f)
        
        return data.get('roles', [])
    
    def _calculate_overlaps(self) -> Dict[str, Any]:
        """
        Pre-calculate which roles are similar to each role based on metric distances.
        This runs once at startup to avoid repeated calculations.
        
        Uses Euclidean distance in 4D metric space (technical, creative, business, customer).
        
        Returns:
            Dict mapping role_name -> {close: [...], oddball: [...]}
            Each entry includes distance value for proper map positioning
        """
        overlaps = {}
        
        for role in self.all_roles:
            role_name = role['name']
            role_metrics = (
                role.get('technical', 5),
                role.get('creative', 5),
                role.get('business', 5),
                role.get('customer', 5)
            )
            
            distances = []
            for other in self.all_roles:
                if other['name'] == role_name:
                    continue
                
                other_metrics = (
                    other.get('technical', 5),
                    other.get('creative', 5),
                    other.get('business', 5),
                    other.get('customer', 5)
                )
                
                # Euclidean distance in 4D metric space
                distance = sum((a - b)**2 for a, b in zip(role_metrics, other_metrics)) ** 0.5
                distances.append((other['name'], distance))
            
            # Sort by distance (closest first)
            distances.sort(key=lambda x: x[1])
            
            # Close matches: roles with lowest distances
            close_matches = [
                {'name': d[0], 'distance': d[1]} 
                for d in distances[:self.CLOSE_POOL_SIZE]
            ]
            
            # Oddball: roles with highest distances for diverse recommendations
            # Calculate pool size (slightly larger than needed for variety)
            oddball_pool = int(self.ODDBALL_POOL_SIZE * 1.6)
            oddball_candidates = [
                {'name': d[0], 'distance': d[1]} 
                for d in distances[-oddball_pool:]
            ]
            oddball = oddball_candidates[:self.ODDBALL_POOL_SIZE]
            
            overlaps[role_name] = {
                'close': close_matches,
                'oddball': oddball
            }
        
        return overlaps