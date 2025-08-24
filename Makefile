# DataOrb Makefile for Raspberry Pi
# Usage: make [target] or just 'make' for interactive menu

# Use bash for better echo support
SHELL := /bin/bash

# Default target - show interactive menu
.DEFAULT_GOAL := menu

# Default app directory for Pi deployment
APP_DIR ?= /home/pianalytics/pi-analytics-dashboard

# Node memory limit for Pi builds
NODE_MEM ?= 512

# Python interpreter
PYTHON ?= python3

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
PURPLE := \033[0;35m
CYAN := \033[0;36m
WHITE := \033[1;37m
NC := \033[0m # No Color

# =============================================================================
# Interactive Menu
# =============================================================================

.PHONY: menu
menu: ## Show interactive menu
	@clear
	@echo ""
	@printf "$(BLUE)╔══════════════════════════════════════════════════════════════╗$(NC)\n"
	@printf "$(BLUE)║$(WHITE)            DataOrb Build System - Interactive Menu           $(BLUE)║$(NC)\n"
	@printf "$(BLUE)╠══════════════════════════════════════════════════════════════╣$(NC)\n"
	@printf "$(BLUE)║$(NC)                                                             $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC) $(CYAN)Rebuild Operations:$(NC)                                        $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)   $(GREEN)1)$(NC) Complete rebuild (clean + install + build)            $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)   $(GREEN)2)$(NC) Rebuild frontend only                                 $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)   $(GREEN)3)$(NC) Rebuild backend only                                  $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)                                                             $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC) $(CYAN)Development:$(NC)                                               $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)   $(GREEN)4)$(NC) Start development servers                             $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)   $(GREEN)5)$(NC) Build locally (not on Pi)                             $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)   $(GREEN)6)$(NC) Deploy to Pi                                          $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)                                                             $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC) $(CYAN)Service Management:$(NC)                                        $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)   $(GREEN)7)$(NC) Check status                                          $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)   $(GREEN)8)$(NC) Restart services                                      $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)   $(GREEN)9)$(NC) View logs                                             $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)   $(GREEN)10)$(NC) Follow logs (live)                                   $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)                                                             $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC) $(CYAN)Quality & Testing:$(NC)                                         $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)   $(GREEN)11)$(NC) Run linting                                          $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)   $(GREEN)12)$(NC) Auto-format code                                     $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)   $(GREEN)13)$(NC) Run tests                                            $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)                                                             $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC) $(CYAN)Other:$(NC)                                                     $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)   $(GREEN)14)$(NC) Show all make targets                                $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)   $(GREEN)15)$(NC) Clean everything                                     $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)   $(GREEN)q)$(NC) Quit                                                  $(BLUE)║$(NC)\n"
	@printf "$(BLUE)║$(NC)                                                             $(BLUE)║$(NC)\n"
	@printf "$(BLUE)╚══════════════════════════════════════════════════════════════╝$(NC)\n"
	@echo ""
	@printf "Enter choice: "
	@read choice; \
	case $$choice in \
		1) $(MAKE) rebuild ;; \
		2) $(MAKE) frontend ;; \
		3) $(MAKE) backend ;; \
		4) $(MAKE) dev ;; \
		5) $(MAKE) build-local ;; \
		6) echo "Enter PI_HOST (e.g., 192.168.1.154):"; read pi_host; \
		   echo "Enter PI_USER (e.g., pianalytics):"; read pi_user; \
		   $(MAKE) deploy PI_HOST=$$pi_host PI_USER=$$pi_user ;; \
		7) $(MAKE) status ;; \
		8) $(MAKE) restart-services ;; \
		9) $(MAKE) logs ;; \
		10) $(MAKE) logs-follow ;; \
		11) $(MAKE) lint ;; \
		12) $(MAKE) format ;; \
		13) $(MAKE) test ;; \
		14) $(MAKE) help ;; \
		15) $(MAKE) clean ;; \
		q|Q) echo "Goodbye!" ;; \
		*) echo "Invalid choice. Please run 'make menu' again." ;; \
	esac

