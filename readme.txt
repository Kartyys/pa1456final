code.py

This script analyzes a given GitHub repository or local repository directory for various security and best-practice checks, such as:
- Checking for `.gitignore` and `LICENSE` files
- Detecting test files
- Running Gitleaks for secret detection
- Counting workflow YAML files
- Analyzing commit history

Dependencies

Ensure the following dependencies are installed:
- Docker (required for running Git and Gitleaks inside containers)
- Python 3 (recommended, for running the script)



First step, traverse to the folder with the code present in.

cd <repository-directory>


Usage

Running on Windows (Command Prompt or PowerShell)

python code.py <repository_url_or_local_path>


Running on Linux (Terminal)

python3 code.py <repository_url_or_local_path>


Example

To analyze a GitHub repository:

python code.py https://github.com/example/repo.git


To analyze a local repository:

python code.py /path/to/local/repo


Configuration

The script uses a `config.json` file to manage settings, including the directory for cloning repositories and allowed failures. Ensure this file exists with the necessary settings before running the script.

Notes
- Docker must be running for the script to work correctly.
- If using a local repository, ensure the `.git` folder is present.
- If analyzing a GitHub URL, the repository is cloned before analysis.
- If run on linux, make sure to give permission for the program.

License
This project is licensed under the MIT License.

