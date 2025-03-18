import subprocess
import os
import sys
import shutil
import stat
import json
from pathlib import Path

#function to be able to remove readable .git file
def force_remove_readonly(func, path, _):
    os.chmod(path, stat.S_IWRITE)  # Change file permission to writable
    func(path)  # Retry the removal function (os.remove or os.rmdir)


# Load config.json file 
def load_config():
    with open('config.json', 'r') as f:
        return json.load(f)


# Clone the repository using Git inside Docker, cloning to location given in config file
def clone_repository(repo_url, clone_dir):
    if os.path.exists(clone_dir):
        print(f"Removing existing directory: {clone_dir}")
        shutil.rmtree(clone_dir, onerror=force_remove_readonly)

    print(f"Cloning into {clone_dir} using Docker...")

    subprocess.run([
        "docker", "run", "--rm",
        "-v", f"{os.getcwd()}:/repo",
        "alpine/git", "clone", repo_url, f"/repo/{clone_dir}"
    ])
    print("-" * 40)


# Parse the .gitignore file to get the list of ignored files and directories
def parse_gitignore(clone_dir):
    gitignore_path = os.path.join(clone_dir, '.gitignore')
    ignored = []

    if os.path.exists(gitignore_path):
        with open(gitignore_path, 'r') as f:
            ignored = [line.strip() for line in f.readlines() if line.strip() and not line.startswith('#')]

    return ignored


# Check if a file is ignored by .gitignore
def is_ignored(path, ignored):
    for pattern in ignored:
        if Path(path).match(pattern):  # Using pathlib's match function for simple globbing
            return True
    return False


# Check for the existence of .gitignore and LICENSE files
def check_files(clone_dir, allowed_failures):
    # Find .gitignore file (case-insensitive)
    gitignore_path = next((os.path.join(clone_dir, f) for f in os.listdir(clone_dir) if f.lower() == '.gitignore'), None)

    # Find LICENSE file (case-insensitive)
    license_path = next((os.path.join(clone_dir, f) for f in os.listdir(clone_dir) if f.lower() == 'license'), None)

    # Check .gitignore
    if gitignore_path and os.path.exists(gitignore_path):
        if os.path.getsize(gitignore_path) <= 1:  # Check if empty
            print("🟡 .gitignore exists but is empty.")
        else:
            
            print("🟢 .gitignore exists.")
    else:
        if allowed_failures.get('gitignore_check', False):
            print("🟡 .gitignore is missing. (failure is allowed)")
        else:
            print("🔴 .gitignore is missing.")
            return False

    # Check LICENSE
    if license_path and os.path.exists(license_path):
        if os.path.getsize(license_path) <= 1:  # Check if empty
            print("🟡 LICENSE exists but is empty.")
        else:
            print("🟢 LICENSE exists.")
    else:
        if allowed_failures.get('license_check', False):
            print("🟡 LICENSE is missing. (failure is allowed)")
        else:
            print("🔴 LICENSE is missing.")
            return False

    return True




# Check for files containing 'test' in their name
def list_test_files(clone_dir, allowed_failures):
    if not os.path.exists(clone_dir):
        print("🔴 Cloned repository not found.")
        return False

    # Get the list of ignored files and directories
    ignored = parse_gitignore(clone_dir)

    test_files = []
    print("Listing files containing 'test' in their name:")

    # Walk through the directory and its subdirectories
    for root, dirs, files in os.walk(clone_dir):
        # Ignore directories listed in .gitignore
        dirs[:] = [d for d in dirs if not is_ignored(os.path.join(root, d), ignored)]
        
        for file in files:
            if 'test' in file.lower() and not is_ignored(os.path.join(root, file), ignored):
                test_files.append(os.path.join(root, file))

    if test_files:
        for test_file in test_files:
            print(f"   📄 {test_file}")
    else:
        if allowed_failures['test_files_check']:
            print("🟡 No test files found (but failure is allowed).")
        else:
            print("🔴 No test files found.")
        return False

    return True