.PHONY: help
help: ## Show this help message
	@echo "DataOrb Build System"
	@echo "===================="
	@echo ""
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "Examples:"
	@echo "  make rebuild         # Complete rebuild on Pi"
	@echo "  make frontend        # Rebuild frontend only"
	@echo "  make backend         # Rebuild backend only"
	@echo "  make test           # Run all tests"

# =============================================================================
# Complete Rebuild
# =============================================================================

.PHONY: rebuild
rebuild: clean-all install-all build-all restart-services ## Complete clean rebuild of frontend and backend
	@echo -e "$(GREEN)✓ Complete rebuild finished successfully!$(NC)"
	@$(MAKE) status

.PHONY: clean-all
clean-all: clean-frontend clean-backend ## Clean all dependencies and builds
	@echo -e "$(GREEN)✓ All cleaned$(NC)"

.PHONY: install-all
install-all: install-frontend install-backend ## Install all dependencies
	@echo -e "$(GREEN)✓ All dependencies installed$(NC)"

.PHONY: build-all
build-all: build-frontend build-backend ## Build all components (with linting)
	@echo -e "$(GREEN)✓ All components built and verified$(NC)"

# =============================================================================
# Frontend Targets
# =============================================================================

.PHONY: frontend
frontend: clean-frontend install-frontend build-frontend ## Clean rebuild of frontend only
	@echo -e "$(GREEN)✓ Frontend rebuild complete$(NC)"

.PHONY: clean-frontend
clean-frontend: ## Clean frontend dependencies and build
	@echo -e "$(YELLOW)Cleaning frontend...$(NC)"
	@cd frontend && rm -rf node_modules build
	@echo "  ✓ Removed node_modules and build"

.PHONY: install-frontend
install-frontend: ## Install frontend dependencies
	@echo -e "$(YELLOW)Installing frontend dependencies...$(NC)"
	@cd frontend && npm install
	@echo "  ✓ Frontend dependencies installed"

.PHONY: build-frontend
build-frontend: lint-frontend ## Build frontend with memory constraints for Pi (runs linting first)
	@echo -e "$(YELLOW)Building frontend with NODE_OPTIONS=--max-old-space-size=$(NODE_MEM)$(NC)"
	@cd frontend && \
		NODE_OPTIONS="--max-old-space-size=$(NODE_MEM)" \
		GENERATE_SOURCEMAP=false \
		CI=false \
		npm run build
	@if [ -f "frontend/build/index.html" ]; then \
		echo -e "$(GREEN)  ✓ Frontend build successful$(NC)"; \
	else \
		echo -e "$(RED)  ✗ Frontend build failed!$(NC)"; \
		exit 1; \
	fi

.PHONY: dev-frontend
dev-frontend: ## Run frontend in development mode with file watching
	@echo -e "$(YELLOW)Starting frontend dev server...$(NC)"
	@cd frontend && npm start

# =============================================================================
# Backend Targets
# =============================================================================

.PHONY: backend
backend: clean-backend install-backend build-backend ## Clean rebuild of backend only (with linting)
	@echo -e "$(GREEN)✓ Backend rebuild and verification complete$(NC)"

.PHONY: clean-backend
clean-backend: ## Clean backend virtual environment and cache
	@echo -e "$(YELLOW)Cleaning backend...$(NC)"
	@cd backend && rm -rf venv __pycache__ *.pyc .mypy_cache
	@find backend -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find backend -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find backend -name "*.pyc" -delete 2>/dev/null || true
	@echo "  ✓ Removed venv, Python cache, and mypy cache"

