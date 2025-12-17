#!/usr/bin/env python3
"""
Simple Git Pull Script for PythonAnywhere
Non-interactive version that pulls latest changes without prompts.
"""

import subprocess
import os
import sys


def git_pull(repo_path='.', branch='master', remote='origin'):
    """Pull latest changes from git repository"""
    try:
        original_dir = os.getcwd()
        repo_path = os.path.abspath(repo_path)
        
        if not os.path.exists(repo_path):
            print(f"Error: Repository path does not exist: {repo_path}")
            return False
        
        os.chdir(repo_path)
        
        # Check if it's a git repository
        if not os.path.exists('.git'):
            print(f"Error: Not a git repository: {repo_path}")
            return False
        
        # Fetch latest changes
        print(f"Fetching from {remote}...")
        fetch_result = subprocess.run(
            ['git', 'fetch', remote],
            capture_output=True,
            text=True
        )
        
        if fetch_result.returncode != 0:
            print(f"Warning: Fetch failed: {fetch_result.stderr}")
        
        # Pull changes
        print(f"Pulling from {remote}/{branch}...")
        pull_result = subprocess.run(
            ['git', 'pull', remote, branch],
            capture_output=True,
            text=True
        )
        
        if pull_result.returncode == 0:
            print("✓ Successfully pulled latest changes!")
            if pull_result.stdout:
                print(pull_result.stdout)
            return True
        else:
            print(f"✗ Error pulling changes:")
            print(pull_result.stderr)
            return False
            
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        os.chdir(original_dir)


if __name__ == '__main__':
    # Default to current directory, but allow command line argument
    repo_path = sys.argv[1] if len(sys.argv) > 1 else '.'
    branch = sys.argv[2] if len(sys.argv) > 2 else 'master'
    
    success = git_pull(repo_path, branch)
    sys.exit(0 if success else 1)

