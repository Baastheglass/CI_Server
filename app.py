from fastapi import FastAPI, Request, BackgroundTasks
import uvicorn
import json
import subprocess
import os
import uuid
from datetime import datetime

# Global dictionary to track processes
processes = {}

def run_commands(clone_url, repo_name, branch, target_path, commands, process_id=None):
    # Update process status if process_id is provided
    if process_id:
        processes[process_id]['status'] = 'running'
        processes[process_id]['started_at'] = datetime.now().isoformat()
    
    # Full path where repo will be stored
    repo_dir = os.path.join(target_path, repo_name)
    
    try:
        for command in commands:
            if(command == "git pull"):
                if os.path.exists(repo_dir):
                    # Repo exists, pull latest
                    print(f"{processes[process_id]} Pulling latest code in {repo_dir}")
                    subprocess.run(["git", "-C", repo_dir, "pull"], check=True)
                else:
                    # Repo doesn't exist, clone it
                    print(f"{processes[process_id]} Cloning into {repo_dir}")
                    subprocess.run(["git", "clone", "--branch", branch, clone_url, repo_dir], check=True)
            else:
                print(f"Running shell command: {command}")
                subprocess.run(command, shell=True, check=True, cwd=repo_dir)
        
        # Mark as completed
        if process_id:
            processes[process_id]['status'] = 'completed'
            processes[process_id]['completed_at'] = datetime.now().isoformat()
        print("Success!")
        
    except Exception as e:
        # Mark as failed
        if process_id:
            processes[process_id]['status'] = 'failed'
            processes[process_id]['error'] = str(e)
            processes[process_id]['failed_at'] = datetime.now().isoformat()
        print(f"Exception occurred: {e}")

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request, background_tasks: BackgroundTasks):
    # Generate unique process ID
    process_id = str(uuid.uuid4())
    
    # Get JSON payload from GitHub
    payload = await request.json()
    
    # Get GitHub event type from header
    event_type = request.headers.get("X-GitHub-Event")
    
    # Print (or log) payload and event type
    print(f"Received event: {event_type} (Process ID: {process_id})")
    print(f"Payload: {payload}")
    
    # Initialize process tracking
    processes[process_id] = {
        'process_id': process_id,
        'status': 'queued',
        'event_type': event_type,
        'repository': payload.get('repository', {}).get('name', 'unknown'),
        'created_at': datetime.now().isoformat()
    }
    
    # Optionally: handle specific event types
    try:
        if event_type == "push" and payload['ref'].split('/')[-1] == "main":
            repo_name = payload['repository']['name']
            print(f"Repo name: {repo_name}")
            with open('config.json') as f:
                config = json.load(f)
                for _, repo_info in config['repositories'].items():
                    print(f"Repo info: {repo_info}")
                    if(repo_info['name'] == repo_name):
                        path = repo_info['path']
                        clone_url = payload['repository']['clone_url']
                        repo_name = payload['repository']['name']
                        branch = payload['ref'].split('/')[-1]
                        actions = repo_info['branches']['main']['actions']
                        commands = []
                        for _, action_info in actions.items():
                            for command in action_info['commands']:
                                commands.append(command)
                        print(f"Commands to run: {commands}")
                        
                        # Run commands in background
                        background_tasks.add_task(
                            run_commands, clone_url, repo_name, branch, path, commands, process_id
                        )
                        
                        print(f"Processing started for process ID: {process_id}")
        
        # If not processed
        processes[process_id]['status'] = 'ignored'
        print(f"Event not processed for process ID: {process_id}")
        
    except Exception as e:
        processes[process_id]['status'] = 'failed'
        processes[process_id]['error'] = str(e)
        print(f"Exception occurred in webhook for process ID {process_id}: {e}")

@app.get("/status/{process_id}")
async def get_status(process_id: str):
    if process_id in processes:
        return processes[process_id]["status"]
    return {"error": "Process not found"}

@app.get("/processes")
async def list_processes():
    return {"processes": list(processes.values())}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)