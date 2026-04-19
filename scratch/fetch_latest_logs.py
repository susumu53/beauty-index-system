import urllib.request
import zipfile
import io
import json

def get_logs():
    # Fetch latest run ID first
    url = "https://api.github.com/repos/susumu53/beauty-index-system/actions/runs"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            run_id = data['workflow_runs'][0]['id']
            print(f"Fetching logs for run {run_id}...")
            
        logs_url = f"https://api.github.com/repos/susumu53/beauty-index-system/actions/runs/{run_id}/logs"
        req = urllib.request.Request(logs_url)
        with urllib.request.urlopen(req) as resp:
            zip_data = resp.read()
            with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
                found = False
                for name in z.namelist():
                    if 'Run analysis.txt' in name or 'Run analysis' in name:
                        print(f"--- Log file: {name} ---")
                        content = z.read(name).decode('utf-8', errors='ignore')
                        # Print last 50 lines to keep it concise
                        lines = content.split('\n')
                        print('\n'.join(lines[-50:]))
                        found = True
                if not found:
                    print("Could not find 'Run analysis.txt' in the logs zip.")
                    print("Available files:", z.namelist())
    except Exception as e:
        print(f"Error fetching logs: {e}")

if __name__ == "__main__":
    get_logs()
