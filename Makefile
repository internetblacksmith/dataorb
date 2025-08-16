# Pi Analytics Dashboard Development Makefile
# Run 'make' without arguments for interactive menu

.PHONY: help menu dev dev-python dev-bash stop build test quality docs install clean update format lint deploy

# Default target - show interactive menu
.DEFAULT_GOAL := menu

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
WHITE := \033[1;37m
NC := \033[0m # No Color

# Project directories
BACKEND_DIR := backend
FRONTEND_DIR := frontend
DOCS_DIR := docs
SCRIPTS_DIR := scripts

#==============================================================================
# Interactive Menu
#==============================================================================

menu:
	@echo -e "$(BLUE)╔══════════════════════════════════════════════════════════════╗$(NC)"
	@echo -e "$(BLUE)║$(WHITE)           Pi Analytics Dashboard Development Menu            $(BLUE)║$(NC)"
	@echo -e "$(BLUE)╠══════════════════════════════════════════════════════════════╣$(NC)"
	@echo -e "$(BLUE)║$(NC) $(CYAN)Development:$(NC)                                               $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)   $(GREEN)1)$(NC) Start development servers (Frontend + Backend)        $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)   $(GREEN)2)$(NC) Build production version                              $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)   $(GREEN)3)$(NC) Run production server                                 $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)                                                             $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC) $(CYAN)Quality & Testing:$(NC)                                         $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)   $(GREEN)4)$(NC) Run all quality checks                                $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)   $(GREEN)5)$(NC) Run tests only                                        $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)   $(GREEN)6)$(NC) Format code (Black + Prettier)                        $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)   $(GREEN)7)$(NC) Run linting checks                                    $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)                                                             $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC) $(CYAN)Documentation:$(NC)                                             $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)   $(GREEN)8)$(NC) Start documentation server                            $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)   $(GREEN)9)$(NC) Check documentation quality                           $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)   $(GREEN)10)$(NC) Sync documentation to Docsify                        $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)                                                             $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC) $(CYAN)Installation & Setup:$(NC)                                      $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)   $(GREEN)11)$(NC) Install all dependencies                             $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)   $(GREEN)12)$(NC) Install pre-commit hooks                             $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)   $(GREEN)13)$(NC) Clean build artifacts                                $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)                                                             $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC) $(CYAN)Deployment:$(NC)                                                $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)   $(GREEN)14)$(NC) Deploy to Raspberry Pi                               $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)   $(GREEN)15)$(NC) Check for updates                                    $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)                                                             $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)   $(RED)q)$(NC) Quit                                                  $(BLUE)║$(NC)"
	@echo -e "$(BLUE)╚══════════════════════════════════════════════════════════════╝$(NC)"
	@echo -e ""
	@printf "$(YELLOW)Select an option: $(NC)"; \
	read choice; \
	case $$choice in \
		1) $(MAKE) dev ;; \
		2) $(MAKE) build ;; \
		3) $(MAKE) run ;; \
		4) $(MAKE) quality ;; \
		5) $(MAKE) test ;; \
		6) $(MAKE) format ;; \
		7) $(MAKE) lint ;; \
		8) $(MAKE) docs ;; \
		9) $(MAKE) check-docs ;; \
		10) $(MAKE) sync-docs ;; \
		11) $(MAKE) install ;; \
		12) $(MAKE) install-hooks ;; \
		13) $(MAKE) clean ;; \
		14) $(MAKE) deploy ;; \
		15) $(MAKE) check-updates ;; \
		q|Q) echo "$(GREEN)Goodbye!$(NC)" ;; \
		*) echo "$(RED)Invalid option!$(NC)" && $(MAKE) menu ;; \
	esac

#==============================================================================
# Help Target
#==============================================================================

