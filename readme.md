# Basic FastAPI GitHub CI Server with Async Processing

A FastAPI-based CI server that processes GitHub push events asynchronously with process ID tracking for deployment automation.

## Features

- **Async Processing**: Non-blocking webhook handling with background task execution
- **Process Tracking**: Unique UUID assigned to each webhook request
- **Status Monitoring**: Real-time status tracking (queued → running → completed/failed)
- **Git Operations**: Automated git clone/pull based on repository changes
- **Custom Commands**: Configurable shell commands per repository
- **RESTful API**: Endpoints to monitor process status and list all processes

## Prerequisites

- Python 3.7+
- FastAPI
- Uvicorn
- Git
- ngrok (for local testing)

## Installation

```bash
pip -r requirements.txt
```

## Configuration

Create a `config.json` file in the same directory as your application:

```json
{
  "repositories": {
    "repo1": {
      "name": "my-repository",
      "path": "/path/to/deployment/directory",
      "branches": {
        "main": {
          "actions": {
            "deploy": {
              "commands": [
                "git pull",
                "npm install",
                "npm run build",
                "pm2 restart app"
              ]
            }
          }
        }
      }
    }
  }
}
```

### Configuration Structure

- **repositories**: Object containing repository configurations
- **name**: GitHub repository name (must match exactly)
- **path**: Local directory where the repository will be cloned/pulled
- **branches**: Branch-specific configurations
- **actions**: Named action groups
- **commands**: Array of shell commands to execute

## API Endpoints

### Webhook Endpoint
```
POST /webhook
```
- Receives GitHub webhook events
- Processes push events to main branch
- Returns immediately with process ID
- Executes commands asynchronously in background

### Status Endpoints

#### Get Process Status
```
GET /status/{process_id}
```
Returns the current status of a specific process.

**Response**: Process status string (`queued`, `running`, `completed`, `failed`, `ignored`)

#### List All Processes
```
GET /processes
```
Returns detailed information about all processes.

**Response**:
```json
{
  "processes": [
    {
      "process_id": "uuid-string",
      "status": "completed",
      "event_type": "push",
      "repository": "my-repo",
      "created_at": "2024-01-01T10:00:00",
      "started_at": "2024-01-01T10:00:01",
      "completed_at": "2024-01-01T10:00:30"
    }
  ]
}
```

## Process Statuses

- **queued**: Process is waiting to start
- **running**: Process is currently executing commands
- **completed**: Process finished successfully
- **failed**: Process encountered an error
- **ignored**: Webhook received but not processed (wrong event type or branch)

## Running the Application

### Local Development

1. **Start the FastAPI server**:
   ```bash
   python app.py
   ```
   The server will run on `http://localhost:8000`

2. **Test the webhook endpoint**:
   ```bash
   curl -X POST http://localhost:8000/webhook \
     -H "Content-Type: application/json" \
     -H "X-GitHub-Event: push" \
     -d '{"repository": {"name": "test-repo"}}'
   ```

### Production Deployment

For production, use a proper WSGI server:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --workers 4
```

## Local Testing with ngrok

When testing locally, you need to expose your local server to the internet so GitHub can send webhooks to it. Here's how to set it up:

### Step 1: Install ngrok

**Option A: Download from website**
1. Go to [ngrok.com](https://ngrok.com)
2. Sign up for a free account
3. Download ngrok for your operating system
4. Extract and install ngrok

**Option B: Install via package manager**
```bash
# macOS with Homebrew
brew install ngrok/ngrok/ngrok

# Windows with Chocolatey
choco install ngrok

# Linux with Snap
snap install ngrok
```

### Step 2: Start up ngrok

```bash
ngrok config add-authtoken YOUR_AUTHTOKEN
```
Get your authtoken from the [ngrok dashboard](https://dashboard.ngrok.com/get-started/your-authtoken).

### Step 3: Start your FastAPI application

```bash
python app.py
```
Your app should be running on `http://localhost:8000`

### Step 4: Expose your local server

