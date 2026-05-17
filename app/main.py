from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, projects, tasks
from app.database import engine
from app import models

models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Taskly API", version="1.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(projects.router, prefix="/projects", tags=["projects"])
app.include_router(tasks.router, prefix="/projects/{project_id}/tasks", tags=["tasks"])


@app.get("/health")
def health():
    return {"status": "ok"}
