from fastapi import APIRouter, HTTPException
from typing import List
import uuid
from datetime import datetime
from ..models.project import Project, ProjectCreate
from ..db.database import db_list_projects, db_get_project, db_save_project

router = APIRouter(prefix="/api/projects", tags=["Projects"])

@router.get("", response_model=List[Project])
async def list_projects():
    return db_list_projects()

@router.post("", response_model=Project)
async def create_project(req: ProjectCreate):
    new_id = f"proj-{uuid.uuid4().hex[:8]}"
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    proj = Project(
        id=new_id,
        title=req.title,
        target_molecule_name=req.target_molecule_name,
        brand_working_name=req.brand_working_name or f"{req.target_molecule_name.title()} Brand",
        therapy_area=req.therapy_area,
        primary_indication=req.primary_indication,
        target_geography=req.target_geography,
        status="active",
        created_at=now_str,
        updated_at=now_str
    )
    db_save_project(proj)
    return proj

@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str):
    proj = db_get_project(project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj

@router.put("/{project_id}", response_model=Project)
async def update_project(project_id: str, req: ProjectCreate):
    existing = db_get_project(project_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Project not found")

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    updated = Project(
        id=project_id,
        title=req.title,
        target_molecule_name=req.target_molecule_name,
        brand_working_name=req.brand_working_name or f"{req.target_molecule_name.title()} Brand",
        therapy_area=req.therapy_area,
        primary_indication=req.primary_indication,
        target_geography=req.target_geography,
        status=existing.status,
        created_at=existing.created_at,
        updated_at=now_str
    )
    db_save_project(updated)
    return updated
