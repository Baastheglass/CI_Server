from fastapi import FastAPI, Request
import uvicorn
import json
import subprocess
import os

def run_commands(clone_url, repo_name, branch, target_path, commands):
    # Full path where repo will be stored
    repo_dir = os.path.join(target_path, repo_name)
    for command in commands:
        if(command == "git pull"):
            if os.path.exists(repo_dir):
                # Repo exists, pull latest
                print(f"Pulling latest code in {repo_dir}")
                subprocess.run(["git", "-C", repo_dir, "pull"], check=True)
            else:
                # Repo doesn't exist, clone it
                print(f"Cloning into {repo_dir}")
                subprocess.run(["git", "clone", "--branch", branch, clone_url, repo_dir], check=True)
        else:    
            print(f"Running shell command: {command}")
            subprocess.run(command, shell=True, check=True, cwd=repo_dir)

app = FastAPI()

@app.post("/webhook")
async def webhook(request: Request):
    # Get JSON payload from GitHub
    payload = await request.json()
    
    # Get GitHub event type from header
    event_type = request.headers.get("X-GitHub-Event")
    
    # Print (or log) payload and event type
    print(f"Received event: {event_type}")
    print(f"Payload: {payload}")

    # Optionally: handle specific event types
    
    if event_type == "push" and payload['ref'].split('/')[-1] == "main":
        repo_name = payload['repository']['name']
        with open('config.json') as f:
            config = json.load(f)    
        for _, repo_info in config['repositories'].items():
            print(repo_info)
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
                print(commands) 
                run_commands(clone_url, repo_name, branch, path, commands)
                print("Success")
    
if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload = True)