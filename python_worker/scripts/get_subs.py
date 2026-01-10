import sys
import subprocess
import json
import os
import glob

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"status": "error", "message": "Missing URL"}))
        return

    video_url = sys.argv[1]
    output_dir = "/data"
    video_id = video_url.split("v=")[-1]
    out_template = os.path.join(output_dir, f"{video_id}.%(ext)s")
    
    # Percorso interno al container definito nel docker-compose
    cookies_path = "/app/cookies.txt"

    command = [
        "yt-dlp",
        "--write-auto-subs",
        "--sub-langs", ".*-orig",
        "--convert-subs", "srt",
        "--skip-download",
        "--js-runtimes", "deno", # Ora che abbiamo node/deno è più stabile
        "--output", out_template,
        video_url
    ]

    # Se il file cookies esiste, lo aggiungiamo al comando
    if os.path.exists(cookies_path):
        command.extend(["--cookies", cookies_path])

    try:
        # Eseguiamo il comando
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        
        found_files = glob.glob(f"{output_dir}/{video_id}*.srt")
        if not found_files:
            print(json.dumps({"status": "error", "message": "No file generated", "stderr": result.stderr}))
            return

        latest_file = max(found_files, key=os.path.getctime)
        
        # Change file permissions to 777 so n8n can access it
        os.chmod(latest_file, 0o777)

        print(json.dumps({
            "status": "success",
            "file_name": os.path.basename(latest_file),
            "file_path": latest_file,
            "n8n_file_path": latest_file.replace("/data/", "/home/node/.n8n-files/"),
            "message": "Subtitles downloaded using cookies"
        }))

    except subprocess.CalledProcessError as e:
        print(json.dumps({
            "status": "error",
            "message": "Download failed even with cookies",
            "stderr": e.stderr
        }))

if __name__ == "__main__":
    main()