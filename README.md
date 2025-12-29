# Modular Resume System

YAML-driven resume builder with intelligent content selection for different job types.

## Quick Start

```bash
# List available layouts and themes
make list

# Generate a new resume
make new LAYOUT=skill_first THEME=ml COMPANY=Databricks

# Preview, edit, rebuild cycle
make preview          # View PDF
make edit             # Open in VS Code
make rebuild          # Recompile after edits

# Lock final version
make lock COMPANY=Databricks
```

## Workflow

```
1. make new LAYOUT=... THEME=... COMPANY=...   → temp/<Company>_<timestamp>.tex
2. make preview                                 → View PDF
3. make edit                                    → Edit in VS Code
4. make rebuild                                 → Recompile PDF
5. (repeat 3-4 until satisfied)
6. make lock COMPANY=...                        → Application/<Company>/
```

## Layouts

Control section order:

| Layout | Description |
|--------|-------------|
| `skill_first` | Skills prominent (technical roles) |
| `experience_first` | Experience prominent (industry) |
| `academic` | Education first (research/PhD positions) |
| `streamlined` | One-page focused |
| `fullversion` | Comprehensive, all sections |

## Themes

Control content selection (which bullets, skills, projects appear):

| Theme | Focus |
|-------|-------|
| `ml` | Machine Learning & AI |
| `formal` | Formal Methods & Verification |
| `systems` | Systems & Embedded |
| `hardware` | Hardware Security |
| `llm` | LLM & AI Agents |
| `cloud` | Cloud & DevOps |
| `fullstack` | Full-Stack Development |
| `robotics` | Robotics & Perception |
| `default` | Comprehensive |

## Project Structure

```
AutoResume/
├── Makefile              # CLI interface
├── main.tex              # Base LaTeX structure
├── builder/
│   ├── cli.py            # Command-line interface
│   └── core.py           # Resume generation logic
├── content/              # YAML content (edit these!)
│   ├── experiences.yaml  # Work experience with tagged bullets
│   ├── education.yaml    # Education entries
│   ├── projects.yaml     # Project entries with tagged bullets
│   └── skills.yaml       # Skills with themed versions
├── config/               # Configuration
│   ├── layouts.yaml      # Section order definitions
│   └── themes.yaml       # Content selection rules
├── resume_components/    # LaTeX component templates
│   ├── core/             # Header, preamble
│   ├── education/        # Education template
│   ├── experience/       # Experience templates
│   ├── skills/           # Skills templates
│   ├── projects/         # Projects template
│   └── extras/           # Honors, interests
├── temp/                 # Generated temp files
└── Application/          # Locked final versions
```

## Content Files

### experiences.yaml

```yaml
experiences:
  grad_research:
    base:
      title: "Graduate Research Assistant"
      organization: "University Lab"
      dates: "2022 - Present"
    bullets:
      - id: ml_training
        text: "Developed ML training pipeline..."
        tags: [ml, systems, cloud]
      - id: formal_verification
        text: "Applied formal methods..."
        tags: [formal, systems]
```

### skills.yaml

```yaml
skills:
  programming:
    category: "Languages"
    default: "Python, C++, Java, JavaScript"
    versions:
      ml: "Python, C++, CUDA, Julia"
      formal: "Python, Coq, Isabelle, OCaml"
```

### themes.yaml

```yaml
themes:
  ml:
    description: "Machine Learning focus"
    experience_tags: [ml, data, research]
    project_tags: [ml, ai, deep-learning]
    skills: [programming, ml, tools]
```

## Commands

| Command | Description |
|---------|-------------|
| `make list` | Show available layouts and themes |
| `make new LAYOUT=... THEME=...` | Generate temp resume |
| `make analyze THEME=...` | Preview content selection |
| `make preview` | Open latest PDF |
| `make edit` | Edit latest temp file in VS Code |
| `make rebuild` | Recompile after edits |
| `make lock COMPANY=...` | Lock as final version |
| `make show-temp` | List temp files |
| `make show-apps` | List locked applications |
| `make clean-temp` | Clear temp directory |

## Adding Content

1. **New experience bullet**: Add to `content/experiences.yaml` with appropriate tags
2. **New skill version**: Add to `content/skills.yaml` under the relevant theme
3. **New project**: Add to `content/projects.yaml` with tags
4. **New theme**: Add to `config/themes.yaml` with tag preferences

## Requirements

- Python 3 with PyYAML
- pdflatex (TeX Live or MiKTeX)
- VS Code (for `make edit`)
