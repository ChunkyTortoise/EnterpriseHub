
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="Test Server")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "test_server"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