help:
	@echo -e "$(BLUE)Pi Analytics Dashboard Development Commands$(NC)"
	@echo -e ""
	@echo -e "$(CYAN)Development:$(NC)"
	@echo -e "  $(GREEN)make dev$(NC)          - Start development servers (Frontend + Backend)"
	@echo -e "  $(GREEN)make stop$(NC)         - Stop all development servers"
	@echo -e "  $(GREEN)make build$(NC)        - Build production version"
	@echo -e "  $(GREEN)make run$(NC)          - Run production server"
	@echo -e ""
	@echo -e "$(CYAN)Quality & Testing:$(NC)"
	@echo -e "  $(GREEN)make quality$(NC)      - Run all quality checks"
	@echo -e "  $(GREEN)make test$(NC)         - Run all tests"
	@echo -e "  $(GREEN)make format$(NC)       - Format all code"
	@echo -e "  $(GREEN)make lint$(NC)         - Run linting checks"
	@echo -e ""
	@echo -e "$(CYAN)Documentation:$(NC)"
	@echo -e "  $(GREEN)make docs$(NC)         - Start documentation server"
	@echo -e "  $(GREEN)make check-docs$(NC)   - Check documentation quality"
	@echo -e "  $(GREEN)make sync-docs$(NC)    - Sync docs to Docsify"
	@echo -e ""
	@echo -e "$(CYAN)Installation:$(NC)"
	@echo -e "  $(GREEN)make install$(NC)      - Install all dependencies"
	@echo -e "  $(GREEN)make install-hooks$(NC) - Install pre-commit hooks"
	@echo -e "  $(GREEN)make clean$(NC)        - Clean build artifacts"
	@echo -e ""
	@echo -e "$(CYAN)Deployment:$(NC)"
	@echo -e "  $(GREEN)make deploy$(NC)       - Deploy to Raspberry Pi"
	@echo -e "  $(GREEN)make check-updates$(NC) - Check for OTA updates"

#==============================================================================
# Development Targets
#==============================================================================

dev:
	@echo -e "$(BLUE)🚀 Starting development servers...$(NC)"
	@echo -e "$(YELLOW)Choose method:$(NC)"
	@echo -e "  1) Python script (recommended)"
	@echo -e "  2) Bash script"
	@read -p "Enter choice [1]: " choice; \
	if [ "$$choice" = "2" ]; then \
		echo -e "$(GREEN)Using bash script...$(NC)"; \
		./scripts/dev-server.sh; \
	else \
		echo -e "$(GREEN)Using Python script...$(NC)"; \
		python3 dev.py; \
	fi

dev-python:
	@echo -e "$(BLUE)🚀 Starting development servers (Python)...$(NC)"
	@python3 dev.py

dev-bash:
	@echo -e "$(BLUE)🚀 Starting development servers (Bash)...$(NC)"
	@./scripts/dev-server.sh

stop:
	@echo -e "$(RED)🛑 Stopping all development servers...$(NC)"
	@./scripts/stop-dev.sh

build:
	@echo -e "$(BLUE)🔨 Building production version...$(NC)"
	@./build.sh

run:
	@echo -e "$(BLUE)▶️  Running production server...$(NC)"
	@python3 run.py

#==============================================================================
# Quality & Testing Targets
#==============================================================================

quality:
	@echo -e "$(BLUE)✅ Running quality checks...$(NC)"
	@./quality-check.sh

test:
	@echo -e "$(BLUE)🧪 Running tests...$(NC)"
	@echo -e "$(YELLOW)Backend tests:$(NC)"
	@cd $(BACKEND_DIR) && ./venv/bin/pytest tests/ -v
	@echo -e ""
	@echo -e "$(YELLOW)Frontend tests:$(NC)"
	@cd $(FRONTEND_DIR) && npm test -- --watchAll=false

test-backend:
	@echo -e "$(BLUE)🐍 Running backend tests...$(NC)"
	@cd $(BACKEND_DIR) && ./run-tests.sh

test-frontend:
	@echo -e "$(BLUE)⚛️  Running frontend tests...$(NC)"
	@cd $(FRONTEND_DIR) && npm test -- --watchAll=false

format:
	@echo -e "$(BLUE)🎨 Formatting code...$(NC)"
	@echo -e "$(YELLOW)Formatting Python code with Black...$(NC)"
	@cd $(BACKEND_DIR) && ./venv/bin/black app.py config_manager.py ota_manager.py
	@echo -e "$(YELLOW)Formatting frontend code with Prettier...$(NC)"
	@cd $(FRONTEND_DIR) && npm run format

