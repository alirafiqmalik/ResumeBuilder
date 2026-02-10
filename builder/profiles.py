#!/usr/bin/env python3
"""
Profile Manager - Create and manage resume selection profiles
"""
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class ProfileManager:
    """Manages CRUD operations for resume profiles"""
    
    def __init__(self, profiles_dir: Path):
        self.profiles_dir = profiles_dir
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
    
    def list(self) -> List[str]:
        """List all available profile names"""
        return [p.stem for p in self.profiles_dir.glob("*.yaml")]
    
    def exists(self, name: str) -> bool:
        """Check if profile exists"""
        return (self.profiles_dir / f"{name}.yaml").exists()
    
    def load(self, name: str) -> Optional[Dict]:
        """Load profile by name"""
        profile_path = self.profiles_dir / f"{name}.yaml"
        if not profile_path.exists():
            return None
        with open(profile_path) as f:
            return yaml.safe_load(f) or {}
    
    def save(self, name: str, profile: Dict) -> Path:
        """Save profile to file"""
        profile_path = self.profiles_dir / f"{name}.yaml"
        profile["updated_at"] = datetime.now().isoformat()
        with open(profile_path, "w") as f:
            yaml.dump(profile, f, default_flow_style=False, sort_keys=False)
        return profile_path
    
    def delete(self, name: str) -> bool:
        """Delete profile"""
        profile_path = self.profiles_dir / f"{name}.yaml"
        if profile_path.exists():
            profile_path.unlink()
            return True
        return False
    
    def validate_schema(self, profile: Dict) -> tuple[bool, List[str]]:
        """Validate profile schema"""
        errors = []
        
        if "name" not in profile:
            errors.append("Missing required field: name")
        
        if "experiences" in profile:
            if not isinstance(profile["experiences"], dict):
                errors.append("'experiences' must be a dictionary")
            else:
                for exp_id, bullets in profile["experiences"].items():
                    if not isinstance(bullets, list):
                        errors.append(f"Experience '{exp_id}' bullets must be a list")
        
        if "skills" in profile:
            if not isinstance(profile["skills"], dict):
                errors.append("'skills' must be a dictionary")
        
        if "projects" in profile:
            if not isinstance(profile["projects"], dict):
                errors.append("'projects' must be a dictionary")
        
        return len(errors) == 0, errors


class ProfileBuilder:
    """Interactive profile builder"""
    
    def __init__(self, content_dir: Path, manager: ProfileManager):
        self.content_dir = content_dir
        self.manager = manager
        self._experiences = None
        self._skills = None
        self._projects = None
    
    def _load_yaml(self, path: Path) -> dict:
        if not path.exists():
            return {}
        with open(path) as f:
            return yaml.safe_load(f) or {}
    
    @property
    def experiences(self) -> dict:
        if self._experiences is None:
            data = self._load_yaml(self.content_dir / "experiences.yaml")
            self._experiences = data.get("experiences", {})
        return self._experiences
    
    @property
    def skills(self) -> dict:
        if self._skills is None:
            data = self._load_yaml(self.content_dir / "skills.yaml")
            self._skills = data.get("skills", {})
        return self._skills
    
    @property
    def projects(self) -> dict:
        if self._projects is None:
            data = self._load_yaml(self.content_dir / "projects.yaml")
            self._projects = data.get("projects", {})
        return self._projects
    
    def create_empty(self, name: str, description: str = "", inherit_from: str = None) -> Dict:
        """Create empty profile structure"""
        return {
            "name": name,
            "description": description,
            "inherit_from": inherit_from,
            "experiences": {},
            "skills": {},
            "projects": {},
            "created_at": datetime.now().isoformat()
        }
    
    def select_experience_bullets(self, profile: Dict, theme_config: Dict = None) -> Dict:
        """Interactive experience bullet selection (to be called from CLI)"""
        # This method provides data structure for CLI to use
        # Returns organized experience data for selection
        
        exp_data = {}
        for exp_id, exp_content in self.experiences.items():
            base = exp_content.get("base", {})
            bullets = exp_content.get("bullets", [])
            
            exp_data[exp_id] = {
                "title": base.get("title", ""),
                "organization": base.get("organization", ""),
                "dates": base.get("dates", ""),
                "bullets": [
                    {
                        "id": bullet["id"],
                        "text": bullet["text"],
                        "tags": bullet.get("tags", [])
                    }
                    for bullet in bullets
                ]
            }
        
        return exp_data
    
    def select_skills(self, profile: Dict, theme_config: Dict = None) -> Dict:
        """Interactive skill selection (to be called from CLI)"""
        # Returns organized skill data for selection
        
        skills_by_category = {}
        for skill_id, skill_data in self.skills.items():
            category = skill_data.get("category", "Other")
            if category not in skills_by_category:
                skills_by_category[category] = []
            
            skills_by_category[category].append({
                "id": skill_id,
                "default": skill_data.get("default", ""),
                "versions": skill_data.get("versions", {})
            })
        
        return skills_by_category
    
    def add_experience_bullets(self, profile: Dict, exp_id: str, bullet_ids: List[str]) -> Dict:
        """Add specific bullets from an experience to profile"""
        if "experiences" not in profile:
            profile["experiences"] = {}
        profile["experiences"][exp_id] = bullet_ids
        return profile
    
    def remove_experience(self, profile: Dict, exp_id: str) -> Dict:
        """Remove experience from profile"""
        if "experiences" in profile and exp_id in profile["experiences"]:
            del profile["experiences"][exp_id]
        return profile
    
    def add_skills(self, profile: Dict, category: str, skill_ids: List[str]) -> Dict:
        """Add skills by category"""
        if "skills" not in profile:
            profile["skills"] = {}
        profile["skills"][category] = skill_ids
        return profile
    
    def preview_selection(self, profile: Dict) -> str:
        """Generate human-readable preview of profile selections"""
        lines = [f"Profile: {profile.get('name', 'Unnamed')}"]
        
        if profile.get("description"):
            lines.append(f"Description: {profile['description']}")
        
        if profile.get("inherit_from"):
            lines.append(f"Inheriting from theme: {profile['inherit_from']}")
        
        lines.append("\nExperiences:")
        for exp_id, bullet_ids in profile.get("experiences", {}).items():
            exp = self.experiences.get(exp_id, {})
            base = exp.get("base", {})
            lines.append(f"  • {base.get('title', exp_id)} ({len(bullet_ids)} bullets)")
            for bid in bullet_ids:
                bullets = exp.get("bullets", [])
                bullet = next((b for b in bullets if b["id"] == bid), None)
                if bullet:
                    text = bullet["text"][:60] + "..." if len(bullet["text"]) > 60 else bullet["text"]
                    lines.append(f"    - {text}")
        
        lines.append("\nSkills:")
        for category, skill_ids in profile.get("skills", {}).items():
            lines.append(f"  • {category}: {len(skill_ids)} skills")
            for sid in skill_ids:
                skill = self.skills.get(sid, {})
                lines.append(f"    - {skill.get('default', sid)}")
        
        if profile.get("projects"):
            lines.append("\nProjects:")
            for proj_id, bullet_ids in profile.get("projects", {}).items():
                lines.append(f"  • {proj_id} ({len(bullet_ids)} bullets)")
        
        return "\n".join(lines)
