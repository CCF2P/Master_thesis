from os import path, getenv

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from Routers.MainRouter import main_router
from Routers.DatabaseRouter import database_router

dotenv_path = path.join(path.dirname(__file__), 'config.env')
if path.exists(dotenv_path):
    load_dotenv(dotenv_path)

HOST = getenv("HOST")
if HOST is None:
    HOST = "127.0.0.1"
    print("[WARN ] Application will start on 127.0.0.1")

PORT = getenv("PORT")
if PORT is None:
    print("[WARN ] Application will use the port by default - 8000")
    PORT = 8000
else:
    PORT = int(PORT)

app = FastAPI()

# Build a path to the "Static" folder from the root folder of the OS +
# a path relative to the current script
path = path.join(
    path.dirname(__file__),
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
        port=PORT,
        http="auto"
    )
