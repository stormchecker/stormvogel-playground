from flask import Flask, request, jsonify, session
from flask_cors import CORS #necessary for frontend/backend communication
import sandbox              #sandbox code 
import uuid                 #for unique session keys

app = Flask(__name__)
CORS(app)

'''
Creates session and starts sandbox for user
called on: startup
'''
@app.before_request
def create_session():
    if "user_id" not in session:
        session["user_id"] = str(uuid.uuid4())
        sandbox.start_sandbox(session["user_id"]) 
        print(f"Created new sandbox for user {session['user_id']}")

'''
Does arbitrary code execution in user sandbox
is called fron svelte post request: 
    executeCode function in +page.svelte 
    (which intern is called by pressing the execute button)
'''
@app.route('/execute', methods=['POST'])
def execute_code():
    #svelte doesn't sent {"code" : "<python code>"} but {"<python code>"}, but doesn't matter.
    data = request.json
    code = data.get('code', '')

    if "user_id" not in session:
        return jsonify({"status": "error", "message": "No active session"}), 400
    
    result = sandbox.execute_code(session["user_id"], code)
    return jsonify(result)

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

#call python3 app.py --debug for dev backend
if __name__ == '__main__':
    app.run(debug=args.debug, host='0.0.0.0', port=5000)
