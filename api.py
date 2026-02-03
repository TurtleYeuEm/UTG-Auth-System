from flask import Flask, jsonify, request
import json
import os
import requests

app = Flask(__name__)

GITHUB_REPO = os.getenv('GITHUB_REPO')

@app.route('/')
def home():
    return "UTG Auth API is running!", 200

@app.route('/blacklist', methods=['GET', 'POST'])
def get_blacklist():
    """Get blacklist - Support both GET and POST"""
    try:
        import time
        url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/blacklist.json?t={int(time.time())}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = json.loads(response.text)
        
        return jsonify({
            "success": True,
            "userids": data.get('userids', [])
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "userids": []
        }), 500

@app.route('/check', methods=['POST'])
def check_user():
    """Check if user is banned via POST"""
    try:
        # Get userid from POST body
        data = request.get_json()
        userid = str(data.get('userid', ''))
        
        if not userid:
            return jsonify({
                "success": False,
                "error": "No userid provided",
                "banned": False
            }), 400
        
        # Get blacklist
        import time
        url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/blacklist.json?t={int(time.time())}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        blacklist_data = json.loads(response.text)
        userids = blacklist_data.get('userids', [])
        
        is_banned = userid in userids
        
        return jsonify({
            "success": True,
            "userid": userid,
            "banned": is_banned
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "banned": False
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
