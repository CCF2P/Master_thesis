import os

from jinja2 import Environment, FileSystemLoader
from fastapi.templating import Jinja2Templates

# Build path to "Templates" folder from OS root folder
template_path = os.path.join(os.path.dirname(__file__), "Templates")
# Creating an environment with FileSystemLoader to collect relative
# folder paths to HTML templates
env = Environment(
    loader=FileSystemLoader(
        searchpath=template_path,
        encoding="utf-8"
    ),
    auto_reload=True
)
# Connected templates that are in the environment
templates = Jinja2Templates(env=env)
