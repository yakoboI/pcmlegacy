#!/usr/bin/env python3
"""
Git Pull Automation Script
Pulls latest changes from git repository with error handling and status reporting.
"""

import subprocess
import os
import sys
from pathlib import Path


def run_git_command(command, repo_path='.'):
    """Run a git command and return the result"""
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
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False  # Don't raise exception on error
        )
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }
    finally:
        os.chdir(original_dir)


def git_status(repo_path='.'):
    """Get git status"""
    result = run_git_command(['git', 'status', '--short'], repo_path)
    if result['success']:
        return result['stdout'].strip()
    return None


def git_pull(repo_path='.', branch='master', remote='origin'):
    """Pull latest changes from git repository"""
    print(f"Pulling from {remote}/{branch}...")
    print(f"Repository: {os.path.abspath(repo_path)}")
    print("-" * 60)
    
    # First, fetch to see what's available
    print("Fetching latest changes...")
    fetch_result = run_git_command(['git', 'fetch', remote], repo_path)
    
    if not fetch_result['success']:
        print(f"Error fetching: {fetch_result['stderr']}")
        return False
    
    # Check current branch
    branch_result = run_git_command(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], repo_path)
    current_branch = branch_result['stdout'].strip() if branch_result['success'] else 'unknown'
    print(f"Current branch: {current_branch}")
    
    # Check if there are local changes
    status = git_status(repo_path)
    if status:
        print("\n⚠ Warning: You have uncommitted changes:")
        print(status)
        response = input("\nContinue with pull? (y/n): ").strip().lower()
        if response != 'y':
            print("Pull cancelled.")
            return False
    
    # Pull changes
    print(f"\nPulling from {remote}/{branch}...")
    pull_result = run_git_command(['git', 'pull', remote, branch], repo_path)
    
    if pull_result['success']:
        print("\n✓ Successfully pulled latest changes!")
        if pull_result['stdout']:
            print(pull_result['stdout'])
        
        # Show what changed
        print("\n" + "-" * 60)
        print("Recent commits:")
        log_result = run_git_command(
            ['git', 'log', '--oneline', '-5', f'{remote}/{branch}'],
            repo_path
        )
        if log_result['success']:
            print(log_result['stdout'])
        
        return True
    else:
        print(f"\n✗ Error pulling changes:")
        print(pull_result['stderr'])
        return False


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Pull latest changes from git repository',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python git_pull.py                    # Pull from origin/master in current directory
  python git_pull.py --branch main      # Pull from origin/main
  python git_pull.py --path /path/to/repo  # Pull from specific repository
  python git_pull.py --remote upstream   # Pull from different remote
        """
    )
    
    parser.add_argument(
        '--path', '-p',
        default='.',
        help='Path to git repository (default: current directory)'
    )
    parser.add_argument(
        '--branch', '-b',
        default='master',
        help='Branch to pull (default: master)'
    )
    parser.add_argument(
        '--remote', '-r',
        default='origin',
        help='Remote name (default: origin)'
    )
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress output (only show errors)'
    )
    
    args = parser.parse_args()
    
    # Convert to absolute path
    repo_path = os.path.abspath(args.path)
    
    if not args.quiet:
        print("=" * 60)
        print("Git Pull Automation Script")
        print("=" * 60)
        print()
    
    success = git_pull(repo_path, args.branch, args.remote)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

