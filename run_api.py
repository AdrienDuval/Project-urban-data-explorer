"""Convenience script to start the development server.

Usage:
    python run_api.py

Equivalent to:
    uvicorn api.main:app --reload --host 127.0.0.1 --port 8000

The ``--reload`` flag watches for source changes and restarts automatically.
For production, run uvicorn directly without ``--reload`` and set the number
of workers appropriately:

    uvicorn api.main:app --workers 4 --host 0.0.0.0 --port 8000
"""

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )
