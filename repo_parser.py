#!/usr/bin/env python3

# Author - Gururaj Rao

from pathlib import Path
import os
import sys
import csv
import subprocess

# Linux-specific file extensions
LIBRARY_EXTENSIONS = {'.so', '.a', '.o', '.la', '.dll'}
SCRIPT_EXTENSIONS = {'.sh', '.py', '.pl', '.rb', '.php'}
BIN_EXTENSIONS = {'.mbn', '.img', '.exe'}

def find_git_repos(root_dir):
    """Find all Git repositories in directory tree"""
    repos = []
    for root, dirs, _ in os.walk(root_dir):
        if '.git' in dirs:
            repos.append(root)
            dirs.remove('.git')  # Skip .git directory
    return repos

def is_executable(path):
    """Check if file has executable permissions"""
    return os.access(path, os.X_OK)

def scan_repo(repo_path):
    """Parse repository for libraries binaries and scripts """
    libraries = []
    binaries = []
    scripts = []
    
    for root, _, files in os.walk(repo_path):
        for file in files:
            file_path = Path(root) / file
            ext = file_path.suffix.lower()
            
            # Skip .git directory contents
            if '.git' in file_path.parts:
                continue
                
            # Check for libraries
            if ext in LIBRARY_EXTENSIONS:
                libraries.append(str(file_path))
            # Include scripts with common extensions
            elif ext in SCRIPT_EXTENSIONS or not ext:
                scripts.append(str(file_path))
            # Check for binaries (executable files)
            elif is_executable(file_path):
                # Include binaries with common extensions
                if ext in BIN_EXTENSIONS or not ext:
                    binaries.append(str(file_path))
    
    return libraries, binaries, scripts

def main():
    # Use provided directory or current working directory
    root_dir = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    root_dir = os.path.abspath(root_dir)
    
    print(f"Parsing for repositories in: {root_dir}\n")
    
    repos = find_git_repos(root_dir)
    if not repos:
        print("No Git repositories found.")
        return
    for repo_path in sorted(repos):
       fieldnames = ['repo_url', 'repo_path', 'libraries', 'binaries', 'scripts']
       #with open('customer_data.csv', 'w', newline='') as csvfile:
       #   writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
       #   writer.writeheader()
       try:
             repo_name = os.path.basename(repo_path)
             result = subprocess.run(
                     ['git', 'remote', '-v'],
                     cwd=repo_path,
                     check=True,
                     stdout=subprocess.PIPE,
                     stderr=subprocess.PIPE,
                     text=True
                     )
             # Parse the output
             remotes = {}
             for line in result.stdout.splitlines():
                parts = line.split()
                if len(parts) >= 3:
                   name = parts[0]
                   url = parts[1]
                   remote_type = parts[2].strip('()')  # Remove parentheses
                   if name not in remotes:
                      remotes[name] = {}
                   remotes[name][remote_type] = url
             libraries, binaries, scripts  = scan_repo(repo_path)
             print(f"Repository URL: {url}")
             print(f"Repository Name: {repo_name}")
             print(f"Path: {repo_path}")
             print("\nLibraries:")
             if libraries:
                for lib in sorted(libraries):
                    print(f"  - {lib}")
             else:
                  print("  None found")
             print("\nBinaries:")
             if binaries:
                for binary in sorted(binaries):
                    print(f"  - {binary}")
             else:
                 print("  None found")
             print("\nScripts:")
             if scripts:
                 for scripts in sorted(scripts):
                     print(f"  - {scripts}")
             else:
                  print("  None found")
             #data = [url, repo_path, lib, binary, scripts]
             #writer.writerows(data)
       except subprocess.CalledProcessError as e:
              return f"Error: {e.stderr.strip()}"
       except FileNotFoundError:
              return "Error: Git not found in PATH"
       except Exception as e:
              return f"Error: {str(e)}"
       print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main()
