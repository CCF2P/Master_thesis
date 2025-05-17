import uvicorn
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from core.Routers.TemplateRouter import template_router

app = FastAPI()
# Build a path to the "Static" folder from the root folder of the OS +
# a path relative to the current script
path = os.path.join(
    os.path.dirname(__file__),
    "core/Routers/Templates/Static"
)
# Mount a sub-application into a FastAPI application.
# In this case, the sub-application that is mounted
# is a StaticFiles object.
app.mount(
    "/Static",
    StaticFiles(directory=path),
    "static"
)
# Include created routers
app.include_router(template_router)

if __name__ == "__main__":
    uvicorn.run(
        app="main:app",
        host="127.0.0.1",
        port=8000,
        http="auto",
        reload=True
    )