lint:
	@echo -e "$(BLUE)🔍 Running linters...$(NC)"
	@echo -e "$(YELLOW)Linting Python code...$(NC)"
	@cd $(BACKEND_DIR) && ./venv/bin/flake8 app.py config_manager.py ota_manager.py
	@cd $(BACKEND_DIR) && ./venv/bin/mypy app.py config_manager.py ota_manager.py
	@echo -e "$(YELLOW)Linting frontend code...$(NC)"
	@cd $(FRONTEND_DIR) && npm run lint

#==============================================================================
# Documentation Targets
#==============================================================================

docs:
	@echo -e "$(BLUE)📚 Starting documentation server...$(NC)"
	@echo -e "$(YELLOW)Documentation will be available at: http://localhost:35001$(NC)"
	@echo -e "$(CYAN)Press Ctrl+C to stop the server$(NC)"
	@npx docsify-cli serve $(DOCS_DIR) --port 35001 || (echo -e "$(YELLOW)Installing docsify-cli...$(NC)" && npm install -g docsify-cli && npx docsify-cli serve $(DOCS_DIR) --port 35001)

docs-preview:
	@echo -e "$(BLUE)📚 Starting documentation preview...$(NC)"
	@./$(SCRIPTS_DIR)/preview-docs.sh

check-docs:
	@echo -e "$(BLUE)📋 Checking documentation quality...$(NC)"
	@./$(SCRIPTS_DIR)/check-docs.sh

sync-docs:
	@echo -e "$(BLUE)🔄 Syncing documentation to Docsify...$(NC)"
	@./$(SCRIPTS_DIR)/sync-docs.sh

validate-docs:
	@echo -e "$(BLUE)✓ Validating documentation completeness...$(NC)"
	@./$(SCRIPTS_DIR)/validate-docs.sh

#==============================================================================
# Installation Targets
#==============================================================================

install:
	@echo -e "$(BLUE)📦 Installing all dependencies...$(NC)"
	@$(MAKE) install-backend
	@$(MAKE) install-frontend
	@echo -e "$(GREEN)✅ All dependencies installed!$(NC)"

install-backend:
	@echo -e "$(YELLOW)Installing backend dependencies...$(NC)"
	@cd $(BACKEND_DIR) && python3 -m venv venv
	@cd $(BACKEND_DIR) && ./venv/bin/pip install -r requirements.txt
	@cd $(BACKEND_DIR) && ./venv/bin/pip install -r requirements-dev.txt

install-frontend:
	@echo -e "$(YELLOW)Installing frontend dependencies...$(NC)"
	@cd $(FRONTEND_DIR) && npm install

install-hooks:
	@echo -e "$(BLUE)🪝 Installing pre-commit hooks...$(NC)"
	@./$(SCRIPTS_DIR)/install-pre-commit.sh

#==============================================================================
# Clean Target
#==============================================================================

clean:
	@echo -e "$(BLUE)🧹 Cleaning build artifacts...$(NC)"
	@rm -rf $(FRONTEND_DIR)/build
	@rm -rf $(BACKEND_DIR)/__pycache__
	@rm -rf $(BACKEND_DIR)/.pytest_cache
	@rm -rf $(BACKEND_DIR)/.mypy_cache
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@echo -e "$(GREEN)✅ Clean complete!$(NC)"

clean-all: clean
	@echo -e "$(YELLOW)Removing virtual environment...$(NC)"
	@rm -rf $(BACKEND_DIR)/venv
	@echo -e "$(YELLOW)Removing node_modules...$(NC)"
	@rm -rf $(FRONTEND_DIR)/node_modules
	@echo -e "$(GREEN)✅ Deep clean complete!$(NC)"

#==============================================================================
# Deployment Targets
#==============================================================================

deploy:
	@echo -e "$(BLUE)🚀 Deploying to Raspberry Pi...$(NC)"
	@printf "Enter Pi hostname/IP: "; read PI_HOST; \
	printf "Enter Pi username [pi]: "; read PI_USER; \
	PI_USER=$${PI_USER:-pi}; \
	echo "$(YELLOW)Building production version...$(NC)"; \
	$(MAKE) build; \
	echo "$(YELLOW)Copying files to $$PI_USER@$$PI_HOST...$(NC)"; \
	rsync -avz --exclude 'node_modules' --exclude 'venv' --exclude '__pycache__' \
		--exclude '.git' --exclude '*.pyc' --exclude '.pytest_cache' \
		. $$PI_USER@$$PI_HOST:~/posthog_pi/

