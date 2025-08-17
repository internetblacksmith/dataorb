# DataOrb Development Makefile
# Interactive menu for all development tasks

.PHONY: menu

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
# Interactive Menu - The Only Way
#==============================================================================

menu:
	@clear
	@echo -e "$(BLUE)╔══════════════════════════════════════════════════════════════╗$(NC)"
	@echo -e "$(BLUE)║$(WHITE)                   DataOrb Development Menu                   $(BLUE)║$(NC)"
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
	@echo -e "$(BLUE)║$(NC)                                                             $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC) $(CYAN)Installation & Setup:$(NC)                                      $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)   $(GREEN)10)$(NC) Install all dependencies                             $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)   $(GREEN)11)$(NC) Clean build artifacts                                $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)                                                             $(BLUE)║$(NC)"
	@echo -e "$(BLUE)║$(NC)   $(RED)q)$(NC) Quit                                                  $(BLUE)║$(NC)"
	@echo -e "$(BLUE)╚══════════════════════════════════════════════════════════════╝$(NC)"
	@echo -e ""
	@printf "$(YELLOW)Select an option: $(NC)"; \
	read choice; \
	case $$choice in \
		1) \
			echo -e "$(BLUE)🚀 Starting development servers...$(NC)"; \
			echo -e "$(GREEN)Frontend will auto-rebuild on file changes$(NC)"; \
			echo -e "$(GREEN)Backend will auto-reload on Python changes$(NC)"; \
			python3 dev.py \
			;; \
		2) \
			echo -e "$(BLUE)🔨 Building production version...$(NC)"; \
			./build.sh; \
			echo -e "$(GREEN)✅ Build complete!$(NC)" \
			;; \
		3) \
			echo -e "$(BLUE)▶️  Running production server...$(NC)"; \
			python3 run.py \
			;; \
		4) \
			echo -e "$(BLUE)✅ Running all quality checks...$(NC)"; \
			./quality-check.sh \
			;; \
		5) \
			echo -e "$(BLUE)🧪 Running tests...$(NC)"; \
			cd $(BACKEND_DIR) && ./venv/bin/pytest tests/ -v 2>/dev/null || echo "$(YELLOW)Backend tests not configured$(NC)"; \
			cd ../$(FRONTEND_DIR) && npm test -- --watchAll=false 2>/dev/null || echo "$(YELLOW)Frontend tests not configured$(NC)" \
			;; \
		6) \
			echo -e "$(BLUE)🎨 Formatting code...$(NC)"; \
			cd $(BACKEND_DIR) && \
			if [ -f venv/bin/black ]; then \
				./venv/bin/black app.py config_manager.py ota_manager.py; \
			else \
				echo "$(YELLOW)Black not installed$(NC)"; \
			fi; \
			cd ../$(FRONTEND_DIR) && npm run format \
			;; \
		7) \
			echo -e "$(BLUE)🔍 Running linters...$(NC)"; \
			cd $(BACKEND_DIR) && \
			if [ -f venv/bin/flake8 ]; then \
				./venv/bin/flake8 app.py config_manager.py ota_manager.py; \
			else \
				echo "$(YELLOW)Flake8 not installed$(NC)"; \
			fi; \
			cd ../$(FRONTEND_DIR) && npm run lint \
			;; \
		8) \
			echo -e "$(BLUE)📚 Starting documentation server...$(NC)"; \
			echo -e "$(YELLOW)Documentation at: http://localhost:35001$(NC)"; \
			npx docsify-cli serve $(DOCS_DIR) --port 35001 \
			;; \
		9) \
			echo -e "$(BLUE)📋 Checking documentation...$(NC)"; \
			if [ -f $(SCRIPTS_DIR)/check-docs.sh ]; then \
				./$(SCRIPTS_DIR)/check-docs.sh; \
			else \
				echo "$(YELLOW)Documentation check script not found$(NC)"; \
			fi \
			;; \
		10) \
			echo -e "$(BLUE)📦 Installing dependencies...$(NC)"; \
			echo -e "$(YELLOW)Installing backend dependencies...$(NC)"; \
			cd $(BACKEND_DIR) && \
			python3 -m venv venv && \
			./venv/bin/pip install -r requirements.txt && \
			if [ -f requirements-dev.txt ]; then \
				./venv/bin/pip install -r requirements-dev.txt; \
			fi; \
			echo -e "$(YELLOW)Installing frontend dependencies...$(NC)"; \
			cd ../$(FRONTEND_DIR) && npm install; \
			echo -e "$(GREEN)✅ All dependencies installed!$(NC)" \
			;; \
		11) \
			echo -e "$(BLUE)🧹 Cleaning build artifacts...$(NC)"; \
			rm -rf $(FRONTEND_DIR)/build; \
			rm -rf $(BACKEND_DIR)/__pycache__; \
			find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true; \
			find . -type f -name "*.pyc" -delete; \
			echo -e "$(GREEN)✅ Clean complete!$(NC)" \
			;; \
		q|Q) \
			echo -e "$(GREEN)👋 Goodbye!$(NC)" \
			;; \
		*) \
			echo -e "$(RED)❌ Invalid option! Please try again.$(NC)"; \
			sleep 2; \
			make \
			;; \
	esac