import subprocess
import tempfile
from flask import Flask, request, jsonify, session
from flask_cors import CORS # Necessary for frontend/backend communication
import sandbox              # Sandbox code 
import uuid                 # For unique session keys
import os 
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
CORS(app, supports_credentials=True)
app.secret_key = os.environ.get("FLASK_SECRET_KEY")

'''
Creates session and starts sandbox for user
is called fron svelte post request: 
    in startup function in script (+page_svelte)
'''
@app.route('/startup', methods=['POST'])
def create_session():
    data = request.json

    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
        if sandbox.start_sandbox(session["user_id"]):
            print(f"Created new sandbox for user {session['user_id']}")
            return jsonify({"status": "success", "message": "Succeded in lauching container"}), 200
    return jsonify({"status": "error", "message": "Failed to launch sandbox"}), 400

'''
Lints the provided code using Ruff
is called from svelte post request:
    lintCode function in +page.svelte
'''
@app.route('/lint', methods=['POST'])
def lint_code():
    code = request.json.get("code")
    if not code:
        return jsonify({"error": "No code provided"}), 400
    try:
        # Write the code to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
            temp_file.write(code.encode())
            temp_file_path = temp_file.name

        # Run Ruff with the temp file
        process = subprocess.run(
            ["ruff", "check", temp_file_path],
            capture_output=True,
            text=True
        )

        # Log output and errors
        print(f"Ruff stdout: {process.stdout}")
        print(f"Ruff stderr: {process.stderr}")

        # Parse Ruff's output
        lint_output = process.stdout.strip()

        if process.returncode != 0:
            return jsonify({"error": process.stdout}), 500
        return jsonify({"lint": lint_output})

    except Exception as e:
        print(f"Linting failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


'''
Does arbitrary code execution in user sandbox
is called fron svelte post request: 
    executeCode function in +page.svelte 
    (which intern is called by pressing the execute button)
'''
@app.route('/execute', methods=['POST'])
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
is called from svelte post request:
    TODO: use onDestroy in svelte frontend
          use visibilitychange event to signal closed tabs or switch tabs -> maybe close sandbox then
'''
@app.route('/stop', methods=['POST'])
def stop_sandbox():
    if "user_id" in session:
        sandbox.stop_sandbox(session["user_id"])
        session.pop("user_id", None) 
        return jsonify({"status": "success", "message": "Sandbox stopped"})
    return jsonify({"status": "error", "message": "No active session"}), 400

# Call python3 app.py --debug for dev backend
# Problems with passing arguments in my current setup, so hardcoded debug mode :|
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
