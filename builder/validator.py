#!/usr/bin/env python3
"""
Constraint Validator - Check resume constraints and provide suggestions
"""
from typing import Dict, List, Tuple
from pathlib import Path


class ValidationResult:
    """Container for validation results"""
    
    def __init__(self):
        self.passed = True
        self.warnings = []
        self.errors = []
        self.info = []
    
    def add_warning(self, message: str):
        self.warnings.append(message)
    
    def add_error(self, message: str):
        self.errors.append(message)
        self.passed = False
    
    def add_info(self, message: str):
        self.info.append(message)
    
    def has_issues(self) -> bool:
        return len(self.warnings) > 0 or len(self.errors) > 0
    
    def format(self) -> str:
        """Format results as readable string"""
        lines = []
        
        if self.passed and not self.warnings:
            lines.append("✓ All constraints satisfied")
        
        if self.errors:
            lines.append("\n❌ ERRORS:")
            for err in self.errors:
                lines.append(f"  • {err}")
        
        if self.warnings:
            lines.append("\n⚠️  WARNINGS:")
            for warn in self.warnings:
                lines.append(f"  • {warn}")
        
        if self.info:
            lines.append("\nℹ️  INFO:")
            for info in self.info:
                lines.append(f"  • {info}")
        
        return "\n".join(lines)


class ConstraintChecker:
    """Validates resume content against constraints"""
    
    def __init__(self, metrics_estimator):
        self.metrics = metrics_estimator
        
        # Default constraints (can be customized)
        self.max_bullet_lines = 2.0
        self.max_pages = 1.0
        self.recommended_experiences = 3
        self.recommended_projects = 3
    
    def validate_bullet(self, bullet_text: str) -> Tuple[bool, Optional[str]]:
        """Validate individual bullet point"""
        return self.metrics.check_bullet_constraints(bullet_text)
    
    def validate_bullets(self, bullets: List[str]) -> ValidationResult:
        """Validate all bullets in a list"""
        result = ValidationResult()
        
        for i, bullet in enumerate(bullets, 1):
            valid, message = self.validate_bullet(bullet)
            if not valid:
                result.add_warning(f"Bullet {i}: {message}")
        
        return result
    
    def validate_content_counts(self, content: Dict, layout_config: Dict = None) -> ValidationResult:
        """Validate experience/project counts"""
        result = ValidationResult()
        
        num_exp = len(content.get("experiences", []))
        num_proj = len(content.get("projects", []))
        
        if num_exp > 4:
            result.add_warning(f"High experience count ({num_exp}), may exceed 1 page")
        elif num_exp < 2:
            result.add_warning(f"Low experience count ({num_exp}), resume may look sparse")
        
        if num_proj > 4:
            result.add_warning(f"High project count ({num_proj}), may exceed 1 page")
        
        total_items = num_exp + num_proj
        if total_items > 6:
            result.add_warning(f"Many total items ({total_items}), likely exceeds 1 page")
        
        return result
    
    def validate_page_estimate(self, content: Dict) -> ValidationResult:
        """Validate estimated page count"""
        result = ValidationResult()
        
        estimated_pages = self.metrics.estimate_pages(content)
        
        result.add_info(f"Estimated pages: {estimated_pages:.2f}")
        
        if estimated_pages > self.max_pages:
            overage = (estimated_pages - self.max_pages) * 100
            result.add_error(f"Content exceeds 1 page by ~{overage:.0f}%")
            result.add_info("Consider removing 1-2 experiences/projects or bullets")
        elif estimated_pages > 0.9:
            result.add_warning("Content is close to page limit (>90% full)")
        elif estimated_pages < 0.7:
            result.add_info("Content is relatively sparse (<70% of page)")
        
        return result
    
    def validate_actual_pages(self, pdf_path: Path) -> ValidationResult:
        """Validate actual compiled PDF page count"""
        result = ValidationResult()
        
        page_count = self.metrics.count_pdf_pages(pdf_path)
        
        if page_count is None:
            result.add_warning("Could not read PDF page count")
            return result
        
        result.add_info(f"Actual pages: {page_count}")
        
        if page_count > self.max_pages:
            result.add_error(f"Resume is {page_count} pages (exceeds 1-page requirement)")
            
            # Calculate how much to reduce
            if page_count == 2:
                result.add_info("Suggestion: Remove 2-3 bullet points or 1 experience/project")
            else:
                result.add_info(f"Suggestion: Reduce content significantly ({page_count} → 1 page)")
        else:
            result.add_info("✓ Resume fits on 1 page")
        
        return result
    
    def validate_full(self, content: Dict, pdf_path: Path = None) -> ValidationResult:
        """Run all validations"""
        result = ValidationResult()
        
        # Validate bullets
        all_bullets = []
        for exp in content.get("experiences", []):
            all_bullets.extend(exp.get("bullets", []))
        for proj in content.get("projects", []):
            all_bullets.extend(proj.get("bullets", []))
        
        bullet_result = self.validate_bullets(all_bullets)
        result.warnings.extend(bullet_result.warnings)
        result.errors.extend(bullet_result.errors)
        
        # Validate counts
        count_result = self.validate_content_counts(content)
        result.warnings.extend(count_result.warnings)
        
        # Validate page estimate
        estimate_result = self.validate_page_estimate(content)
        result.warnings.extend(estimate_result.warnings)
        result.errors.extend(estimate_result.errors)
        result.info.extend(estimate_result.info)
        
        # Validate actual PDF if provided
        if pdf_path and pdf_path.exists():
            actual_result = self.validate_actual_pages(pdf_path)
            result.warnings.extend(actual_result.warnings)
            result.errors.extend(actual_result.errors)
            result.info.extend(actual_result.info)
        
        return result
    
    def suggest_reductions(self, content: Dict, target_reduction: float = 0.2) -> List[str]:
        """Suggest specific items to remove to meet page constraint"""
        suggestions = []
        
        # Analyze experiences by bullet count and content length
        experiences = content.get("experiences", [])
        if experiences:
            # Suggest removing experience with fewest/shortest bullets
            exp_scores = []
            for i, exp in enumerate(experiences):
                bullets = exp.get("bullets", [])
                total_chars = sum(len(b) for b in bullets)
                exp_scores.append((total_chars, i, exp))
            
            exp_scores.sort()
            if exp_scores:
                _, idx, exp = exp_scores[0]
                suggestions.append(f"Remove experience: {exp.get('title', f'#{idx+1}')} (smallest)")
        
        # Suggest removing bullets that are too long
        for exp in experiences:
            title = exp.get('title', 'Unknown')
            for bullet in exp.get("bullets", []):
                lines = self.metrics.estimate_bullet_lines(bullet)
                if lines > 2.5:
                    suggestions.append(f"Shorten bullet in '{title}' ({lines:.1f} lines)")
        
        # Suggest removing projects if many exist
        projects = content.get("projects", [])
        if len(projects) > 3:
            suggestions.append(f"Remove {len(projects) - 3} project(s)")
        
        return suggestions
