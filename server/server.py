import os
import requests
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from datetime import datetime
from auth import auth_middleware, new_token

app = Flask(__name__)
load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
if not GITHUB_TOKEN:
    raise ValueError("GITHUB_TOKEN is not set in .env file")

REPO_OWNER = "positiveblue"
REPO_NAME = "agihouse_agents_demo"
BASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"

def github_request(method, endpoint, data=None):
    url = f"{BASE_URL}/{endpoint}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.request(method, url, json=data, headers=headers)
    return response.json(), response.status_code

@app.route('/newToken', methods=['POST'])
def create_token():
    data = request.json
    expires_at = data.get('expires_at')
    if expires_at is not None:
        expires_at = datetime.fromisoformat(expires_at)

    token = new_token(expires_at, data.get('methods'))
    return jsonify({"token": token})

@app.route('/create', methods=['POST'])
@auth_middleware
def create_issue():
    data = request.json
    
    title = data.get('title')
    body = data.get('body') or data.get('description')
        
    if not title or not body:
        return jsonify({"error": "Title and body (or description) are required"}), 400
    
    issue = {"title": title, "body": body}
    response, status_code = github_request('POST', 'issues', issue)
    
    return jsonify(response), status_code

@app.route('/solve', methods=['POST'])
@auth_middleware
def solve_issue():
    data = request.json
    issue_number = data.get('issue_number')
    if not issue_number or issue_number <= 0:
        return jsonify({"error": "Invalid issue number"}), 400
    
    response, status_code = github_request('POST', f'issues/{issue_number}/labels', ["solved"])
    
    return (jsonify({"message": f"Label 'solved' added to issue #{issue_number}"}), 200) if status_code == 200 else (jsonify({"error": "Error adding label to GitHub issue"}), status_code)

@app.route('/close', methods=['POST'])
@auth_middleware
def close_issue():
    issue_number = request.json.get('issue_number')
    if not issue_number or issue_number <= 0:
        return jsonify({"error": "Invalid issue number"}), 400
    
    labels, status_code = github_request('GET', f'issues/{issue_number}/labels')
    if status_code != 200:
        return jsonify({"error": "Error fetching issue labels"}), 500
    
    if "solve" not in [label['name'] for label in labels]:
        return jsonify({"error": "Issue does not have 'solved' label"}), 400
    
    response, status_code = github_request('PATCH', f'issues/{issue_number}', {"state": "closed"})
    if status_code != 200:
        return jsonify({"error": response}), status_code
    
    return jsonify({"message": f"Issue #{issue_number} closed successfully"}), 200

if __name__ == '__main__':
    app.run(port=8080, debug=True)