# Run Gitleaks using Docker
def run_gitleaks(repo_dir, allowed_failures):
    try:
        abs_repo_dir = os.path.abspath(repo_dir)

        result = subprocess.run(
            ["docker", "run", "--rm",
             "-v", f"{abs_repo_dir}:/repo",
             "zricethezav/gitleaks:latest", "detect",
             "--source", "/repo", "--no-git", "--verbose"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("🟢 No leaks found by Gitleaks.")
            return True

        # Filter and parse Gitleaks output
        filtered_output = "\n".join(
            line for line in result.stdout.split("\n")
            if not line.startswith("    ○") and line.strip() != ""
        )

        leaks = []
        finding = {}

        for line in filtered_output.split("\n"):
            line = line.strip()
            if line.startswith("Finding:"):
                if finding:
                    leaks.append(finding)
                finding = {"finding": line.replace("Finding: ", "").strip()}
            elif line.startswith("Secret:"):
                finding["secret"] = line.replace("Secret: ", "").strip()
            elif line.startswith("RuleID:"):
                finding["rule"] = line.replace("RuleID: ", "").strip()
            elif line.startswith("File:"):
                finding["file"] = line.replace("File: ", "").strip()

        if finding:
            leaks.append(finding)

        if not leaks:
            print("⚠️ Gitleaks reported an issue, but no specific leaks were found.")
            return True

        if allowed_failures['gitleaks_check']:
            print("🟡 Gitleaks detected sensitive data (but failure is allowed).")
        else:
            print("🔴 Potential leaks detected:")

        for leak in leaks:
            print(
                f"📄 File: {leak.get('file', 'Unknown')}\n"
                f"   🔑 Secret: {leak.get('secret', 'Unknown')}\n"
                f"   🛡️ Rule: {leak.get('rule', 'Unknown')}\n"
                + "-" * 40
            )

        return False

    except Exception as e:
        print(f"⚠️ Gitleaks scan failed: {str(e)}")
        return False


# Count the number of YAML workflow files
def count_workflow_files(clone_dir, allowed_failures):
    workflow_dir = os.path.join(clone_dir, '.github', 'workflows')
    if not os.path.exists(workflow_dir):
        if allowed_failures['workflow_check']:
            print("🟡 No workflows found (but failure is allowed).")
        else:
            print("🔴 No workflows found.")
        return False

    yaml_files = [f for f in os.listdir(workflow_dir) if f.endswith('.yaml') or f.endswith('.yml')]
    yaml_count = len(yaml_files)

    if yaml_count == 0:
        if allowed_failures['workflow_check']:
            print("🟡 No workflow YAML files found (but failure is allowed).")
        else:
            print("🟡 No workflow YAML files found.")
        return False
    else:
        print(f"🟢 {yaml_count} workflow YAML files found.")
        return True


# Analyze commits and contributors using Git inside Docker
def analyze_commits(clone_dir, allowed_failures):
    if not os.path.exists(clone_dir):
        print("\ud83d\udd34 Cloned repository not found.")
        return False

    abs_clone_dir = os.path.abspath(clone_dir)

    result = subprocess.run(
        ["docker", "run", "--rm",
         "-v", f"{abs_clone_dir}:/repo",
         "-w", "/repo",
         "alpine/git", "shortlog", "--all", "--no-merges", "-sn"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        if allowed_failures['commits_check']:
            print("\ud83d\udfe1 Error analyzing commits (but failure is allowed).")
        else:
            print("\ud83d\udd34 Error analyzing commits.")
        return False

    total_commits = 0
    contributors = []
    
    for line in result.stdout.splitlines():
        count, name = line.strip().split('\t')
        count = int(count.strip())
        total_commits += count
        contributors.append((name.strip(), count))
    
    print("Commit Summary:")
    print(f"Total commits: {total_commits}")
    print("Contributor rankings (by number of commits):")
    for name, count in contributors:
        print(f"   {name}: {count} commits")
    print("-" * 40)
    return True



# Check if the input path is a URL
def is_url(path):
    return path.lower().startswith('https://github.com/')


def main():
    if len(sys.argv) != 2:
        print("Usage: python checkpathurl.py <repository_url_or_local_path>")
        sys.exit(1)

    input_path = sys.argv[1]
    config = load_config()
    clone_dir = config.get("clone_directory", "cloned_repo")
    allowed_failures = config.get('allowed_failures', {})

    overall_status = True  # Assume everything passes unless we find a non allowed failure

    # Check if input is GitHub URL or local 
    if is_url(input_path):  # If it's a GitHub URL
        print(f"Cloning from GitHub URL: {input_path}")
        clone_repository(input_path, clone_dir)  # Clone from GitHub
    else:
        repo_path = Path(input_path).resolve()  # Normalize local path

        if repo_path.is_dir() and (repo_path / ".git").exists():  # Check if its a local repo
            print(f"Using local repository at: {repo_path}" "\n-"*40)
            clone_dir = repo_path  # Skip cloning, use the local repo path directly
        else:
            print("Invalid repository path or URL.")
            sys.exit(1)

    # Analyze commits 
    if not analyze_commits(clone_dir, allowed_failures):
        if not allowed_failures['commits_check']:
            overall_status = False

    # Check for license and gitignore
    if not check_files(clone_dir, allowed_failures):
        if not allowed_failures['gitignore_check'] and not allowed_failures['license_check']:
            overall_status = False

    # Check workflow files
    if not count_workflow_files(clone_dir, allowed_failures):
        if not allowed_failures['workflow_check']:
            overall_status = False

    # Check for test files
    if not list_test_files(clone_dir, allowed_failures):
        if not allowed_failures['test_files_check']:
            overall_status = False

    # Run Gitleaks
    if not run_gitleaks(clone_dir, allowed_failures):
        if not allowed_failures['gitleaks_check']:
            overall_status = False

    # Final decision: if all failures are allowed or no critical failures occurred, mark as green
    if overall_status:
        print("🟢 All checks passed or failures were allowed.")
    else:
        print("🔴 Some checks failed.")

    # Return the exit status code: 0 for success, non-zero for failure
    sys.exit(0 if overall_status else 1)



if __name__ == '__main__':
    main()
