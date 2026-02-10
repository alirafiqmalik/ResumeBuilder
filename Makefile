# Makefile for Modular Resume System (WSL/Linux)
# YAML-Driven Resume Builder with Python Backend
# Usage: make [target]

# ============================================================================
# CONFIGURATION
# ============================================================================

PYTHON = python3
CLI_MODULE = -m builder

# Directories
TEMP_DIR = temp
APPS_DIR = Application

# ============================================================================
# WORKFLOW
# ============================================================================

.PHONY: new list analyze lock edit rebuild preview show-temp show-apps clean-temp clean distclean help
.PHONY: profile edit-profile validate measure

# Generate new resume: make new LAYOUT=skill_first THEME=ml [COMPANY=Databricks] [PROFILE=profile_name]
new:
	@if [ -z "$(LAYOUT)" ] || [ -z "$(THEME)" ]; then \
		echo "Usage: make new LAYOUT=<layout> THEME=<theme> [COMPANY=<name>] [PROFILE=<profile>]"; \
		echo ""; \
		echo "Run 'make list' to see available layouts, themes, and profiles"; \
		exit 1; \
	fi
	@if [ -n "$(PROFILE)" ]; then \
		if [ -n "$(COMPANY)" ]; then \
			$(PYTHON) $(CLI_MODULE) new --layout $(LAYOUT) --theme $(THEME) --company "$(COMPANY)" --profile $(PROFILE); \
		else \
			$(PYTHON) $(CLI_MODULE) new --layout $(LAYOUT) --theme $(THEME) --profile $(PROFILE); \
		fi \
	else \
		if [ -n "$(COMPANY)" ]; then \
			$(PYTHON) $(CLI_MODULE) new --layout $(LAYOUT) --theme $(THEME) --company "$(COMPANY)"; \
		else \
			$(PYTHON) $(CLI_MODULE) new --layout $(LAYOUT) --theme $(THEME); \
		fi \
	fi

# List available layouts, themes, and profiles
list:
	@$(PYTHON) $(CLI_MODULE) list

# Analyze what content will be selected for a theme
# Usage: make analyze THEME=ml
analyze:
	@if [ -z "$(THEME)" ]; then \
		echo "Usage: make analyze THEME=<theme>"; \
		exit 1; \
	fi
	@$(PYTHON) $(CLI_MODULE) analyze $(THEME)

# Create or edit a profile
# Usage: make edit-profile PROFILE=ml_focused [DESCRIPTION="ML and AI roles"]
edit-profile: profile
profile:
	@if [ -z "$(PROFILE)" ]; then \
		echo "Usage: make edit-profile PROFILE=<name> [DESCRIPTION=\"...\"]"; \
		echo ""; \
		echo "This will launch an interactive profile editor."; \
		exit 1; \
	fi
	@if [ -n "$(DESCRIPTION)" ]; then \
		$(PYTHON) $(CLI_MODULE) edit-profile $(PROFILE) --description "$(DESCRIPTION)"; \
	else \
		$(PYTHON) $(CLI_MODULE) edit-profile $(PROFILE); \
	fi

