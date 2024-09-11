from contextlib import asynccontextmanager

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


app: FastAPI = FastAPI()

app.include_router(router)

app.mount("/static", StaticFiles(directory="/static"), name="static")
app.mount("/js", StaticFiles(directory="/static/js"), name="js")
app.mount("/css", StaticFiles(directory="/static/css"), name="css")


@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("/static/index.html")
