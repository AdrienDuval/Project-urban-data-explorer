"""Convenience script to start the development server.

Usage:
    python run_api.py

Equivalent to:
    uvicorn api.main:app --reload --host 127.0.0.1 --port 8000

LAN / phone testing: bind on all interfaces and allow your Next origin in CORS:


    set UDE_API_HOST=0.0.0.0
    set CORS_EXTRA_ORIGINS=http://YOUR_PC_IP:3000
    python run_api.py

The ``--reload`` flag watches for source changes and restarts automatically.
For production, run uvicorn directly without ``--reload`` and set the number
of workers appropriately:

    uvicorn api.main:app --workers 4 --host 0.0.0.0 --port 8000
"""

import os

import uvicorn

if __name__ == "__main__":
    host = os.environ.get("UDE_API_HOST", "127.0.0.1")
    port = int(os.environ.get("UDE_API_PORT", "8000"))
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=True,
    )
