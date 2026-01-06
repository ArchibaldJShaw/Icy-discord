from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Discord webhook URLs (you'll need to create these in Discord)
DISCORD_WEBHOOKS = {
    'ic-events': os.getenv('IC_WEBHOOK_URL'),
    'supernatural-events': os.getenv('SPN_WEBHOOK_URL'),
    'general-ic': os.getenv('IC_WEBHOOK_URL')
}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/send-ic', methods=['POST'])
def send_ic_message():
    try:
        data = request.json
        channel_id = data.get('channelId', 'ic-events')
        message = data.get('message', '')
        
        webhook_url = DISCORD_WEBHOOKS.get(channel_id)
        if not webhook_url:
            return jsonify({'status': 'error', 'message': 'No webhook configured'}), 400
        
        # Send to Discord webhook
        payload = {
            'content': message,
            'username': 'IC System'
        }
        
        response = requests.post(webhook_url, json=payload)
        
        if response.status_code == 204:
            return jsonify({'status': 'success'}), 200
        else:
            return jsonify({'status': 'error', 'message': 'Discord webhook failed'}), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
