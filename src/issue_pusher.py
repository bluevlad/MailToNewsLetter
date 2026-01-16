import re
import subprocess
import os
import json
import sys

# Set encoding to utf-8 for console output on Windows
sys.stdout.reconfigure(encoding='utf-8')

ISSUE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs", "issues_2026_01_16.md")

def parse_issues(file_path):
    print(f"Reading issues from: {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Split by "## Issue"
    # The regex looks for "## Issue <number>: <Title>"
    raw_issues = re.split(r'^## Issue \d+:', content, flags=re.MULTILINE)[1:]
    
    parsed = []
    
    # We need to extract the title from the split delimiter or re-parse.
    # Let's use re.finditer to keep the title.
    
    # Better approach: Iterate matches
    matches = list(re.finditer(r'^## Issue \d+:\s*(.+)$', content, flags=re.MULTILINE))
    
    for i, match in enumerate(matches):
        title = match.group(1).strip()
        start = match.end()
        end = matches[i+1].start() if i + 1 < len(matches) else len(content)
        
        chunk = content[start:end].strip()
        
        # Extract Labels
        labels = []
        label_match = re.search(r'\*\*Label:\*\*\s*(.+)', chunk)
        if label_match:
            # Remove backticks and split
            raw_labels = label_match.group(1)
            labels = [l.strip().replace('`', '') for l in raw_labels.split(',')]
            
        # Clean body: Remove the Label line and the separator lines
        body_lines = []
        for line in chunk.split('\n'):
            if "**Label:**" in line:
                continue
            if line.strip() == "---":
                continue
            body_lines.append(line)
            
        body = "\n".join(body_lines).strip()
        
        # BASIC SANITIZATION (as requested)
        # Remove potential API keys or sensitive data if they appear (just in case)
        # Replacing long sequences of alphanumeric characters that look like keys?
        # For now, let's just make sure we don't accidentally publish enviroment variable values if they were hardcoded.
        # The current doc seems clean, but good practice:
        if "AIza" in body: 
            body = re.sub(r'AIza[a-zA-Z0-9_\-]+', '[REDACTED_API_KEY]', body)
            
        parsed.append({
            "title": title,
            "labels": labels,
            "body": body
        })
        
    return parsed

def get_existing_issues():
    try:
        # Check existing issues to prevent duplicates
        cmd = ["gh", "issue", "list", "--limit", "100", "--json", "title"]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        if result.returncode != 0:
            print(f"Warning: Could not list issues. ({result.stderr.strip()})")
            return []
        
        data = json.loads(result.stdout)
        return [i['title'] for i in data]
    except Exception as e:
        print(f"Error checking existing issues: {e}")
        return []

def ensure_labels_exist(needed_labels):
    print("Checking labels...")
    try:
        cmd = ["gh", "label", "list", "--limit", "100", "--json", "name"]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        existing_labels = []
        if result.returncode == 0:
            existing_labels = [l['name'] for l in json.loads(result.stdout)]
            
        for label in needed_labels:
            if label not in existing_labels:
                print(f"Creating label: {label}")
                # Create label with a random color or default
                subprocess.run(["gh", "label", "create", label, "--color", "1f883d", "--description", f"Created by automation"], capture_output=True)
                
    except Exception as e:
        print(f"Warning: Could not check/create labels: {e}")

def create_github_issue(issue):
    cmd = [
        "gh", "issue", "create",
        "--title", issue['title'],
        "--body", issue['body'],
    ]
    for label in issue['labels']:
        cmd.extend(["--label", label])
        
    print(f"Creating issue: '{issue['title']}' ...")
    
    try:
        process = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
        
        if process.returncode == 0:
            print(f" -> Success: {process.stdout.strip()}")
        else:
            print(f" -> Error: {process.stderr.strip()}")
    except Exception as e:
        print(f" -> Execution failed: {e}")

def main():
    if not os.path.exists(ISSUE_FILE):
        print(f"File not found: {ISSUE_FILE}")
        return

    issues = parse_issues(ISSUE_FILE)
    print(f"Found {len(issues)} issues to process.")
    
    # Ensure labels exist
    all_labels = set()
    for issue in issues:
        all_labels.update(issue['labels'])
        
    ensure_labels_exist(all_labels)
    
    existing_titles = get_existing_issues()
            
    for issue in issues:
        if issue['title'] in existing_titles:
            print(f"Skipping duplicate: {issue['title']}")
            continue
            
        create_github_issue(issue)

if __name__ == "__main__":
    main()
