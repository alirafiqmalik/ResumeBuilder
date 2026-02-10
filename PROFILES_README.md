# Resume Builder - Profile System & Space Validation

## Overview

This resume builder now supports **profile-based content selection** and **automatic page validation** to help create targeted, one-page resumes.

### Key Features

- ✅ **Profile System**: Create reusable selection profiles with fine-grained bullet-point control
- ✅ **Interactive CLI Editor**: Build profiles through guided command-line interface
- ✅ **Space Estimation**: Predict page usage before generation
- ✅ **Automatic Validation**: Check PDF page count after compilation
- ✅ **Measurement Cache**: Learn from actual compilations to improve estimates
- ✅ **Constraint Checking**: Validate bullet length and content density

## Quick Start

### Traditional Workflow (Auto-Selection)

```bash
# Generate resume with theme-based auto-selection
make new LAYOUT=skill_first THEME=ml COMPANY=Databricks

# View and validate
make preview
make validate
```

### Profile Workflow (Manual Selection)

```bash
# 1. Create a profile interactively
make edit-profile PROFILE=my_ml_resume

# 2. Validate profile before generating
make validate PROFILE=my_ml_resume THEME=ml

# 3. Generate resume with profile
make new LAYOUT=skill_first THEME=ml PROFILE=my_ml_resume COMPANY=Databricks

# 4. Validate generated PDF
make validate
```

## Commands

### Profile Management

```bash
# Create/edit profile interactively
make edit-profile PROFILE=ml_focused

# Or use Python directly
python -m builder edit-profile ml_focused --description "ML and AI roles"
```

### Generation with Profiles

```bash
# Generate with profile (overrides theme auto-selection)
make new LAYOUT=skill_first THEME=ml PROFILE=ml_focused COMPANY=Acme

# Generate without profile (uses theme auto-selection)
make new LAYOUT=skill_first THEME=ml COMPANY=Acme
```

### Validation

```bash
# Validate latest PDF
make validate

# Validate specific file
make validate FILE=temp/Resume_20260210_123456.pdf

# Validate profile without generating
make validate PROFILE=ml_focused THEME=ml
```

### Measurement & Analysis

```bash
# Show space measurements for all content
make measure

# Analyze what theme will select
make analyze THEME=ml

# List everything (layouts, themes, profiles)
make list
```

## Profile Structure

Profiles are YAML files in `config/profiles/` that specify exactly which experiences, skills, and bullets to include:

```yaml
name: ml_focused
description: "Machine Learning and AI roles"
inherit_from: ml  # Optional: use theme as base

experiences:
  grad_research:
    - gr_1  # Select specific bullets by ID
    - gr_2
  ml_intern:
    - ml_1
    - ml_2

skills:
  Programming Languages:
    - skills_programming
  DS/ML/AI:
    - skills_ml
  LLM & Agents:
    - skills_llm

created_at: "2026-02-10T00:00:00"
updated_at: "2026-02-10T00:00:00"
```

### Example Profiles

- **ml_focused.yaml**: ML and AI roles - emphasizes ML skills and experience
- **security_focused.yaml**: Security and formal methods - verification work
- **minimal.yaml**: Minimal 1-page resume - carefully selected key experiences

## Space Validation System

### How It Works

1. **Heuristic Estimation**: Fast character-count based prediction (before generation)
2. **Actual Measurement**: PDF page counting post-compilation
3. **Cached Learning**: System remembers actual measurements to improve future estimates
4. **Constraint Checking**: Validates bullets don't exceed 2 lines, total content fits 1 page

### Validation Output

```
✓ All constraints satisfied

⚠️  WARNINGS:
  • Bullet 3: Bullet too long (2.5 lines, ~50 chars over 2-line limit)

ℹ️  INFO:
  • Estimated pages: 0.95
  • Actual pages: 1
  • ✓ Resume fits on 1 page
```

## CLI Interface

All commands are available via `python -m builder`:

```bash
# List everything
python -m builder list

# Generate resume
python -m builder new --layout skill_first --theme ml --company Databricks

# Generate with profile
python -m builder new --layout skill_first --theme ml --profile ml_focused --company Databricks

# Create/edit profile
python -m builder edit-profile my_profile --description "Custom selection"

# Validate
python -m builder validate --file temp/Resume.pdf
python -m builder validate --profile ml_focused --theme ml

# Measure space usage
python -m builder measure

# Analyze theme
python -m builder analyze ml

# Lock application
python -m builder lock Databricks

# Show files
python -m builder show-temp
python -m builder show-apps

# Clean
python -m builder clean-temp
```

## Architecture

### Modules

- **builder/core.py**: Resume generation engine with profile support
- **builder/profiles.py**: ProfileManager and ProfileBuilder for CRUD and interactive editing
- **builder/metrics.py**: SpaceEstimator with heuristic and actual measurements
- **builder/cache.py**: MeasurementCache for persistent storage
- **builder/validator.py**: ConstraintChecker for validation logic
- **builder/cli.py**: Command-line interface
- **builder/__main__.py**: Entry point for `python -m builder`

### Profile System Flow

```
User → CLI Editor → ProfileBuilder → Profile YAML
                                          ↓
                                     ProfileManager → Save to config/profiles/
                                          ↓
ResumeBuilder (with profile) → Core → LaTeX Generation
                                          ↓
                                     PDF Compilation
                                          ↓
                                  Validator → Metrics → Cache
```

## Benefits

### For Users

- **Fine-Grained Control**: Select individual bullet points, not just entire experiences
- **Reusable Profiles**: Create once, use for multiple similar job applications
- **Pre-Validation**: Know if content fits before generating PDF
- **Post-Validation**: Automatic warnings if resume exceeds 1 page
- **Guided Workflow**: Interactive editor prevents syntax errors

### For Automation

- **Programmatic API**: Import `builder` package in other Python scripts
- **Clean Interfaces**: ProfileManager, SpaceEstimator, Validator classes
- **Extensible**: Easy to add new constraint types or measurement strategies
- **Cached Data**: Measurements persist across runs for faster estimates

## Migration from Old System

Old resumes still work! The system is backward compatible:

```bash
# Old way (still works)
make new LAYOUT=skill_first THEME=ml COMPANY=Databricks

# New way (with profile)
make new LAYOUT=skill_first THEME=ml PROFILE=ml_focused COMPANY=Databricks
```

If you don't specify a profile, the system uses theme-based auto-selection (original behavior).

## Tips

1. **Start with a theme analysis**: `make analyze THEME=ml` shows what would be auto-selected
2. **Create profile from analysis**: Use interactive editor to customize selections
3. **Validate early**: Check profile constraints before generating PDF
4. **Iterate**: Validation warnings help you adjust content to fit 1 page
5. **Reuse profiles**: Save profiles for similar roles (e.g., all ML positions)

## Future Enhancements

Potential additions:
- GUI profile editor
- More sophisticated space models (font-aware, LaTeX template-aware)
- Auto-suggest profile modifications when validation fails
- Profile inheritance and composition
- Version control integration for profiles
- A/B testing different profile versions

## License

[Same as parent project]