.PHONY: install-backend
install-backend: ## Install backend dependencies in virtual environment
	@echo -e "$(YELLOW)Installing backend dependencies...$(NC)"
	@cd backend && $(PYTHON) -m venv venv
	@cd backend && . venv/bin/activate && pip install --upgrade pip
	@cd backend && . venv/bin/activate && pip install -r requirements.txt
	@if [ -f "backend/requirements-dev.txt" ]; then \
		cd backend && . venv/bin/activate && pip install -r requirements-dev.txt; \
		echo "  ✓ Backend dev dependencies installed"; \
	fi
	@echo "  ✓ Backend dependencies installed"

.PHONY: build-backend
build-backend: lint-backend ## Verify backend code quality (runs linting)
	@echo -e "$(YELLOW)Checking backend code quality...$(NC)"
	@echo -e "$(GREEN)  ✓ Backend code quality verified$(NC)"

.PHONY: dev-backend
dev-backend: ## Run backend in development mode with auto-reload
	@echo -e "$(YELLOW)Starting backend dev server...$(NC)"
	@cd backend && . venv/bin/activate && FLASK_DEBUG=1 $(PYTHON) app.py

# =============================================================================
# Service Management
# =============================================================================

.PHONY: restart-services
restart-services: restart-backend restart-display ## Restart all systemd services
	@echo -e "$(GREEN)✓ All services restarted$(NC)"

.PHONY: restart
restart: restart-services ## Alias for restart-services

.PHONY: restart-backend
restart-backend: ## Restart backend systemd service
	@echo -e "$(YELLOW)Restarting backend service...$(NC)"
	@if systemctl is-active --quiet pi-analytics-backend; then \
		sudo systemctl restart pi-analytics-backend; \
		sleep 2; \
		if systemctl is-active --quiet pi-analytics-backend; then \
			echo -e "$(GREEN)  ✓ Backend service restarted$(NC)"; \
		else \
			echo -e "$(RED)  ✗ Backend service failed to start$(NC)"; \
			sudo systemctl status pi-analytics-backend --no-pager; \
		fi \
	else \
		echo "  Backend service not running, starting it..."; \
		sudo systemctl start pi-analytics-backend; \
	fi

.PHONY: restart-display
restart-display: ## Restart display systemd service
	@echo -e "$(YELLOW)Restarting display service...$(NC)"
	@if systemctl is-active --quiet pi-analytics-display; then \
		sudo systemctl restart pi-analytics-display; \
		sleep 2; \
		if systemctl is-active --quiet pi-analytics-display; then \
			echo -e "$(GREEN)  ✓ Display service restarted$(NC)"; \
		else \
			echo -e "$(RED)  ✗ Display service failed to start$(NC)"; \
			sudo systemctl status pi-analytics-display --no-pager; \
		fi \
	else \
		echo "  Display service not running, starting it..."; \
		sudo systemctl start pi-analytics-display; \
	fi

.PHONY: stop-services
stop-services: ## Stop all systemd services
	@echo -e "$(YELLOW)Stopping services...$(NC)"
	@sudo systemctl stop pi-analytics-backend pi-analytics-display 2>/dev/null || true
	@echo -e "$(GREEN)  ✓ Services stopped$(NC)"

.PHONY: start-services
start-services: ## Start all systemd services
	@echo -e "$(YELLOW)Starting services...$(NC)"
	@sudo systemctl start pi-analytics-backend pi-analytics-display
	@echo -e "$(GREEN)  ✓ Services started$(NC)"

# =============================================================================
# Testing and Quality
# =============================================================================

.PHONY: test
test: test-backend lint ## Run all tests and linting

.PHONY: test-backend
test-backend: ## Run backend tests
	@echo -e "$(YELLOW)Running backend tests...$(NC)"
	@cd backend && . venv/bin/activate && python -m pytest tests/ -v || echo "  No tests found"

.PHONY: lint
lint: lint-frontend lint-backend ## Run linting on frontend and backend