# Validate resume constraints
# Usage: make validate FILE=temp/Resume.pdf  OR  make validate PROFILE=ml_focused
validate:
	@if [ -n "$(FILE)" ]; then \
		$(PYTHON) $(CLI_MODULE) validate --file "$(FILE)"; \
	elif [ -n "$(PROFILE)" ]; then \
		$(PYTHON) $(CLI_MODULE) validate --profile $(PROFILE) --theme $(THEME); \
	else \
		LATEST=$$(ls -t $(TEMP_DIR)/*.pdf 2>/dev/null | head -1); \
		if [ -z "$$LATEST" ]; then \
			echo "Usage: make validate FILE=<pdf> OR make validate PROFILE=<name>"; \
			exit 1; \
		fi; \
		echo "Validating latest PDF: $$LATEST"; \
		$(PYTHON) $(CLI_MODULE) validate --file "$$LATEST"; \
	fi

# Show space measurements
measure:
	@$(PYTHON) $(CLI_MODULE) measure

# Lock temp file as final application
# Usage: make lock COMPANY=Databricks [FILE=specific_file.tex]
lock:
	@if [ -z "$(COMPANY)" ]; then \
		echo "Usage: make lock COMPANY=<name> [FILE=<temp_file.tex>]"; \
		exit 1; \
	fi
	@if [ -n "$(FILE)" ]; then \
		$(PYTHON) $(CLI_MODULE) lock "$(COMPANY)" --file "$(FILE)"; \
	else \
		$(PYTHON) $(CLI_MODULE) lock "$(COMPANY)"; \
	fi

# Edit most recent temp file in VS Code
# Usage: make edit [COMPANY=Databricks]
edit:
	@if [ -n "$(COMPANY)" ]; then \
		LATEST=$$(ls -t $(TEMP_DIR)/$(COMPANY)*.tex 2>/dev/null | head -1); \
	else \
		LATEST=$$(ls -t $(TEMP_DIR)/*.tex 2>/dev/null | head -1); \
	fi; \
	if [ -z "$$LATEST" ]; then \
		echo "No temp file found"; \
		exit 1; \
	fi; \
	echo "Opening in VS Code: $$LATEST"; \
	code "$$LATEST"

# Rebuild/recompile most recent temp file to update PDF
# Usage: make rebuild [COMPANY=Databricks]
rebuild:
	@if [ -n "$(COMPANY)" ]; then \
		LATEST=$$(ls -t $(TEMP_DIR)/$(COMPANY)*.tex 2>/dev/null | head -1); \
	else \
		LATEST=$$(ls -t $(TEMP_DIR)/*.tex 2>/dev/null | head -1); \
	fi; \
	if [ -z "$$LATEST" ]; then \
		echo "No temp file found"; \
		exit 1; \
	fi; \
	echo "Recompiling: $$LATEST"; \
	pdflatex -interaction=nonstopmode -output-directory=$(TEMP_DIR) "$$LATEST" > /dev/null; \
	rm -f $(TEMP_DIR)/*.aux $(TEMP_DIR)/*.log $(TEMP_DIR)/*.out; \
	echo "PDF updated"

# Preview most recent temp PDF
# Usage: make preview [COMPANY=Databricks]
preview:
	@if [ -n "$(COMPANY)" ]; then \
		LATEST=$$(ls -t $(TEMP_DIR)/$(COMPANY)*.pdf 2>/dev/null | head -1); \
	else \
		LATEST=$$(ls -t $(TEMP_DIR)/*.pdf 2>/dev/null | head -1); \
	fi; \
	if [ -z "$$LATEST" ]; then \
		echo "No PDF found"; \
		exit 1; \
	fi; \
	echo "Opening: $$LATEST"; \
	xdg-open "$$LATEST" 2>/dev/null || open "$$LATEST"

# Show temp files
show-temp:
	@$(PYTHON) $(CLI_MODULE) show-temp

# Show locked applications
show-apps:
	@$(PYTHON) $(CLI_MODULE) show-apps

# Clean temp directory
clean-temp:
	@$(PYTHON) $(CLI_MODULE) clean-temp

# ============================================================================
# MAINTENANCE
# ============================================================================

clean:
	@echo "Cleaning auxiliary files..."
	@rm -f $(TEMP_DIR)/*.aux $(TEMP_DIR)/*.log $(TEMP_DIR)/*.out
	@echo "Clean complete."

distclean: clean
	@rm -rf $(TEMP_DIR)/*
	@echo "Full clean complete."

# ============================================================================
# HELP
# ============================================================================

help:
	@echo "Modular Resume System - YAML-Driven Builder with Profiles"
	@echo "=========================================================="
	@echo ""
	@echo "WORKFLOW:"
	@echo "  make list                              - Show layouts, themes & profiles"
	@echo "  make new LAYOUT=skill_first THEME=ml   - Generate temp resume"
	@echo "  make new LAYOUT=skill_first THEME=ml COMPANY=Databricks"
	@echo "  make new LAYOUT=skill_first THEME=ml PROFILE=ml_focused"
	@echo "  make analyze THEME=ml                  - Preview content selection"
	@echo "  make preview                           - Open latest PDF"
	@echo "  make edit                              - Edit in VS Code"
	@echo "  make rebuild                           - Recompile after edits"
	@echo "  make lock COMPANY=Databricks           - Lock as final version"
	@echo ""
	@echo "PROFILES (Content Selection):"
	@echo "  make edit-profile PROFILE=ml_focused   - Create/edit profile interactively"
	@echo "  make validate PROFILE=ml_focused       - Validate profile (pre-generation)"
	@echo "  make validate FILE=temp/Resume.pdf     - Validate PDF (post-generation)"
	@echo "  make measure                           - Show space measurements"
	@echo ""
	@echo "EXAMPLE WITH PROFILE:"
	@echo "  1. make edit-profile PROFILE=my_profile  # Select experiences/skills"
	@echo "  2. make validate PROFILE=my_profile      # Check constraints"
	@echo "  3. make new LAYOUT=skill_first THEME=ml PROFILE=my_profile COMPANY=Acme"
	@echo "  4. make validate                         # Validate generated PDF"
	@echo "  5. make lock COMPANY=Acme                # Lock final version"
	@echo ""
	@echo "EXAMPLE WITHOUT PROFILE (Auto-selection):"
	@echo "  1. make new LAYOUT=skill_first THEME=ml COMPANY=Databricks"
	@echo "  2. make preview                    # Review PDF"
	@echo "  3. make edit                       # Edit in VS Code"
	@echo "  4. make rebuild                    # Recompile to see changes"
	@echo "  5. make lock COMPANY=Databricks   # Lock final version"
	@echo ""
	@echo "LAYOUTS:"
	@echo "  skill_first      - Skills prominent (technical roles)"
	@echo "  experience_first - Experience prominent (industry)"
	@echo "  academic         - Education first (research/PhD)"
	@echo "  streamlined      - One-page focused"
	@echo "  fullversion      - Comprehensive"
	@echo ""
	@echo "THEMES:"
	@echo "  ml, formal, systems, hardware, llm, cloud, fullstack,"
	@echo "  robotics, default"
	@echo ""
	@echo "FILE MANAGEMENT:"
	@echo "  make show-temp    - List temp files"
	@echo "  make show-apps    - List locked applications"
	@echo "  make clean-temp   - Clear temp directory"
	@echo ""
	@echo "MAINTENANCE:"
	@echo "  make clean        - Remove auxiliary files"
	@echo "  make distclean    - Full clean including temp"
	@echo ""
	@echo "DIRECT CLI:"
	@echo "  python -m builder <command> --help  - See all CLI options"
