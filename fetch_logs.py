import urllib.request
import zipfile
import io

def get_logs():
    run_id = '24619198815'
    url = f"https://api.github.com/repos/susumu53/beauty-index-system/actions/runs/{run_id}/logs"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as resp:
            zip_data = resp.read()
            with zipfile.ZipFile(io.BytesIO(zip_data)) as z:
                # Find the log file for the analyze job
                for name in z.namelist():
                    if 'Run analysis.txt' in name or 'Run analysis' in name:
                        print(f"--- Log file: {name} ---")
                        print(z.read(name).decode('utf-8'))
    except Exception as e:
        print(f"Error fetching logs: {e}")

if __name__ == "__main__":
    get_logs()
