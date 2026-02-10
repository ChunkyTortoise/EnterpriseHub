import os

import uvicorn

from portal_api import app

if __name__ == "__main__":
    # Get port from environment variable for deployment (e.g., Railway)
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
