from flask import Flask, request
import requests
import os

app = Flask(__name__)

DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK')

@app.route('/webhook', methods=['POST'])
def proxy():
    data = request.get_json()
    requests.post(DISCORD_WEBHOOK, json=data)
    return 'OK', 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