.PHONY: lint-frontend
lint-frontend: ## Run ESLint and stylelint on frontend
	@echo -e "$(YELLOW)Linting frontend code...$(NC)"
	@echo "  Running ESLint (JavaScript/TypeScript)..."
	@cd frontend && npm run lint || \
		(echo -e "$(RED)  ✗ ESLint found issues$(NC)" && exit 1)
	@echo "  Running stylelint (CSS)..."
	@cd frontend && npm run lint:css || \
		(echo -e "$(RED)  ✗ stylelint found issues. Run 'make lint-css-fix' to auto-fix.$(NC)" && exit 1)
	@echo -e "$(GREEN)  ✓ Frontend linting passed$(NC)"

.PHONY: lint-css
lint-css: ## Run stylelint on CSS files only
	@echo -e "$(YELLOW)Linting CSS files...$(NC)"
	@cd frontend && npm run lint:css

.PHONY: lint-css-fix
lint-css-fix: ## Auto-fix CSS linting issues
	@echo -e "$(YELLOW)Auto-fixing CSS issues...$(NC)"
	@cd frontend && npm run lint:css:fix

.PHONY: lint-backend
lint-backend: ## Run flake8, black, and mypy on backend
	@echo -e "$(YELLOW)Linting backend Python code...$(NC)"
	@echo "  Running flake8..."
	@cd backend && . venv/bin/activate && \
		flake8 app.py config_manager.py ota_manager.py themes.py --max-line-length=100 --extend-ignore=E203,W503 || \
		(echo -e "$(RED)  ✗ flake8 found issues$(NC)" && exit 1)
	@echo "  Running black..."
	@cd backend && . venv/bin/activate && \
		black --check app.py config_manager.py ota_manager.py themes.py --line-length=100 --no-cache || \
		(echo -e "$(RED)  ✗ black found formatting issues. Run 'make format-backend' to fix.$(NC)" && exit 1)
	@echo "  Running mypy..."
	@cd backend && . venv/bin/activate && \
		mypy app.py config_manager.py ota_manager.py themes.py --ignore-missing-imports || \
		(echo -e "$(RED)  ✗ mypy found type issues$(NC)" && exit 1)
	@echo -e "$(GREEN)  ✓ Backend linting passed$(NC)"

.PHONY: format
format: format-frontend format-backend ## Auto-format all code

.PHONY: format-frontend
format-frontend: ## Auto-format frontend code with Prettier
	@echo -e "$(YELLOW)Formatting frontend...$(NC)"
	@cd frontend && npm run format

.PHONY: format-backend
format-backend: ## Auto-format backend code with Black
	@echo -e "$(YELLOW)Formatting backend...$(NC)"
	@cd backend && . venv/bin/activate && \
		black app.py config_manager.py ota_manager.py themes.py --line-length=100 --no-cache

# =============================================================================
# Status and Monitoring
# =============================================================================

