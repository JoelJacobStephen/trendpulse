# Git Repository Cleanup Guide

## Overview

This guide helps you properly manage the `.gitignore` file and clean up files that shouldn't be tracked by Git.

## What We've Done

1. **Created a comprehensive `.gitignore` file** that covers:
   - Python backend files (virtual environments, cache, logs, databases)
   - Frontend files (node_modules, build outputs, package locks)
   - Development tools (IDE files, OS-specific files)
   - Project-specific files (temp files, secrets, logs)

## Files That Should Be Removed from Git Tracking

If these files are currently tracked by Git, you should remove them:

### Backend Files

```bash
# Remove log files
git rm --cached backend/server.log
git rm --cached backend/*.log

# Remove database files
git rm --cached backend/news_trends.db
git rm --cached backend/*.db
git rm --cached backend/*.sqlite

# Remove Python cache
git rm -r --cached backend/__pycache__
git rm -r --cached backend/**/__pycache__

# Remove virtual environment (if accidentally tracked)
git rm -r --cached backend/venv

# Remove model cache
git rm -r --cached backend/models_cache
```

### Frontend Files

```bash
# Remove node_modules (if accidentally tracked)
git rm -r --cached frontend/node_modules

# Remove package-lock.json (keep package.json)
git rm --cached frontend/package-lock.json

# Remove build outputs
git rm -r --cached frontend/dist
git rm -r --cached frontend/build
```

### General Cleanup

```bash
# Remove OS-specific files
git rm --cached .DS_Store
git rm --cached **/.DS_Store

# Remove IDE files
git rm -r --cached .idea
git rm -r --cached .vscode/settings.json
```

## Step-by-Step Cleanup Process

1. **Check current git status:**

   ```bash
   git status
   ```

2. **Remove unwanted tracked files:**

   ```bash
   # Remove specific files that shouldn't be tracked
   git rm --cached backend/server.log
   git rm --cached backend/news_trends.db
   git rm --cached frontend/package-lock.json

   # For directories (if they exist and are tracked):
   git rm -r --cached backend/__pycache__
   git rm -r --cached backend/venv
   git rm -r --cached frontend/node_modules
   ```

3. **Commit the changes:**

   ```bash
   git add .gitignore
   git commit -m "Add comprehensive .gitignore and remove tracked files that should be ignored"
   ```

4. **Verify the cleanup:**
   ```bash
   git status
   # Should now show a clean working directory
   ```

## What Each Section of .gitignore Does

### Python/Backend Section

- **Virtual environments:** `venv/`, `.venv`, `env/` - Never track these
- **Cache files:** `__pycache__/`, `*.pyc` - Generated automatically
- **Database files:** `*.db`, `*.sqlite` - Usually contain local data
- **Log files:** `*.log` - Generated during runtime
- **Model cache:** `models_cache/` - Large ML model files

### Frontend/Node.js Section

- **Dependencies:** `node_modules/` - Can be regenerated from package.json
- **Package locks:** `package-lock.json`, `yarn.lock` - Can cause conflicts
- **Build outputs:** `dist/`, `build/` - Generated from source
- **Cache:** `.cache/`, `.vite/` - Temporary build cache

### Development Tools

- **IDE files:** `.vscode/`, `.idea/` - Personal preferences
- **OS files:** `.DS_Store`, `Thumbs.db` - System-generated

### Security

- **Environment files:** `.env` - Contains secrets and API keys
- **Certificates:** `*.pem`, `*.key` - Security credentials

## Best Practices

1. **Always commit .gitignore first** before adding other files
2. **Keep example files** for environment variables (`.env.example`)
3. **Don't ignore files with actual code** - only generated/temporary files
4. **Use specific patterns** rather than broad wildcards when possible
5. **Document any unusual ignore patterns** in your README

## Troubleshooting

### If files are still showing up after adding to .gitignore:

```bash
# Clear git cache and re-add everything
git rm -r --cached .
git add .
git commit -m "Apply .gitignore to all files"
```

### If you accidentally commit large files:

```bash
# Use git filter-branch or BFG Repo-Cleaner to remove from history
# This is more complex - consult Git documentation
```

## Verification Commands

```bash
# Check what's ignored
git status --ignored

# Check what would be added (dry run)
git add --dry-run .

# See what files git is tracking
git ls-tree -r HEAD --name-only
```

## Final Repository State

After cleanup, your repository should only track:

- Source code files (`.py`, `.js`, `.vue`, `.md`)
- Configuration files (`package.json`, `requirements.txt`)
- Documentation and README files
- Example/template files (`.env.example`)

**It should NOT track:**

- Generated files (logs, databases, cache)
- Dependencies (node_modules, venv)
- Build outputs (dist, build directories)
- Personal IDE settings
- OS-specific files
- Sensitive files (actual .env files)
