# Git Pull Automation Guide

Quick reference for using the git pull scripts to update your repository.

## Quick Start

### For PythonAnywhere (Recommended)

```bash
cd /home/chusi/pcmlegacy
python3 git_pull_simple.py
```

### For Local Development

```bash
python git_pull.py
```

## Scripts Overview

### 1. `git_pull.py` - Full-Featured Version

**Features:**
- ✅ Command-line arguments
- ✅ Checks for uncommitted changes
- ✅ Shows recent commits after pull
- ✅ Interactive prompts for safety
- ✅ Detailed status reporting

**Usage Examples:**

```bash
# Basic pull from origin/master
python git_pull.py

# Pull from different branch
python git_pull.py --branch main

# Pull from specific repository path
python git_pull.py --path /home/chusi/pcmlegacy

# Pull from different remote
python git_pull.py --remote upstream

# Quiet mode (minimal output)
python git_pull.py --quiet
```

**Command-Line Options:**
- `--path, -p`: Path to git repository (default: current directory)
- `--branch, -b`: Branch to pull (default: master)
- `--remote, -r`: Remote name (default: origin)
- `--quiet, -q`: Suppress output (only show errors)

### 2. `git_pull_simple.py` - Simple Version

**Features:**
- ✅ Non-interactive (no prompts)
- ✅ Minimal output
- ✅ Perfect for automated deployments
- ✅ Simple command-line arguments

**Usage Examples:**

```bash
# Basic pull (current directory, master branch)
python git_pull_simple.py

# With custom path
python git_pull_simple.py /home/chusi/pcmlegacy

# With custom path and branch
python git_pull_simple.py /home/chusi/pcmlegacy main
```

## PythonAnywhere Deployment Workflow

### Step 1: Pull Latest Changes

```bash
cd /home/chusi/pcmlegacy
python3 git_pull_simple.py
```

### Step 2: Install/Update Dependencies (if needed)

```bash
pip install --user -r requirements.txt
```

### Step 3: Reload Web App

1. Go to PythonAnywhere Dashboard → **Web** tab
2. Click **"Reload"** button

## Common Use Cases

### Update Production Server

```bash
# SSH into PythonAnywhere
cd /home/chusi/pcmlegacy
python3 git_pull_simple.py
# Then reload web app via dashboard
```

### Update Local Development Environment

```bash
python git_pull.py
```

### Automated Deployment Script

Create a `deploy.sh` script:

```bash
#!/bin/bash
cd /home/chusi/pcmlegacy
python3 git_pull_simple.py
pip install --user -r requirements.txt
echo "Deployment complete. Please reload web app."
```

## Troubleshooting

### Error: "Not a git repository"

**Solution:** Make sure you're in the correct directory:
```bash
cd /home/chusi/pcmlegacy  # or your actual project path
```

### Error: "Repository path does not exist"

**Solution:** Check the path:
```bash
ls -la /home/chusi/pcmlegacy
```

### Error: "Permission denied"

**Solution:** Make sure you have read/write permissions:
```bash
chmod +x git_pull.py git_pull_simple.py
```

### Merge Conflicts

If you have local changes that conflict:
1. Stash your changes: `git stash`
2. Pull: `python git_pull_simple.py`
3. Apply stashed changes: `git stash pop`
4. Resolve conflicts manually

## Integration with Deployment

### Add to PythonAnywhere Scheduled Task

1. Go to PythonAnywhere Dashboard → **Tasks** tab
2. Create a new scheduled task
3. Command: `cd /home/chusi/pcmlegacy && python3 git_pull_simple.py`

### Add to Webhook (GitHub Actions)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to PythonAnywhere

on:
  push:
    branches: [ master ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Pull on PythonAnywhere
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.PA_HOST }}
          username: ${{ secrets.PA_USERNAME }}
          key: ${{ secrets.PA_SSH_KEY }}
          script: |
            cd /home/chusi/pcmlegacy
            python3 git_pull_simple.py
```

## Manual Git Commands (Alternative)

If you prefer using git directly:

```bash
# Pull latest changes
git pull origin master

# Or fetch and merge separately
git fetch origin
git merge origin/master

# Check status
git status

# View recent commits
git log --oneline -5
```

## Best Practices

1. **Always backup before pulling** (if you have local changes)
2. **Test locally first** before deploying to production
3. **Check for conflicts** before pulling
4. **Review changes** after pulling
5. **Reload web app** after pulling on PythonAnywhere

## Support

If you encounter issues:
1. Check git status: `git status`
2. Check git log: `git log --oneline -5`
3. Check error messages in the script output
4. Verify repository path and permissions

