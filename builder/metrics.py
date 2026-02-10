#!/usr/bin/env python3
"""
Space Measurement - Estimate and measure resume element sizes
"""
import re
import hashlib
from pathlib import Path
from typing import Dict, Optional, Tuple
import subprocess


class SpaceEstimator:
    """Estimates and measures space usage of resume elements"""
    
    # Heuristic constants based on typical LaTeX resume formatting
    # These are rough estimates in points (1 inch = 72 points)
    CHAR_WIDTH_AVG = 5.5  # Average character width in points
    LINE_HEIGHT = 12      # Line height in points
    CHARS_PER_LINE = 95   # Approximate characters per line in resume format
    
    SECTION_HEADER_HEIGHT = 18    # Points for section headers
    EXPERIENCE_HEADER_HEIGHT = 14  # Points for experience/project title
    BULLET_INDENT = 20            # Indent space for bullets
    VERTICAL_SPACING = 4          # Extra vertical space between items
    
    PAGE_HEIGHT = 720  # Approximate usable page height in points (10 inches)
    
    def __init__(self, cache_manager=None):
        self.cache = cache_manager
    
    def estimate_bullet_lines(self, text: str) -> float:
        """Estimate how many lines a bullet will take"""
        # Remove LaTeX commands for length estimation
        clean_text = re.sub(r'\\[a-zA-Z]+\{([^}]*)\}', r'\1', text)
        clean_text = re.sub(r'\\[a-zA-Z]+', '', clean_text)
        
        char_count = len(clean_text)
        estimated_lines = max(1.0, char_count / self.CHARS_PER_LINE)
        
        # Round up to nearest 0.5 for better estimates
        return round(estimated_lines * 2) / 2
    
    def estimate_bullet_height(self, text: str) -> float:
        """Estimate bullet height in points"""
        lines = self.estimate_bullet_lines(text)
        return lines * self.LINE_HEIGHT + self.VERTICAL_SPACING
    
    def estimate_experience_height(self, experience: Dict) -> float:
        """Estimate total height of an experience entry"""
        height = self.EXPERIENCE_HEADER_HEIGHT
        
        bullets = experience.get("bullets", [])
        for bullet_text in bullets:
            height += self.estimate_bullet_height(bullet_text)
        
        height += self.VERTICAL_SPACING
        return height
    
    def estimate_project_height(self, project: Dict) -> float:
        """Estimate total height of a project entry"""
        # Similar structure to experience
        return self.estimate_experience_height(project)
    
    def estimate_skills_height(self, num_skill_lines: int) -> float:
        """Estimate height of skills section"""
        height = self.SECTION_HEADER_HEIGHT
        height += num_skill_lines * (self.LINE_HEIGHT + 2)
        return height
    
    def estimate_education_height(self, num_entries: int) -> float:
        """Estimate height of education section"""
        height = self.SECTION_HEADER_HEIGHT
        # Each entry is roughly 3 lines (degree, institution, details)
        height += num_entries * (3 * self.LINE_HEIGHT + self.VERTICAL_SPACING)
        return height
    
    def estimate_total_height(self, content: Dict) -> float:
        """Estimate total document height from content structure"""
        total = 30  # Base header/footer margins
        
        # Header/contact info
        total += 40
        
        # Experiences
        for exp in content.get("experiences", []):
            total += self.estimate_experience_height(exp)
        
        # Projects
        for proj in content.get("projects", []):
            total += self.estimate_project_height(proj)
        
        # Skills
        num_skill_lines = len(content.get("skills", []))
        if num_skill_lines > 0:
            total += self.estimate_skills_height(num_skill_lines)
        
        # Education
        num_edu = len(content.get("education", []))
        if num_edu > 0:
            total += self.estimate_education_height(num_edu)
        
        return total
    
    def estimate_pages(self, content: Dict) -> float:
        """Estimate number of pages needed"""
        total_height = self.estimate_total_height(content)
        return total_height / self.PAGE_HEIGHT
    
    def count_pdf_pages(self, pdf_path: Path) -> Optional[int]:
        """Count actual pages in compiled PDF"""
        if not pdf_path.exists():
            return None
        
        try:
            # Try using pdfinfo (part of poppler-utils)
            result = subprocess.run(
                ["pdfinfo", str(pdf_path)],
                capture_output=True, text=True, timeout=5
            )
            
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if line.startswith("Pages:"):
                        return int(line.split(":")[1].strip())
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Fallback: try pypdf if available
        try:
            import pypdf
            with open(pdf_path, "rb") as f:
                reader = pypdf.PdfReader(f)
                return len(reader.pages)
        except ImportError:
            pass
        
        # Last resort: try PyPDF2 if available
        try:
            import PyPDF2
            with open(pdf_path, "rb") as f:
                reader = PyPDF2.PdfReader(f)
                return len(reader.pages)
        except ImportError:
            pass
        
        return None
    
    def compute_hash(self, text: str) -> str:
        """Compute hash of text for caching"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def check_bullet_constraints(self, text: str) -> Tuple[bool, Optional[str]]:
        """Check if bullet meets line length constraints"""
        lines = self.estimate_bullet_lines(text)
        
        if lines <= 2.0:
            return True, None
        
        char_target = int(self.CHARS_PER_LINE * 2)
        current_chars = len(text)
        over_by = current_chars - char_target
        
        return False, f"Bullet too long ({lines:.1f} lines, ~{over_by} chars over 2-line limit)"
    
    def suggest_trim_target(self, text: str, target_lines: float = 2.0) -> int:
        """Suggest character count to trim to meet target lines"""
        target_chars = int(target_lines * self.CHARS_PER_LINE)
        return max(0, len(text) - target_chars)
