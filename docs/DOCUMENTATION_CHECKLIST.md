# Documentation Update Checklist

This checklist ensures all documentation stays up-to-date with code changes.

## 🚨 IMPORTANT: Documentation updates are MANDATORY
**Documentation must be updated BEFORE any task is marked as complete.**
**Out-of-date documentation is treated as a FAILING TEST.**

## When to Update Documentation

### 1. ✅ Adding New Features
- [ ] Update README.md with feature description
- [ ] Add usage examples to QUICK_START.md
- [ ] Document any new configuration options
- [ ] Update PROJECT_CONTEXT.md with implementation details
- [ ] Add feature to appropriate section in docs

### 2. ✅ Adding/Modifying API Endpoints
- [ ] Update API endpoints list in README.md
- [ ] Document request/response format
- [ ] Add examples to QUICK_START.md
- [ ] Update OTA_README.md if OTA-related
- [ ] Include error responses and status codes

### 3. ✅ Changing Configuration
- [ ] Update .env.example if environment variables change
- [ ] Document in QUICK_START.md configuration section
- [ ] Update README.md configuration section
- [ ] Add migration notes if breaking changes

### 4. ✅ Adding New Scripts
- [ ] Document script purpose in relevant .md file
- [ ] Add usage examples
- [ ] Include in installation steps if needed
- [ ] Update CLAUDE.md if it affects development workflow

### 5. ✅ Modifying Installation Process
- [ ] Update QUICK_START.md installation steps
- [ ] Update install-pi.sh script if needed
- [ ] Test one-command installer still works
- [ ] Document any new dependencies

### 6. ✅ Adding Dependencies
- [ ] Update requirements.txt or package.json
- [ ] Document why dependency was added
- [ ] Update installation instructions
- [ ] Note any version constraints

### 7. ✅ Quality Gate Changes
- [ ] Update CLAUDE.md quality gate section
- [ ] Document new checks or tools
- [ ] Update quality-check.sh if needed
- [ ] Add to pre-commit hooks if applicable

## Documentation Files Reference

### README.md
- Project overview and features
- Basic usage and API endpoints
- Configuration basics

### QUICK_START.md
- Detailed installation guide
- One-command installer
- Troubleshooting steps
- All configuration options

### PROJECT_CONTEXT.md
- Technical implementation details
- Architecture decisions
- Development history
- Advanced features

### OTA_README.md
- OTA update system
- Branch strategy
- Update API endpoints
- Backup/rollback procedures

### CLAUDE.md
- Development guidelines
- Quality gate requirements
- Common commands
- **MUST include**: "Documentation must be kept up-to-date"

## Validation Commands

```bash
# Sync documentation to Docsify (docs/ folder)
./scripts/sync-docs.sh

# Run documentation quality check
./scripts/check-docs.sh

# Run full quality gate (includes docs sync and check)
./quality-check.sh

# Preview documentation website locally
npx docsify serve docs

# Check specific documentation
grep -i "your-new-feature" README.md QUICK_START.md
```

## Documentation Formats

This project maintains documentation in two formats:
1. **Markdown files** (root directory) - For GitHub and offline reading
2. **Docsify website** (docs/ folder) - For GitHub Pages documentation site

Both formats are automatically kept in sync. The quality gate ensures:
- All markdown files are up to date
- Docsify docs are synced with source files
- Documentation website is deployable

## Red Flags 🚩

These indicate documentation is out of date:
- New files/scripts not mentioned in docs
- API endpoints in code but not in docs
- Configuration options not documented
- Installation steps don't match actual process
- Old/removed features still documented
- Code changes more recent than doc changes

## Documentation Standards

1. **Clarity**: Write for users who know nothing about the project
2. **Examples**: Include code examples and commands
3. **Accuracy**: Test all commands and examples
4. **Completeness**: Cover all features and edge cases
5. **Consistency**: Use consistent formatting and terminology

## Review Process

Before marking ANY task as complete:
1. Run `./scripts/check-docs.sh`
2. Review this checklist
3. Update all affected documentation
4. Commit docs in same PR as code
5. Verify quality gate passes

## Remember

> "Code without documentation is broken code. A feature isn't complete until it's documented."

Documentation is not optional. It's as important as:
- ✅ Passing tests
- ✅ Code formatting
- ✅ Type checking
- ✅ Linting

Treat documentation with the same rigor as code!