.PHONY: status
status: ## Check status of all services and components
	@echo "======================================"
	@echo "DataOrb Services Status"
	@echo "======================================"
	@echo ""
	@echo "Backend Service:"
	@if systemctl is-active --quiet pi-analytics-backend 2>/dev/null; then \
		echo -e "$(GREEN)  ✓ Running$(NC)"; \
	else \
		echo -e "$(RED)  ✗ Not running$(NC)"; \
	fi
	@echo ""
	@echo "Display Service:"
	@if systemctl is-active --quiet pi-analytics-display 2>/dev/null; then \
		echo -e "$(GREEN)  ✓ Running$(NC)"; \
	else \
		echo -e "$(RED)  ✗ Not running$(NC)"; \
	fi
	@echo ""
	@echo "Backend API:"
	@if curl -s -f -o /dev/null -w "%{http_code}" http://localhost:5000/api/health | grep -q 200; then \
		echo -e "$(GREEN)  ✓ Responding$(NC)"; \
	else \
		echo -e "$(RED)  ✗ Not responding$(NC)"; \
	fi
	@echo ""
	@echo "Frontend Build:"
	@if [ -f "frontend/build/index.html" ]; then \
		echo -e "$(GREEN)  ✓ Built$(NC)"; \
		stat -c "  Last built: %y" frontend/build/index.html | cut -d'.' -f1; \
	else \
		echo -e "$(RED)  ✗ Not built$(NC)"; \
	fi
	@echo ""
	@echo "Config Auto-Reload:"
	@CONFIG_VERSION=$$(curl -s http://localhost:5000/api/config/version 2>/dev/null | grep -oE '"version":"[^"]+' | cut -d'"' -f4); \
	if [ -n "$$CONFIG_VERSION" ]; then \
		echo -e "$(GREEN)  ✓ Enabled (version: $$CONFIG_VERSION)$(NC)"; \
	else \
		echo -e "$(RED)  ✗ Not available$(NC)"; \
	fi
	@echo ""
	@echo "Network:"
	@echo "  IP: $$(hostname -I | awk '{print $$1}')"
	@echo ""
	@echo "Access URLs:"
	@echo "  Dashboard: http://$$(hostname -I | awk '{print $$1}'):5000"
	@echo "  Config:    http://$$(hostname -I | awk '{print $$1}'):5000/config"
	@echo ""
	@echo "======================================"

.PHONY: logs
logs: ## Show logs from systemd services
	@echo -e "$(YELLOW)Backend logs:$(NC)"
	@sudo journalctl -u pi-analytics-backend -n 20 --no-pager
	@echo ""
	@echo -e "$(YELLOW)Display logs:$(NC)"
	@sudo journalctl -u pi-analytics-display -n 20 --no-pager

.PHONY: logs-follow
logs-follow: ## Follow logs from systemd services
	@sudo journalctl -u pi-analytics-backend -u pi-analytics-display -f

# =============================================================================
# Development Helpers
# =============================================================================

.PHONY: dev
dev: ## Run both frontend and backend in development mode (requires two terminals)
	@echo -e "$(YELLOW)Starting development servers...$(NC)"
	@echo "Run these commands in separate terminals:"
	@echo "  1. make dev-backend"
	@echo "  2. make dev-frontend"

.PHONY: build-local
build-local: ## Build frontend locally (not on Pi)
	@echo -e "$(YELLOW)Building frontend locally...$(NC)"
	@cd frontend && npm run build
	@echo -e "$(GREEN)✓ Frontend built locally$(NC)"

.PHONY: deploy
deploy: build-local ## Build locally and deploy to Pi
	@if [ -z "$(PI_HOST)" ]; then \
		echo -e "$(RED)Error: PI_HOST not set$(NC)"; \
		echo "Usage: make deploy PI_HOST=192.168.1.154 PI_USER=pianalytics"; \
		exit 1; \
	fi
	@echo -e "$(YELLOW)Deploying to $(PI_USER)@$(PI_HOST)...$(NC)"
	@ssh $(PI_USER)@$(PI_HOST) "mkdir -p ~/pi-analytics-dashboard/frontend"
	@scp -r frontend/build $(PI_USER)@$(PI_HOST):~/pi-analytics-dashboard/frontend/
	@echo -e "$(GREEN)✓ Deployed to $(PI_HOST)$(NC)"
	@echo "Restart backend on Pi: ssh $(PI_USER)@$(PI_HOST) 'sudo systemctl restart pi-analytics-backend'"

# =============================================================================
# Maintenance
# =============================================================================

.PHONY: update
update: ## Pull latest changes from git
	@echo -e "$(YELLOW)Pulling latest changes...$(NC)"
	@git pull
	@echo -e "$(GREEN)✓ Updated from git$(NC)"

.PHONY: clean
clean: clean-all ## Clean everything (alias for clean-all)

.PHONY: install
install: install-all ## Install everything (alias for install-all)

.PHONY: build
build: build-all ## Build everything (alias for build-all)
