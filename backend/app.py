from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess

app = Flask(__name__)
CORS(app)

@app.route('/execute', methods=['POST'])
def execute_code():
    data = request.json
    code = data.get('code', '')

    try:
        result = subprocess.run(['python', '-c', code], capture_output=True, text=True, timeout=10)
        return jsonify({'output': result.stdout, 'error': result.stderr})
    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Code execution timed out'}), 408

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
