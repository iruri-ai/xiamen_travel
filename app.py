from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import uuid
from datetime import datetime
import time

load_dotenv()

app = Flask(__name__, static_folder='static')
app.json.ensure_ascii = False
CORS(app)

request_logs = []

@app.before_request
def before_request():
    from flask import request, g
    g.request_id = str(uuid.uuid4())
    g.start_time = time.time()

@app.after_request
def after_request(response):
    from flask import request, g
    if hasattr(g, 'request_id'):
        duration = time.time() - g.start_time if hasattr(g, 'start_time') else 0
        log = {
            'request_id': g.request_id,
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration': round(duration * 1000, 2),
            'timestamp': datetime.now().isoformat()
        }
        request_logs.append(log)
        response.headers['X-Request-ID'] = g.request_id
    return response

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/api/health')
def health():
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {'status': 'ok', 'timestamp': datetime.now().isoformat()},
        'request_id': str(uuid.uuid4())
    })

@app.route('/api/logs')
def get_logs():
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': request_logs[-50:],
        'request_id': str(uuid.uuid4())
    })

from routes import register_blueprints
register_blueprints(app)

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = False
    app.run(host='0.0.0.0', port=port, debug=debug)
