# Makefile for Modular Resume System (WSL/Linux)
# YAML-Driven Resume Builder with Python Backend
# Usage: make [target]

# ============================================================================
# CONFIGURATION
# ============================================================================

PYTHON = python3
CLI = builder/cli.py

# Directories
TEMP_DIR = temp
APPS_DIR = Application

# ============================================================================
# WORKFLOW
# ============================================================================

.PHONY: new list analyze lock edit rebuild preview show-temp show-apps clean-temp clean distclean help

# Generate new resume: make new LAYOUT=skill_first THEME=ml [COMPANY=Databricks]
new:
	@if [ -z "$(LAYOUT)" ] || [ -z "$(THEME)" ]; then \
		echo "Usage: make new LAYOUT=<layout> THEME=<theme> [COMPANY=<name>]"; \
		echo ""; \
		echo "Run 'make list' to see available layouts and themes"; \
		exit 1; \
	fi
	@if [ -n "$(COMPANY)" ]; then \
		$(PYTHON) $(CLI) new --layout $(LAYOUT) --theme $(THEME) --company "$(COMPANY)"; \
	else \
		$(PYTHON) $(CLI) new --layout $(LAYOUT) --theme $(THEME); \
	fi

# List available layouts and themes
list:
	@$(PYTHON) $(CLI) list

# Analyze what content will be selected for a theme
# Usage: make analyze THEME=ml
analyze:
	@if [ -z "$(THEME)" ]; then \
		echo "Usage: make analyze THEME=<theme>"; \
		exit 1; \
	fi
	@$(PYTHON) $(CLI) analyze $(THEME)

# Lock temp file as final application
# Usage: make lock COMPANY=Databricks [FILE=specific_file.tex]
lock:
	@if [ -z "$(COMPANY)" ]; then \
		echo "Usage: make lock COMPANY=<name> [FILE=<temp_file.tex>]"; \
		exit 1; \
	fi
	@if [ -n "$(FILE)" ]; then \
		$(PYTHON) $(CLI) lock "$(COMPANY)" --file "$(FILE)"; \
	else \
		$(PYTHON) $(CLI) lock "$(COMPANY)"; \
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
	@$(PYTHON) $(CLI) show-temp

# Show locked applications
show-apps:
	@$(PYTHON) $(CLI) show-apps

# Clean temp directory
clean-temp:
	@$(PYTHON) $(CLI) clean-temp

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
	@echo "Modular Resume System - YAML-Driven Builder"
	@echo "============================================"
	@echo ""
	@echo "WORKFLOW:"
	@echo "  make list                              - Show layouts & themes"
	@echo "  make new LAYOUT=skill_first THEME=ml   - Generate temp resume"
	@echo "  make new LAYOUT=skill_first THEME=ml COMPANY=Databricks"
	@echo "  make analyze THEME=ml                  - Preview content selection"
	@echo "  make preview                           - Open latest PDF"
	@echo "  make edit                              - Edit in VS Code"
	@echo "  make rebuild                           - Recompile after edits"
	@echo "  make lock COMPANY=Databricks           - Lock as final version"
	@echo ""
	@echo "EXAMPLE:"
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
