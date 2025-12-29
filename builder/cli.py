#!/usr/bin/env python3
"""
Resume Builder CLI
Usage: python builder/cli.py [command] [options]
"""
import sys
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from core import ResumeBuilder


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
    print()


def cmd_new(args, builder: ResumeBuilder):
    """Generate new resume from layout + theme"""
    layout = args.layout
    theme = args.theme
    company = args.company
    
    print(f"\nGenerating resume: layout={layout}, theme={theme}")
    if company:
        print(f"  Company: {company}")
    
    try:
        tex_file = builder.generate(layout, theme, company)
        print(f"\n✓ Generated: {tex_file}")
        
        pdf_file = builder.compile_pdf(tex_file)
        if pdf_file:
            print(f"✓ Compiled: {pdf_file}")
        else:
            print("✗ PDF compilation failed - check LaTeX errors")
        
        print(f"\nNext steps:")
        print(f"  1. Review PDF: xdg-open {pdf_file}")
        print(f"  2. Edit if needed: nano {tex_file}")
        name = company or f"{layout}_{theme}"
        print(f"  3. Lock: make lock COMPANY={name}")
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
            print(f"    {i}. {bullet[:80]}...")
    
    print("\n--- Selected Projects ---")
    selected_proj = builder.select_projects(theme_config)
    for proj in selected_proj:
        print(f"\n  {proj['title']}")
        for i, bullet in enumerate(proj['bullets'], 1):
            print(f"    {i}. {bullet[:80]}...")
    
    print("\n--- Skills ---")
    for skill_id in theme_config.get("skills", []):
        line = builder.get_skill_line(skill_id, theme_name)
        print(f"  {line[:100]}...")
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
    parser = argparse.ArgumentParser(description="Resume Builder CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # list
    subparsers.add_parser("list", help="List layouts and themes")
    
    # new
    p_new = subparsers.add_parser("new", help="Generate new resume")
    p_new.add_argument("--layout", "-l", required=True, help="Layout name")
    p_new.add_argument("--theme", "-t", required=True, help="Theme name")
    p_new.add_argument("--company", "-c", help="Company name (optional)")
    
    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Analyze theme selection")
    p_analyze.add_argument("theme", help="Theme to analyze")
    
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
