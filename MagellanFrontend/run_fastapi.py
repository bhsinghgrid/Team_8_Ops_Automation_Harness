import os

import uvicorn

from fastapi_app import load_env_file


load_env_file()


if __name__ == "__main__":
    uvicorn.run(
        "fastapi_app:app",
        host=os.getenv("FASTAPI_HOST", "127.0.0.1"),
        port=int(os.getenv("FASTAPI_PORT", "8000")),
        reload=True,
    )
