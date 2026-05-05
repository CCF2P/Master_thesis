import os

import uvicorn
from dotenv import load_dotenv

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from Routers.MainRouter import main_router
from Routers.DatabaseRouter import database_router


dotenv_path: str = os.path.join(os.path.dirname(__file__), 'config.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

HOST: str | None = os.getenv("HOST")
if HOST is None:
    HOST = "127.0.0.1"
    print("[WARN ] Application will start on 127.0.0.1")

PORT: str | None = os.getenv("PORT")
if PORT is None:
    print("[WARN ] Application will use the port by default - 8000")
    PORT = "8000"


app = FastAPI()

# Build a path to the "Static" folder from the root folder of the OS +
# a path relative to the current script
path: str = os.path.join(
    os.path.dirname(__file__),
    "Routers/Templates/Static"
)

# Mount a sub-application into a FastAPI application.
# In this case, the sub-application that is mounted
# is a StaticFiles object.
app.mount(
    "/Static",
    StaticFiles(directory=path),
    name="Static"
)

# Include created routers
app.include_router(main_router)
app.include_router(database_router)

if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host=HOST,
        port=int(PORT),
        http="auto"
    )
