from flask import Flask, jsonify, request
import json
import os
import requests

app = Flask(__name__)

GITHUB_REPO = os.getenv('GITHUB_REPO')

@app.route('/')
def home():
    return "UTG Auth API is running!", 200

@app.route('/blacklist', methods=['GET'])
def get_blacklist():
    """Get blacklist for Roblox"""
    try:
        url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/blacklist.json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = json.loads(response.text)
        
        # Return in simple format for Roblox
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

@app.route('/check/<userid>', methods=['GET'])
def check_user(userid):
    """Check if user is banned"""
    try:
        url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/main/blacklist.json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        data = json.loads(response.text)
        userids = data.get('userids', [])
        
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
