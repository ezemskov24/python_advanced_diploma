from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse

from database.db_connection import engine, Base
from api.routers import router


@asynccontextmanager
async def lifespan(application: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app: FastAPI = FastAPI()

app.include_router(router)

app.mount("/static", StaticFiles(directory="../client/static"))
app.mount("/js", StaticFiles(directory="../client/static/js"))
app.mount("/css", StaticFiles(directory="../client/static/css"))


@app.get("/", response_class=HTMLResponse)
async def index():
    return FileResponse("../client/static/templates/index.html")
