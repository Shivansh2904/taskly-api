import csv
import io
from datetime import datetime, UTC
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
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
    overdue: bool = False,
    search: str | None = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    _get_owned_project(project_id, current_user.id, db)
    q = db.query(models.Task).filter(models.Task.project_id == project_id)
    if status:
        q = q.filter(models.Task.status == status)
    if priority:
        q = q.filter(models.Task.priority == priority)
    if overdue:
        q = q.filter(
            models.Task.due_date < datetime.now(UTC),
            models.Task.status != models.TaskStatus.done,
        )
    if search:
        q = q.filter(models.Task.title.ilike(f"%{search.strip()}%"))
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
        due_date=body.due_date,
        project_id=project_id,
    )
    if body.tags:
        task.tags = _get_or_create_tags(body.tags, db)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.post("/bulk", response_model=schemas.TaskBulkCreateResponse, status_code=201)
def bulk_create_tasks(
    project_id: int,
    body: schemas.TaskBulkCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Create up to 100 tasks in a single request."""
    _get_owned_project(project_id, current_user.id, db)
    created = []
    for t in body.tasks:
        task = models.Task(
            title=t.title,
            description=t.description,
            status=t.status,
            priority=t.priority,
            due_date=t.due_date,
            project_id=project_id,
        )
        if t.tags:
            task.tags = _get_or_create_tags(t.tags, db)
        db.add(task)
        created.append(task)
    db.commit()
    for task in created:
        db.refresh(task)
    return schemas.TaskBulkCreateResponse(created=created, count=len(created))


@router.get("/export", summary="Export tasks as CSV")
def export_tasks_csv(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Export all tasks in a project to CSV format. Useful for backups or external analysis."""
    _get_owned_project(project_id, current_user.id, db)
    tasks = db.query(models.Task).filter(models.Task.project_id == project_id).all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([
        "id", "title", "description", "status", "priority",
        "due_date", "tags", "created_at", "updated_at"
    ])
    for t in tasks:
        writer.writerow([
            t.id,
            t.title,
            (t.description or "").replace("\n", " "),
            t.status.value,
            t.priority.value,
            t.due_date.isoformat() if t.due_date else "",
            ";".join(tag.name for tag in t.tags),
            t.created_at.isoformat() if t.created_at else "",
            t.updated_at.isoformat() if t.updated_at else "",
        ])

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="tasks_project_{project_id}.csv"'},
    )


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


@router.get("/{task_id}/comments", response_model=list[schemas.CommentResponse])
def list_comments(
    project_id: int,
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """List all comments on a task, oldest first."""
    task = _get_owned_task(task_id, project_id, current_user.id, db)
    return (
        db.query(models.Comment)
        .filter(models.Comment.task_id == task.id)
        .order_by(models.Comment.created_at)
        .all()
    )


@router.post(
    "/{task_id}/comments",
    response_model=schemas.CommentResponse,
    status_code=201,
)
def create_comment(
    project_id: int,
    task_id: int,
    body: schemas.CommentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Add a comment to a task."""
    task = _get_owned_task(task_id, project_id, current_user.id, db)
    comment = models.Comment(
        body=body.body, task_id=task.id, author_id=current_user.id
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


@router.delete("/{task_id}/comments/{comment_id}", status_code=204)
def delete_comment(
    project_id: int,
    task_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Delete a comment. Only the comment's author may delete it."""
    task = _get_owned_task(task_id, project_id, current_user.id, db)
    comment = (
        db.query(models.Comment)
        .filter(models.Comment.id == comment_id, models.Comment.task_id == task.id)
        .first()
    )
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    if comment.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the author can delete this comment")
    db.delete(comment)
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
