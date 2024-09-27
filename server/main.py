from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

from server.database.db_connection import engine, Base
from server.api.routers import router


@asynccontextmanager
async def lifespan(application: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app: FastAPI = FastAPI(lifespan=lifespan)

app.include_router(router)

static_dir = "/static"
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

js_dir = "/static/js"
if os.path.isdir(js_dir):
    app.mount("/js", StaticFiles(directory=js_dir), name="js")

css_dir = "/static/css"
if os.path.isdir(css_dir):
    app.mount("/css", StaticFiles(directory=css_dir), name="css")


@app.get("/", response_class=HTMLResponse)
async def index():
    """
    Render main page
    """
    return FileResponse("/static/index.html")
