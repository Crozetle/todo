from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.routes import auth, todos

app = FastAPI(title="Todo App")

app.include_router(auth.router)
app.include_router(todos.router)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def root():
    return RedirectResponse(url="/static/pages/login.html")
