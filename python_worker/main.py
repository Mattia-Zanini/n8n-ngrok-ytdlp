from flask import Flask, request, jsonify
import subprocess
import os

import json

app = Flask(__name__)
API_KEY = os.environ.get("PYTHON_WORKER_API_KEY")
SCRIPTS_DIR = "/app/scripts"

def is_authorized():
    return request.headers.get("X-API-KEY") == API_KEY

def is_safe_arg(arg):
    # Prevenzione Argument Injection per yt-dlp e comandi shell
    # Blocca flag pericolosi noti
    forbidden_flags = ["--exec", "--alias", "--config-location"]
    if any(flag in arg for flag in forbidden_flags):
        return False
    # Blocca tentativi di path traversal o accesso a cartelle sensibili
    forbidden_paths = ["/etc/", "/bin/", "/usr/", ".ssh"]
    if any(path in arg for path in forbidden_paths):
        return False
    return True

@app.route('/run', methods=['POST'])
@app.route('/execute', methods=['POST']) # Alias per compatibilità con n8n
def run_script():
    if not is_authorized():
        return jsonify({"error": "Unauthorized"}), 401

    data_req = request.json
    script_name = data_req.get("script") # Es: "test_script.py"
    args = data_req.get("args", [])      # Es: ["Mario", "Rossi"]

    if not script_name:
        return jsonify({"error": "Specificare il nome dello script"}), 400

    # Validazione argomenti di sicurezza
    if not all(is_safe_arg(arg) for arg in args):
        return jsonify({"error": "Rilevati argomenti non sicuri"}), 400

    # Sicurezza: evitiamo Path Traversal (es. "../../../etc/passwd")
    # Ci assicuriamo che lo script sia solo il nome del file, senza percorsi
    script_name = os.path.basename(script_name)
    script_path = os.path.join(SCRIPTS_DIR, script_name)

    if not os.path.exists(script_path):
        return jsonify({"error": f"Script {script_name} non trovato nella cartella scripts"}), 404

    try:
        # Costruiamo il comando: python3 /app/scripts/nome_script.py arg1 arg2 ...
        command = ["python3", script_path] + args
        
        # Eseguiamo lo script (usiamo un timeout per sicurezza)
        result = subprocess.run(command, capture_output=True, text=True, timeout=300)
        
        # Proviamo a decodificare lo stdout come JSON
        try:
            script_data = json.loads(result.stdout)
        except:
            script_data = result.stdout # Resta stringa se non è JSON

        return jsonify({
            "status": "success" if result.returncode == 0 else "error",
            "data": script_data,
            "stderr": result.stderr,
            "return_code": result.returncode
        })
    except subprocess.TimeoutExpired:
        return jsonify({"status": "error", "message": "Script execution timed out"}), 504
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)