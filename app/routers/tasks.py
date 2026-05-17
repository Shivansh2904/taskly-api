from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import models, schemas
from app.routers.projects import get_current_user, _get_owned_project

router = APIRouter()


@router.get("", response_model=list[schemas.TaskResponse])
def list_tasks(
    project_id: int,
    status: models.TaskStatus | None = None,
    priority: models.TaskPriority | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_owned_project(project_id, current_user.id, db)
    q = db.query(models.Task).filter(models.Task.project_id == project_id)
    if status:
        q = q.filter(models.Task.status == status)
    if priority:
        q = q.filter(models.Task.priority == priority)
    return q.all()


@router.post("", response_model=schemas.TaskResponse, status_code=201)
def create_task(
    project_id: int,
    body: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_owned_project(project_id, current_user.id, db)
    task = models.Task(
        title=body.title,
        description=body.description,
        status=body.status,
        priority=body.priority,
        project_id=project_id,
    )
    if body.tags:
        task.tags = _get_or_create_tags(body.tags, db)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", response_model=schemas.TaskResponse)
def get_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return _get_owned_task(task_id, project_id, current_user.id, db)


@router.patch("/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    project_id: int,
    task_id: int,
    body: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = _get_owned_task(task_id, project_id, current_user.id, db)
    data = body.model_dump(exclude_none=True)
    tags = data.pop("tags", None)
    for field, val in data.items():
        setattr(task, field, val)
    if tags is not None:
        task.tags = _get_or_create_tags(tags, db)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    task = _get_owned_task(task_id, project_id, current_user.id, db)
    db.delete(task)
    db.commit()


def _get_owned_task(
    task_id: int, project_id: int, user_id: int, db: Session
) -> models.Task:
    _get_owned_project(project_id, user_id, db)
    task = (
        db.query(models.Task)
        .filter(models.Task.id == task_id, models.Task.project_id == project_id)
        .first()
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def _get_or_create_tags(names: list[str], db: Session) -> list[models.Tag]:
    tags = []
    for name in names:
        name = name.lower().strip()
        tag = db.query(models.Tag).filter(models.Tag.name == name).first()
        if not tag:
            tag = models.Tag(name=name)
            db.add(tag)
            db.flush()
        tags.append(tag)
    return tags
