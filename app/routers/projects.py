from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from jose import JWTError
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.database import get_db
from app import models, schemas
from app.auth import decode_access_token

router = APIRouter()
bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> models.User:
    try:
        user_id = decode_access_token(credentials.credentials)
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.get("", response_model=schemas.PaginatedProjects)
def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    q = db.query(models.Project).filter(models.Project.owner_id == current_user.id)
    total = q.count()
    projects = q.offset((page - 1) * page_size).limit(page_size).all()

    items = []
    for p in projects:
        task_count = (
            db.query(func.count(models.Task.id))
            .filter(models.Task.project_id == p.id)
            .scalar()
        )
        items.append(
            schemas.ProjectResponse(
                id=p.id,
                name=p.name,
                description=p.description,
                owner_id=p.owner_id,
                created_at=p.created_at,
                updated_at=p.updated_at,
                task_count=task_count,
            )
        )
    return schemas.PaginatedProjects(items=items, total=total, page=page, page_size=page_size)


@router.post("", response_model=schemas.ProjectResponse, status_code=201)
def create_project(
    body: schemas.ProjectCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    project = models.Project(
        name=body.name, description=body.description, owner_id=current_user.id
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return schemas.ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        owner_id=project.owner_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        task_count=0,
    )


@router.get("/{project_id}", response_model=schemas.ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    project = _get_owned_project(project_id, current_user.id, db)
    task_count = (
        db.query(func.count(models.Task.id))
        .filter(models.Task.project_id == project_id)
        .scalar()
    )
    return schemas.ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        owner_id=project.owner_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        task_count=task_count,
    )


@router.patch("/{project_id}", response_model=schemas.ProjectResponse)
def update_project(
    project_id: int,
    body: schemas.ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    project = _get_owned_project(project_id, current_user.id, db)
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(project, field, val)
    db.commit()
    db.refresh(project)
    task_count = (
        db.query(func.count(models.Task.id))
        .filter(models.Task.project_id == project_id)
        .scalar()
    )
    return schemas.ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        owner_id=project.owner_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        task_count=task_count,
    )


@router.delete("/{project_id}", status_code=204)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    project = _get_owned_project(project_id, current_user.id, db)
    db.delete(project)
    db.commit()


def _get_owned_project(project_id: int, user_id: int, db: Session) -> models.Project:
    project = (
        db.query(models.Project)
        .filter(models.Project.id == project_id, models.Project.owner_id == user_id)
        .first()
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
