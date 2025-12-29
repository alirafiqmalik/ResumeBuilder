#!/usr/bin/env python3
"""
Resume Builder Core - YAML-driven LaTeX generation
"""
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import subprocess
import shutil


class ResumeBuilder:
    def __init__(self, root_dir: Path = None):
        self.root = root_dir or Path(__file__).parent.parent
        self.config_dir = self.root / "config"
        self.content_dir = self.root / "content"
        self.components_dir = self.root / "resume_components"
        self.temp_dir = self.root / "temp"
        self.apps_dir = self.root / "Application"
        
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self._layouts = None
        self._themes = None
        self._experiences = None
        self._skills = None
        self._education = None
        self._projects = None

    def _load_yaml(self, path: Path) -> dict:
        if not path.exists():
            return {}
        with open(path) as f:
            return yaml.safe_load(f) or {}

    @property
    def layouts(self) -> dict:
        if self._layouts is None:
            self._layouts = self._load_yaml(self.config_dir / "layouts.yaml")
        return self._layouts.get("layouts", {})

    @property
    def themes(self) -> dict:
        if self._themes is None:
            self._themes = self._load_yaml(self.config_dir / "themes.yaml")
        return self._themes.get("themes", {})

    @property
    def experiences(self) -> dict:
        if self._experiences is None:
            self._experiences = self._load_yaml(self.content_dir / "experiences.yaml")
        return self._experiences.get("experiences", {})

    @property
    def skills(self) -> dict:
        if self._skills is None:
            self._skills = self._load_yaml(self.content_dir / "skills.yaml")
        return self._skills.get("skills", {})

    @property
    def education(self) -> dict:
        if self._education is None:
            self._education = self._load_yaml(self.content_dir / "education.yaml")
        return self._education.get("education", {})

    @property
    def projects(self) -> dict:
        if self._projects is None:
            self._projects = self._load_yaml(self.content_dir / "projects.yaml")
        return self._projects.get("projects", {})

    def get_layouts(self) -> List[str]:
        return list(self.layouts.keys())

    def get_themes(self) -> List[str]:
        return list(self.themes.keys())

    def score_bullets(self, bullets: List[dict], target_tags: List[str]) -> List[Tuple[int, dict]]:
        """Score bullets based on tag matches, return sorted list"""
        scored = []
        target_set = set(target_tags)
        for bullet in bullets:
            bullet_tags = set(bullet.get("tags", []))
            score = len(bullet_tags & target_set)
            scored.append((score, bullet))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored

    def select_bullets(self, bullets: List[dict], target_tags: List[str], 
                       max_bullets: int = 4) -> List[str]:
        """Select top bullets based on tag matches"""
        scored = self.score_bullets(bullets, target_tags)
        selected = []
        for score, bullet in scored[:max_bullets]:
            if score > 0 or not selected:
                selected.append(bullet["text"])
        return selected if selected else [bullets[0]["text"]] if bullets else []

    def get_skill_line(self, skill_id: str, theme_name: str) -> str:
        """Get skill line for theme, fallback to default"""
        skill = self.skills.get(skill_id, {})
        versions = skill.get("versions", {})
        text = versions.get(theme_name, skill.get("default", ""))
        category = skill.get("category", skill_id)
        return f"\\textbf{{{category}:}} {text}"

    def select_experiences(self, theme_config: dict) -> List[dict]:
        """Select and format experiences based on theme"""
        target_tags = theme_config.get("experience_tags", [])
        max_exp = theme_config.get("max_experiences", 3)
        bullets_per = theme_config.get("bullets_per_experience", 2)
        
        exp_scores = []
        for exp_id, exp_data in self.experiences.items():
            bullets = exp_data.get("bullets", [])
            scored = self.score_bullets(bullets, target_tags)
            total_score = sum(s for s, _ in scored[:bullets_per])
            exp_scores.append((total_score, exp_id, exp_data))
        
        exp_scores.sort(key=lambda x: x[0], reverse=True)
        
        selected = []
        for score, exp_id, exp_data in exp_scores[:max_exp]:
            base = exp_data.get("base", {})
            bullets = exp_data.get("bullets", [])
            selected_bullets = self.select_bullets(bullets, target_tags, bullets_per)
            selected.append({
                "id": exp_id,
                "title": base.get("title", ""),
                "organization": base.get("organization", ""),
                "location": base.get("location", ""),
                "dates": base.get("dates", ""),
                "bullets": selected_bullets
            })
        return selected

    def select_projects(self, theme_config: dict) -> List[dict]:
        """Select and format projects based on theme"""
        target_tags = theme_config.get("project_tags", [])
        max_proj = theme_config.get("max_projects", 4)
        
        proj_scores = []
        for proj_id, proj_data in self.projects.items():
            bullets = proj_data.get("bullets", [])
            scored = self.score_bullets(bullets, target_tags)
            total_score = sum(s for s, _ in scored[:2])
            proj_scores.append((total_score, proj_id, proj_data))
        
        proj_scores.sort(key=lambda x: x[0], reverse=True)
        
        selected = []
        for score, proj_id, proj_data in proj_scores[:max_proj]:
            base = proj_data.get("base", {})
            bullets = proj_data.get("bullets", [])
            selected_bullets = self.select_bullets(bullets, target_tags, 2)
            selected.append({
                "id": proj_id,
                "title": base.get("title", ""),
                "tech": base.get("tech", ""),
                "bullets": selected_bullets
            })
        return selected

    def generate(self, layout: str, theme: str, company: str = None) -> Path:
        """Generate LaTeX resume with given layout and theme"""
        layout_config = self.layouts.get(layout)
        theme_config = self.themes.get(theme)
        
        if not layout_config:
            raise ValueError(f"Unknown layout: {layout}. Available: {self.get_layouts()}")
        if not theme_config:
            raise ValueError(f"Unknown theme: {theme}. Available: {self.get_themes()}")
        
        latex = self._build_document(layout_config, theme_config, theme)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = company.replace(" ", "_") if company else f"{layout}_{theme}"
        tex_file = self.temp_dir / f"{name}_{timestamp}.tex"
        tex_file.write_text(latex)
        
        return tex_file

    def _build_document(self, layout: dict, theme_config: dict, theme_name: str) -> str:
        """Build complete LaTeX document"""
        sections = layout.get("sections", [])
        
        preamble = (self.components_dir / "core" / "preamble.tex").read_text()
        
        parts = [preamble, "\\begin{document}"]
        
        for section in sections:
            content = self._build_section(section, theme_config, theme_name)
            if content:
                parts.append(content)
        
        parts.append("\\end{document}")
        return "\n\n".join(parts)

    def _build_section(self, section: str, theme_config: dict, theme_name: str) -> str:
        """Build individual section content"""
        if section == "header":
            return (self.components_dir / "core" / "header.tex").read_text()
        
        if section == "skills":
            return self._build_skills_section(theme_config, theme_name)
        
        if section == "experience":
            return self._build_experience_section(theme_config)
        
        if section == "education":
            return self._build_education_section(theme_config)
        
        if section == "projects":
            return self._build_projects_section(theme_config)
        
        if section == "honors":
            honors_file = self.components_dir / "extras" / "honors.tex"
            if honors_file.exists():
                return honors_file.read_text()
        
        return ""

    def _build_skills_section(self, theme_config: dict, theme_name: str) -> str:
        """Build skills section"""
        skill_ids = theme_config.get("skills", [])
        
        lines = ["\\section{Technical Skills}"]
        
        for skill_id in skill_ids:
            skill_line = self.get_skill_line(skill_id, theme_name)
            if skill_line:
                lines.append(f"  {skill_line}\\\\")
        
        # lines.append("\\resumeSubHeadingListEnd")
        return "\n".join(lines)

    def _build_experience_section(self, theme_config: dict) -> str:
        """Build experience section"""
        selected = self.select_experiences(theme_config)
        
        lines = ["\\section{Experience}", "\\resumeSubHeadingListStart"]
        
        for exp in selected:
            lines.append("    \\resumeSubheading")
            lines.append(f"      {{{exp['title']}}}{{{exp['dates']}}}")
            lines.append(f"      {{{exp['organization']}}}{{{exp['location']}}}")
            lines.append("      \\resumeItemListStart")
            for bullet in exp["bullets"]:
                lines.append(f"    \\resumeItem{{{bullet}}}")
            lines.append("      \\resumeItemListEnd")
        
        lines.append("\\resumeSubHeadingListEnd")
        return "\n".join(lines)

    def _build_education_section(self, theme_config: dict) -> str:
        """Build education section"""
        lines = ["\\section{Education}", "  \\resumeSubHeadingListStart"]
        
        for edu_id, edu_data in self.education.items():
            base = edu_data.get("base", {})
            details = edu_data.get("details", [])
            
            lines.append("    \\resumeSubheading")
            lines.append(f"      {{{base.get('degree', '')}}}{{{base.get('dates', '')}}}")
            lines.append(f"      {{{base.get('institution', '')}}}{{\\vspace{{7pt}}}}")
            
            for detail in details[:1]:
                lines.append(f"      {{ \\hspace*{{1em}}\\small {detail.get('text', '')} }}")
            
            lines.append("      \\vspace{-4pt}")
        
        lines.append("  \\resumeSubHeadingListEnd")
        return "\n".join(lines)

    def _build_projects_section(self, theme_config: dict) -> str:
        """Build projects section"""
        selected = self.select_projects(theme_config)
        
        lines = ["\\section{Relevant Projects}", "\\resumeSubHeadingListStart"]
        
        for proj in selected:
            lines.append("\\resumeSubheading")
            lines.append(f"  {{{proj['title']}}}{{}}")
            lines.append(f"  {{{proj['tech']}}}{{}}")
            lines.append("  \\resumeItemListStart")
            for bullet in proj["bullets"]:
                lines.append(f"    \\resumeItem{{{bullet}}}")
            lines.append("  \\resumeItemListEnd")
        
        lines.append("\\resumeSubHeadingListEnd")
        return "\n".join(lines)

    def compile_pdf(self, tex_file: Path) -> Path:
        """Compile LaTeX to PDF"""
        result = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode",
             "-output-directory", str(tex_file.parent), str(tex_file)],
            capture_output=True, text=True, cwd=str(self.root)
        )
        
        for ext in [".aux", ".log", ".out"]:
            aux = tex_file.with_suffix(ext)
            if aux.exists():
                aux.unlink()
        
        pdf_file = tex_file.with_suffix(".pdf")
        if not pdf_file.exists():
            print(f"LaTeX compilation failed:\n{result.stdout}\n{result.stderr}")
            return None
        return pdf_file

    def lock(self, tex_file: Path, company: str) -> Tuple[Path, Path]:
        """Lock temp file as final application"""
        company_clean = company.replace(" ", "_")
        app_dir = self.apps_dir / company_clean
        app_dir.mkdir(parents=True, exist_ok=True)
        
        final_tex = app_dir / f"{company_clean}.tex"
        shutil.copy(tex_file, final_tex)
        
        final_pdf = self.compile_pdf(final_tex)
        
        metadata = {
            "company": company,
            "locked_date": datetime.now().isoformat(),
            "source_temp": str(tex_file.name)
        }
        metadata_file = app_dir / f"{company_clean}_metadata.yaml"
        with open(metadata_file, "w") as f:
            yaml.dump(metadata, f, default_flow_style=False)
        
        return final_tex, final_pdf

    def get_latest_temp(self, pattern: str = None) -> Optional[Path]:
        """Get most recent temp file, optionally matching pattern"""
        temps = list(self.temp_dir.glob("*.tex"))
        if pattern:
            temps = [t for t in temps if pattern.lower() in t.name.lower()]
        if not temps:
            return None
        return max(temps, key=lambda p: p.stat().st_mtime)
