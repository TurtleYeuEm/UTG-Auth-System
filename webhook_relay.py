from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK_URL')

@app.route('/')
def home():
    return "UTG Webhook Relay is running!", 200

@app.route('/log', methods=['POST'])
def relay_log():
    try:
        data = request.get_json()
        
        # Forward to Discord
        response = requests.post(
            DISCORD_WEBHOOK,
            json=data,
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 204:
            return jsonify({"success": True}), 200
        else:
            return jsonify({"success": False, "error": response.text}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
