# FastAPI GitHub CI Server

A lightweight CI server that processes GitHub webhooks asynchronously with real-time status tracking.

## Features

- **Async Processing**: Non-blocking webhook handling with background tasks
- **Process Tracking**: UUID-based process monitoring with status updates
- **Git Operations**: Automated clone/pull on repository changes  
- **Custom Commands**: Configurable shell commands per repository
- **Status API**: Real-time process monitoring endpoints

## Quick Setup

### 1. Installation
```bash
pip install fastapi uvicorn
```

### 2. Configuration

Create `config.json` in your project root:

```json
{
  "repositories": {
    "repo1": {
      "name": "Sustainable_Shopping",
      "description": "This is a random repository.",
      "path": "/",
      "branches": {
        "main": {
          "events": ["push", "pull_request"],
          "actions": {
            "action1": {
              "name": "Build",
              "description": "Pull and Build the project",
              "commands": [
                "git pull",
                "cd front_end/sustainable_shop && npm install"
              ]
            }
          }
        }
      }
    }
  }
}
```

**Configuration Fields:**
- `name`: Must match your GitHub repository name exactly
- `path`: Local directory where repository will be cloned (use `/` for current directory)
- `events`: GitHub events to listen for (currently only `push` is implemented)
- `commands`: Shell commands executed in sequence in the repository directory

### 3. GitHub Webhook Setup

1. Go to your GitHub repository → **Settings** → **Webhooks**
2. Click **Add webhook**
3. Set **Payload URL** to: `https://ci.axonbuild.com/webhook`
4. Set **Content type** to: `application/json`
5. Select **Just the push event**
6. Click **Add webhook**

### 4. Run the Server

```bash
python app.py
```

Server runs on `http://0.0.0.0:8000`

## API Endpoints

### Webhook Processing
```
POST /webhook
```
Receives GitHub events and processes push events to main branch asynchronously.

### Status Monitoring
```
GET /status/{process_id}
```
Returns process status: `queued`, `running`, `completed`, `failed`, or `ignored`

```
GET /processes  
```
Lists all processes with detailed information including timestamps and errors.

## Process Flow

1. GitHub sends push event to webhook endpoint
2. Server generates unique process ID and queues task
3. Background task executes configured commands
4. Status updates: `queued` → `running` → `completed`/`failed`
5. Monitor progress via status endpoints

## Example Usage

After pushing code to main branch:

```bash
# Check process status
curl https://ci.axonbuild.com/status/abc-123-def

# List all processes
curl https://ci.axonbuild.com/processes
```

## Common Commands

**Web Applications:**
```json
"commands": [
  "git pull",
  "npm install",
  "npm run build",
  "pm2 restart app"
]
```

**Docker Deployments:**
```json
"commands": [
  "git pull", 
  "docker-compose down",
  "docker-compose up -d --build"
]
```

**Python Projects:**
```json
"commands": [
  "git pull",
  "pip install -r requirements.txt",
  "python manage.py migrate",
  "systemctl restart myapp"
]
```

## Error Handling

- All command failures are logged with process ID
- Failed processes include error details in status response
- Repository name mismatches result in ignored events
- Invalid events (non-push, non-main branch) are marked as ignored
