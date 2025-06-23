from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


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
    if event_type == "push":
        # do something with the push payload
        print("Push event received!")

    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)