deploy-docs:
	@echo -e "$(BLUE)📚 Deploying documentation to GitHub Pages...$(NC)"
	@git add docs/
	@git commit -m "docs: update documentation" || true
	@git push origin main
	@echo -e "$(GREEN)✅ Documentation deployed! Check GitHub Actions for status.$(NC)"

check-updates:
	@echo -e "$(BLUE)🔄 Checking for updates...$(NC)"
	@curl -s http://localhost:5000/api/admin/ota/check | jq '.' || echo "$(RED)Error: Make sure the server is running$(NC)"

#==============================================================================
# Utility Targets
#==============================================================================

status:
	@echo -e "$(BLUE)📊 Project Status$(NC)"
	@echo -e "$(YELLOW)Git status:$(NC)"
	@git status --short
	@echo -e ""
	@echo -e "$(YELLOW)Python packages:$(NC)"
	@cd $(BACKEND_DIR) && ./venv/bin/pip list || echo "$(RED)Backend venv not found$(NC)"
	@echo -e ""
	@echo -e "$(YELLOW)Node packages:$(NC)"
	@cd $(FRONTEND_DIR) && npm list --depth=0 || echo "$(RED)Frontend packages not installed$(NC)"

logs:
	@echo -e "$(BLUE)📜 Showing application logs...$(NC)"
	@tail -f /var/log/posthog-pi/*.log 2>/dev/null || echo "$(YELLOW)No logs found. Run on Pi for logs.$(NC)"

#==============================================================================
# Docker Targets (Future Enhancement)
#==============================================================================

docker-build:
	@echo -e "$(BLUE)🐳 Building Docker image...$(NC)"
	@echo -e "$(YELLOW)Docker support coming soon!$(NC)"

docker-run:
	@echo -e "$(BLUE)🐳 Running in Docker...$(NC)"
	@echo -e "$(YELLOW)Docker support coming soon!$(NC)"

#==============================================================================
# Git Shortcuts
#==============================================================================

commit:
	@echo -e "$(BLUE)💾 Creating commit...$(NC)"
	@git add -A
	@git status --short
	@printf "Commit message: "; read MSG; \
	git commit -m "$$MSG"

push:
	@echo -e "$(BLUE)⬆️  Pushing to origin...$(NC)"
	@git push origin main

pull:
	@echo -e "$(BLUE)⬇️  Pulling from origin...$(NC)"
	@git pull origin main

#==============================================================================
# Special Targets
#==============================================================================

.PHONY: pi
pi:
	@echo -e "$(PURPLE)    ____            __  __  __            ____  _ $(NC)"
	@echo -e "$(PURPLE)   / __ \____  ____/ /_/ / / /___  ____ _/ __ \(_)$(NC)"
	@echo -e "$(PURPLE)  / /_/ / __ \/ ___/ __/ /_/ / __ \/ __ \`/ /_/ / / $(NC)"
	@echo -e "$(PURPLE) / ____/ /_/ (__  ) /_/ __  / /_/ / /_/ / ____/ /  $(NC)"
	@echo -e "$(PURPLE)/_/    \____/____/\__/_/ /_/\____/\__, /_/   /_/   $(NC)"
	@echo -e "$(PURPLE)                                 /____/             $(NC)"
	@echo -e ""
	@echo -e "$(CYAN)IoT Analytics Dashboard for Raspberry Pi$(NC)"
	@echo -e "$(YELLOW)Version 1.0$(NC)"

# Easter egg
.PHONY: hedgehog
hedgehog:
	@echo -e "$(BLUE)    /\_/\ $(NC)"
	@echo -e "$(BLUE)   ( o.o )$(NC)"
	@echo -e "$(BLUE)    > ^ < $(NC)"
	@echo -e "$(PURPLE)  PostHog!$(NC)"
