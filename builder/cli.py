#!/usr/bin/env python3
"""
Resume Builder CLI
Usage: python -m builder [command] [options]
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core import ResumeBuilder
from profiles import ProfileManager, ProfileBuilder
from metrics import SpaceEstimator
from cache import MeasurementCache
from validator import ConstraintChecker


def cmd_list(args, builder: ResumeBuilder):
    """List available layouts and themes"""
    print("\n=== Available Layouts ===")
    for name, config in builder.layouts.items():
        desc = config.get("description", "")
        sections = ", ".join(config.get("sections", []))
        print(f"  {name:20s} - {desc}")
        print(f"  {'':20s}   Sections: {sections}")
    
    print("\n=== Available Themes ===")
    for name, config in builder.themes.items():
        desc = config.get("description", "")
        tags = ", ".join(config.get("experience_tags", [])[:5])
        print(f"  {name:20s} - {desc}")
        print(f"  {'':20s}   Tags: {tags}")
    
    # List profiles
    profile_mgr = ProfileManager(builder.profiles_dir)
    profiles = profile_mgr.list()
    if profiles:
        print("\n=== Available Profiles ===")
        for pname in profiles:
            profile = profile_mgr.load(pname)
            desc = profile.get("description", "")
            print(f"  {pname:20s} - {desc}")
    
    print()


def cmd_new(args, builder: ResumeBuilder):
    """Generate new resume from layout + theme or profile"""
    layout = args.layout
    theme = args.theme
    company = args.company
    profile = args.profile
    
    # If profile specified, use it
    if profile:
        builder_with_profile = ResumeBuilder(profile=profile)
        print(f"\nGenerating resume with profile: {profile}")
        if not builder_with_profile._profile_data:
            print(f"❌ Profile '{profile}' not found")
            print(f"Available profiles: {', '.join(ProfileManager(builder.profiles_dir).list())}")
            sys.exit(1)
        builder = builder_with_profile
    else:
        print(f"\nGenerating resume: layout={layout}, theme={theme}")
    
    if company:
        print(f"  Company: {company}")
    
    try:
        tex_file = builder.generate(layout, theme, company)
        print(f"\n✓ Generated: {tex_file}")
        
        pdf_file = builder.compile_pdf(tex_file, validate=True)
        if pdf_file:
            print(f"✓ Compiled: {pdf_file}")
        else:
            print("✗ PDF compilation failed - check LaTeX errors")
        
        print(f"\nNext steps:")
        print(f"  1. Review PDF: open {pdf_file}")
        print(f"  2. Edit if needed: nano {tex_file}")
        name = company or f"{layout}_{theme}"
        print(f"  3. Lock: make lock COMPANY={name}")
        print(f"  4. Validate: python -m builder validate --file {pdf_file}")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def cmd_analyze(args, builder: ResumeBuilder):
    """Analyze what content will be selected for a theme"""
    theme_name = args.theme
    theme_config = builder.themes.get(theme_name)
    
    if not theme_config:
        print(f"Unknown theme: {theme_name}")
        print(f"Available: {', '.join(builder.get_themes())}")
        sys.exit(1)
    
    print(f"\n=== Theme Analysis: {theme_name} ===")
    print(f"Description: {theme_config.get('description', '')}")
    print(f"Experience tags: {', '.join(theme_config.get('experience_tags', []))}")
    print(f"Project tags: {', '.join(theme_config.get('project_tags', []))}")
    
    print("\n--- Selected Experiences ---")
    selected_exp = builder.select_experiences(theme_config)
    for exp in selected_exp:
        print(f"\n  {exp['title']}")
        print(f"  {exp['organization']}")
        for i, bullet in enumerate(exp['bullets'], 1):
            lines = builder.metrics.estimate_bullet_lines(bullet)
            bullet_preview = bullet[:80] + "..." if len(bullet) > 80 else bullet
            print(f"    {i}. [{lines:.1f} lines] {bullet_preview}")
    
    print("\n--- Selected Projects ---")
    selected_proj = builder.select_projects(theme_config)
    for proj in selected_proj:
        print(f"\n  {proj['title']}")
        for i, bullet in enumerate(proj['bullets'], 1):
            lines = builder.metrics.estimate_bullet_lines(bullet)
            bullet_preview = bullet[:80] + "..." if len(bullet) > 80 else bullet
            print(f"    {i}. [{lines:.1f} lines] {bullet_preview}")
    
    print("\n--- Skills ---")
    for skill_id in theme_config.get("skills", []):
        line = builder.get_skill_line(skill_id, theme_name)
        print(f"  {line[:100]}...")
    
    # Estimate page usage
    content = {
        "experiences": selected_exp,
        "projects": selected_proj,
        "skills": theme_config.get("skills", []),
        "education": list(builder.education.values())
    }
    estimated_pages = builder.metrics.estimate_pages(content)
    print(f"\n📏 Estimated pages: {estimated_pages:.2f}")
    if estimated_pages > 1.0:
        print("   ⚠️  Content may exceed 1 page")
    
    print()


def cmd_edit_profile(args, builder: ResumeBuilder):
    """Interactive profile builder"""
    profile_name = args.name
    profile_mgr = ProfileManager(builder.profiles_dir)
    profile_builder = ProfileBuilder(builder.content_dir, profile_mgr)
    
    # Load existing or create new
    if profile_mgr.exists(profile_name):
        print(f"Editing existing profile: {profile_name}")
        profile = profile_mgr.load(profile_name)
    else:
        print(f"Creating new profile: {profile_name}")
        profile = profile_builder.create_empty(profile_name, args.description or "")
    
    print("\n=== Profile Editor ===")
    print("Select experiences and skills to include in your resume.")
    print()
    
    # Experience selection
    if not args.skip_experiences:
        print("--- EXPERIENCES ---")
        exp_data = profile_builder.select_experience_bullets(profile)
        
        for exp_id, exp_info in exp_data.items():
            print(f"\n{exp_info['title']} - {exp_info['organization']}")
            print(f"Tags: {', '.join(exp_info['bullets'][0]['tags'] if exp_info['bullets'] else [])}")
            
            # Ask user if they want to include this experience
            response = input(f"Include this experience? (y/n/s=select bullets): ").strip().lower()
            
            if response == 'y':
                # Include all bullets
                bullet_ids = [b['id'] for b in exp_info['bullets']]
                profile = profile_builder.add_experience_bullets(profile, exp_id, bullet_ids)
                print(f"  ✓ Added all {len(bullet_ids)} bullets")
            
            elif response == 's':
                # Let user select specific bullets
                print("  Bullets:")
                for i, bullet in enumerate(exp_info['bullets'], 1):
                    lines = builder.metrics.estimate_bullet_lines(bullet['text'])
                    preview = bullet['text'][:60] + "..." if len(bullet['text']) > 60 else bullet['text']
                    print(f"    {i}. [{lines:.1f} lines] {preview}")
                
                selection = input("  Enter bullet numbers to include (comma-separated, or 'all'): ").strip()
                
                if selection.lower() == 'all':
                    bullet_ids = [b['id'] for b in exp_info['bullets']]
                else:
                    try:
                        indices = [int(x.strip()) - 1 for x in selection.split(',')]
                        bullet_ids = [exp_info['bullets'][i]['id'] for i in indices if 0 <= i < len(exp_info['bullets'])]
                    except (ValueError, IndexError):
                        print("  Invalid selection, skipping")
                        continue
                
                if bullet_ids:
                    profile = profile_builder.add_experience_bullets(profile, exp_id, bullet_ids)
                    print(f"  ✓ Added {len(bullet_ids)} bullets")
    
    # Skills selection
    if not args.skip_skills:
        print("\n--- SKILLS ---")
        skills_data = profile_builder.select_skills(profile)
        
        for category, skills in skills_data.items():
            print(f"\n{category}:")
            for skill in skills:
                print(f"  - {skill['default']}")
            
            response = input(f"Include all {category} skills? (y/n/s=select specific): ").strip().lower()
            
            if response == 'y':
                skill_ids = [s['id'] for s in skills]
                profile = profile_builder.add_skills(profile, category, skill_ids)
                print(f"  ✓ Added all {len(skill_ids)} skills")
            
            elif response == 's':
                print("  Enter skill numbers (comma-separated):")
                for i, skill in enumerate(skills, 1):
                    print(f"    {i}. {skill['id']}")
                
                selection = input("  Selection: ").strip()
                try:
                    indices = [int(x.strip()) - 1 for x in selection.split(',')]
                    skill_ids = [skills[i]['id'] for i in indices if 0 <= i < len(skills)]
                    if skill_ids:
                        profile = profile_builder.add_skills(profile, category, skill_ids)
                        print(f"  ✓ Added {len(skill_ids)} skills")
                except (ValueError, IndexError):
                    print("  Invalid selection, skipping")
    
    # Save profile
    saved_path = profile_mgr.save(profile_name, profile)
    print(f"\n✓ Profile saved: {saved_path}")
    
    # Show preview
    print("\n" + "="*60)
    print(profile_builder.preview_selection(profile))
    print("="*60)
    
    print(f"\nTo generate resume with this profile:")
    print(f"  python -m builder new --profile {profile_name} --layout <layout> --theme <theme>")


def cmd_validate(args, builder: ResumeBuilder):
    """Validate resume constraints"""
    if args.file:
        # Validate existing PDF
        pdf_path = Path(args.file)
        if not pdf_path.exists():
            print(f"❌ File not found: {pdf_path}")
            sys.exit(1)
        
        print(f"Validating: {pdf_path}")
        result = builder.validator.validate_actual_pages(pdf_path)
        print(result.format())
    
    elif args.profile:
        # Validate profile without generating
        profile_mgr = ProfileManager(builder.profiles_dir)
        profile = profile_mgr.load(args.profile)
        
        if not profile:
            print(f"❌ Profile not found: {args.profile}")
            sys.exit(1)
        
        print(f"Validating profile: {args.profile}")
        
        # Build content structure for validation
        temp_builder = ResumeBuilder(profile=args.profile)
        theme_config = temp_builder.themes.get(args.theme or "ml", {})
        
        selected_exp = temp_builder.select_experiences(theme_config)
        selected_proj = temp_builder.select_projects(theme_config)
        
        content = {
            "experiences": selected_exp,
            "projects": selected_proj,
            "skills": profile.get("skills", {}),
            "education": list(temp_builder.education.values())
        }
        
        result = temp_builder.validator.validate_full(content)
        print(result.format())
        
        if result.errors:
            suggestions = temp_builder.validator.suggest_reductions(content)
            if suggestions:
                print("\n💡 Suggestions to reduce content:")
                for suggestion in suggestions:
                    print(f"  • {suggestion}")
    
    else:
        print("Usage: validate --file <pdf> OR --profile <name>")
        sys.exit(1)


def cmd_measure(args, builder: ResumeBuilder):
    """Show space measurements and cache stats"""
    print("\n=== Space Measurement Report ===\n")
    
    # Cache stats
    cache_stats = builder.cache.stats()
    print(f"Cache: {cache_stats['total_entries']} entries")
    print(f"       {cache_stats['size_bytes']} bytes\n")
    
    # Show measurement estimates for all content
    print("--- Experiences ---")
    for exp_id, exp_data in builder.experiences.items():
        base = exp_data.get("base", {})
        bullets = exp_data.get("bullets", [])
        
        mock_exp = {
            "title": base.get("title", ""),
            "bullets": [b["text"] for b in bullets]
        }
        height = builder.metrics.estimate_experience_height(mock_exp)
        
        print(f"  {base.get('title', exp_id)[:40]:40s} {height:6.1f}pts  ({len(bullets)} bullets)")
    
    print("\n--- Projects ---")
    for proj_id, proj_data in builder.projects.items():
        base = proj_data.get("base", {})
        bullets = proj_data.get("bullets", [])
        
        mock_proj = {
            "title": base.get("title", ""),
            "bullets": [b["text"] for b in bullets]
        }
        height = builder.metrics.estimate_project_height(mock_proj)
        
        print(f"  {base.get('title', proj_id)[:40]:40s} {height:6.1f}pts  ({len(bullets)} bullets)")
    
    print("\n--- Skills ---")
    num_skill_lines = len(builder.skills)
    skills_height = builder.metrics.estimate_skills_height(num_skill_lines)
    print(f"  Skills section ({num_skill_lines} lines): {skills_height:.1f}pts")
    
    print("\n--- Page Capacity ---")
    print(f"  Usable page height: {builder.metrics.PAGE_HEIGHT}pts (~10 inches)")
    print(f"  Average experience: ~60-80pts")
    print(f"  Average project: ~40-60pts")
    print()


def cmd_lock(args, builder: ResumeBuilder):
    """Lock temp file as final application"""
    company = args.company
    temp_file = args.file
    
    if temp_file:
        tex_path = builder.temp_dir / temp_file
        if not tex_path.exists():
            tex_path = Path(temp_file)
    else:
        tex_path = builder.get_latest_temp(company)
    
    if not tex_path or not tex_path.exists():
        print(f"No temp file found for '{company}'")
        print("Run: make new LAYOUT=... THEME=... COMPANY=...")
        sys.exit(1)
    
    print(f"\nLocking: {tex_path}")
    print(f"Company: {company}")
    
    final_tex, final_pdf = builder.lock(tex_path, company)
    
    print(f"\n✓ Locked!")
    print(f"  LaTeX: {final_tex}")
    print(f"  PDF: {final_pdf}")
    print(f"  Dir: {final_tex.parent}")


def cmd_show_temp(args, builder: ResumeBuilder):
    """Show temp files"""
    temps = sorted(builder.temp_dir.glob("*.tex"), key=lambda p: p.stat().st_mtime, reverse=True)
    
    if not temps:
        print("No temp files found.")
        return
    
    print("\n=== Temp Files ===")
    for t in temps[:10]:
        pdf = t.with_suffix(".pdf")
        pdf_status = "✓" if pdf.exists() else "✗"
        print(f"  {pdf_status} {t.name}")
    print()


def cmd_show_apps(args, builder: ResumeBuilder):
    """Show locked applications"""
    apps = list(builder.apps_dir.glob("*/*.pdf"))
    
    if not apps:
        print("No locked applications found.")
        return
    
    print("\n=== Locked Applications ===")
    for app in sorted(apps):
        company = app.parent.name
        print(f"  {company}: {app}")
    print()


def cmd_clean_temp(args, builder: ResumeBuilder):
    """Clean temp files"""
    import shutil
    count = 0
    for f in builder.temp_dir.glob("*"):
        f.unlink()
        count += 1
    print(f"Cleaned {count} temp files.")


def main():
    parser = argparse.ArgumentParser(
        description="Resume Builder CLI",
        epilog="Use 'python -m builder <command> --help' for command-specific help"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # list
    subparsers.add_parser("list", help="List layouts, themes, and profiles")
    
    # new
    p_new = subparsers.add_parser("new", help="Generate new resume")
    p_new.add_argument("--layout", "-l", required=True, help="Layout name")
    p_new.add_argument("--theme", "-t", required=True, help="Theme name")
    p_new.add_argument("--company", "-c", help="Company name (optional)")
    p_new.add_argument("--profile", "-p", help="Profile name (overrides theme auto-selection)")
    
    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Analyze theme selection")
    p_analyze.add_argument("theme", help="Theme to analyze")
    
    # edit-profile
    p_edit = subparsers.add_parser("edit-profile", help="Create or edit selection profile")
    p_edit.add_argument("name", help="Profile name")
    p_edit.add_argument("--description", "-d", help="Profile description")
    p_edit.add_argument("--skip-experiences", action="store_true", help="Skip experience selection")
    p_edit.add_argument("--skip-skills", action="store_true", help="Skip skill selection")
    
    # validate
    p_validate = subparsers.add_parser("validate", help="Validate resume constraints")
    p_validate.add_argument("--file", "-f", help="PDF file to validate")
    p_validate.add_argument("--profile", "-p", help="Profile to validate (without generating)")
    p_validate.add_argument("--theme", "-t", help="Theme to use with profile (default: ml)")
    
    # measure
    subparsers.add_parser("measure", help="Show space measurements and cache stats")
    
    # lock
    p_lock = subparsers.add_parser("lock", help="Lock temp file as application")
    p_lock.add_argument("company", help="Company name")
    p_lock.add_argument("--file", "-f", help="Specific temp file (optional)")
    
    # show-temp
    subparsers.add_parser("show-temp", help="Show temp files")
    
    # show-apps
    subparsers.add_parser("show-apps", help="Show locked applications")
    
    # clean-temp
    subparsers.add_parser("clean-temp", help="Clean temp files")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    builder = ResumeBuilder()
    
    commands = {
        "list": cmd_list,
        "new": cmd_new,
        "analyze": cmd_analyze,
        "edit-profile": cmd_edit_profile,
        "validate": cmd_validate,
        "measure": cmd_measure,
        "lock": cmd_lock,
        "show-temp": cmd_show_temp,
        "show-apps": cmd_show_apps,
        "clean-temp": cmd_clean_temp,
    }
    
    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args, builder)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
