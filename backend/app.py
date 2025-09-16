from flask import Flask, request, jsonify, session
import sandbox              # Sandbox code 
import uuid                 # For unique session keys
import os 
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

'''
Creates session and starts sandbox for user
    is called from svelte post request: 
    in startup function in script (+page_svelte)
'''
@app.route('/api/startup', methods=['POST'])
def create_session():
    data = request.json

    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
    if sandbox.start_sandbox(session["user_id"]):
        print(f"Created new sandbox for user {session['user_id']}")
        return jsonify({"status": "success", "message": "Succeeded in launching container"}), 200
    return jsonify({"status": "error", "message": "Failed to launch sandbox"}), 400

'''
Lints the provided code using Ruff
    is called from svelte post request:
    lintCode function in +page.svelte
'''
@app.route('/api/lint', methods=['POST'])
def lint_code():
    code = request.json.get("code")
    if not code:
        return jsonify({"error": "No code provided"}), 400

    if "user_id" not in session:
        return jsonify({"status": "error", "message": "No active session"}), 400

    try:
        # Use the sandbox container to lint the code
        result = sandbox.lint_code(session["user_id"], code)
        if result["status"] == "success":
            return jsonify({"lint": result["lint_output"]})
        else:
            return jsonify({"error": result["message"]})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

'''
Does arbitrary code execution in user sandbox
    is called fron svelte post request: 
    executeCode function in +page.svelte 
    (which intern is called by pressing the execute button)
'''
@app.route('/api/execute', methods=['POST'])
def execute_code():
    # Svelte doesn't sent {"code" : "<python code>"} but {"<python code>"}, but doesn't matter.
    data = request.json
    code = data.get('code', '')

    if "user_id" not in session:
        return jsonify({"status": "error", "message": "No active session"}), 400
    
    result = sandbox.execute_code(session["user_id"], code)
    return jsonify(result), 200

'''
Stops sandbox for user session
    called from svelte post request:
'''
@app.route('/api/stop', methods=['POST'])
def stop_sandbox():
    if "user_id" in session:
        sandbox.stop_sandbox(session["user_id"])
        session.pop("user_id", None) 
        return jsonify({"status": "success", "message": "Sandbox stopped"})
    return jsonify({"status": "error", "message": "No active session"}), 400

'''
Saves all tabs for user
    called from svelte post request in +page.svelte
'''
@app.route('/api/save-tabs', methods=['POST'])
def save_tabs():
    if "user_id" not in session:
        return jsonify({"status": "error", "message": "No active session"}), 400

    tabs = request.json.get("tabs")
    if not tabs:
        return jsonify({"status": "error", "message": "No tabs provided"}), 400

    try:
        result = sandbox.save_tabs(session["user_id"], tabs)
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# Only used for development, deployment uses gunicorn which ignores this
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