In a new terminal window:
```bash
ngrok http 8000
```

You'll see output like:
```
ngrok by @inconshreveable

Session Status    online
Account           your-email@example.com
Version           3.x.x
Region            United States (us)
Latency           50ms
Web Interface     http://127.0.0.1:4040
Forwarding        https://abc123.ngrok.io -> http://localhost:8000
```

**Important**: Copy the `https://abc123.ngrok.io` URL - this is your public webhook URL.

### Step 5: Configure GitHub Webhook

1. **Go to your GitHub repository**
2. **Navigate to Settings > Webhooks**
3. **Click "Add webhook"**
4. **Configure the webhook**:
   - **Payload URL**: `https://abc123.ngrok.io/webhook` (your ngrok URL + `/webhook`)
   - **Content type**: `application/json`
   - **Secret**: (optional, leave blank for testing)
   - **Which events**: Select "Just the push event" or "Send me everything"
   - **Active**: ✓ Checked

5. **Click "Add webhook"**

### Step 6: Test the webhook

1. **Make a commit to your repository**:
   ```bash
   git add .
   git commit -m "Test webhook"
   git push origin main
   ```

2. **Check your FastAPI logs** - you should see:
   ```
   Received event: push (Process ID: abc-123-def)
   Processing started for process ID: abc-123-def
   ```

3. **Check the process status**:
   ```bash
   curl https://abc123.ngrok.io/status/abc-123-def
   ```

4. **Monitor the ngrok web interface** at `http://127.0.0.1:4040` to see incoming requests

### Troubleshooting Local Testing

**Webhook not receiving events?**
- Verify your ngrok URL is correct in GitHub webhook settings
- Check that ngrok is still running (the URL changes each time you restart ngrok)
- Ensure your FastAPI app is running on port 8000
- Check GitHub webhook delivery logs in the webhook settings

**Process not running?**
- Verify your `config.json` has the correct repository name
- Check that the repository name in config matches exactly with GitHub
- Ensure the branch name is "main" (or update your config for different branch names)

**Commands failing?**
- Check file permissions in your deployment directory
- Verify all required tools (git, npm, etc.) are installed
- Check the process status endpoint for error details

### ngrok Tips

- **Free ngrok URLs change on restart** - you'll need to update your GitHub webhook URL each time
- **Paid ngrok plans** offer reserved domains that don't change
- **Keep ngrok running** while testing - closing it breaks the webhook connection
- **Use the web interface** (`http://127.0.0.1:4040`) to inspect webhook requests and debug issues

## Error Handling

The application includes comprehensive error handling:

- **Configuration errors**: Invalid config.json format
- **Git errors**: Failed clone/pull operations
- **Command execution errors**: Failed shell commands
- **Process tracking errors**: Invalid process IDs

All errors are logged and process status is updated accordingly.

## Security Considerations

- **Webhook secrets**: Consider implementing GitHub webhook secret validation
- **Command injection**: Be cautious with shell commands in configuration
- **File permissions**: Ensure proper permissions for deployment directories
- **Network access**: Restrict webhook endpoint access in production
- **Process cleanup**: Consider implementing cleanup for old process records

## Logging

The application outputs detailed logs for:
- Webhook event reception
- Process status changes
- Command execution
- Error occurrences

For production, consider implementing structured logging with proper log levels and file output.

## Example Workflow

1. Developer pushes code to main branch
2. GitHub sends webhook to `/webhook` endpoint
3. FastAPI generates unique process ID and queues the task
4. Background task starts executing configured commands
5. Process status updates from `queued` → `running` → `completed`
6. Deployment commands execute (git pull, build, restart services)
7. Process marked as completed with timestamp

## Monitoring

Use the provided endpoints to monitor your deployments:

```bash
# Check specific deployment
curl http://your-server.com/status/process-id

# List all recent deployments
curl http://your-server.com/processes

# Filter by status in your monitoring scripts
curl http://your-server.com/processes | jq '.processes[] | select(.status=="failed")'
```