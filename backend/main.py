from os import path, getenv

from dotenv import load_dotenv
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles


from Routers.MainRouter import main_router
from Routers.DatabaseRouter import database_router

dotenv_path = path.join(path.dirname(__file__), 'config.env')
if path.exists(dotenv_path):
    load_dotenv(dotenv_path)

HOST = getenv("HOST")
PORT = int(getenv("PORT"))

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
        http="auto",
        reload=True
    )
