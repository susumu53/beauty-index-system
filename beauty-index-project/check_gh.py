import urllib.request
import json

def check_actions():
    url = "https://api.github.com/repos/susumu53/beauty-index-system/actions/runs"
    req = urllib.request.Request(url)
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            if not data['workflow_runs']:
                print("No workflow runs found.")
                return
            
            latest_run = data['workflow_runs'][0]
            print(f"Latest Workflow Run: {latest_run['name']} (ID: {latest_run['id']})")
            print(f"Status: {latest_run['status']}, Conclusion: {latest_run['conclusion']}")
            
            jobs_url = latest_run['jobs_url']
            with urllib.request.urlopen(urllib.request.Request(jobs_url)) as jobs_resp:
                jobs = json.loads(jobs_resp.read().decode())['jobs']
                for job in jobs:
                    print(f"\nJob: '{job['name']}' Status: {job['status']}, Conclusion: {job['conclusion']}")
                    for step in job['steps']:
                        if step['conclusion'] != 'success':
                            print(f" - Step: '{step['name']}' Conclusion: {step['conclusion']}")
                            
    except Exception as e:
        print(f"Error fetching data: {e}")

if __name__ == "__main__":
    check_actions()
