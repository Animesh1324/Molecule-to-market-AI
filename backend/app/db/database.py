import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from sqlalchemy import create_engine, Column, String, Text, text
from sqlalchemy.orm import declarative_base, sessionmaker

from ..models.project import Project

logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DB_DIR, "brandplan.db")
SQLITE_URL = f"sqlite:///{DB_PATH}"

# DATABASE_URL lets a deployment point at managed Postgres. Without it the app
# falls back to a local SQLite file, which on an ephemeral host (Render free
# tier, a container without a mounted volume) is wiped on every restart.
DATABASE_URL = (os.getenv("DATABASE_URL") or "").strip()

if DATABASE_URL:
    # SQLAlchemy dropped the postgres:// alias that several hosts still hand out.
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    # SQLite still needs the threading opt-out; other drivers reject the arg.
    connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, connect_args=connect_args)
else:
    os.makedirs(DB_DIR, exist_ok=True)
    engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
Base = declarative_base()


class ProjectORM(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True, index=True)
    title = Column(String, nullable=False)
    target_molecule_name = Column(String, nullable=False)
    brand_working_name = Column(String, nullable=True)
    therapy_area = Column(String, nullable=False)
    primary_indication = Column(String, nullable=False)
    target_geography = Column(String, nullable=False, default="Global")
    status = Column(String, nullable=False, default="active")
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)


class BrandPlanORM(Base):
    __tablename__ = "brand_plans"
    project_id = Column(String, primary_key=True, index=True)
    data_json = Column(Text, nullable=False)
    updated_at = Column(String, nullable=False)


class MLRAuditLogORM(Base):
    __tablename__ = "mlr_audit_logs"
    id = Column(String, primary_key=True, index=True)
    timestamp = Column(String, nullable=False)
    action_type = Column(String, nullable=False)
    item_reference = Column(String, nullable=False)
    verified_source = Column(String, nullable=False)
    status = Column(String, nullable=False)
    auditor = Column(String, nullable=False)


def init_db():
    """Create tables and seed a few default projects if none exist."""
    # Importing registers the Drug Intelligence tables on Base before
    # create_all runs; without this they are never created.
    from . import drug_models  # noqa: F401
    from . import fda_catalog_models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    try:
        count = session.query(ProjectORM).count()
        if count == 0:
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            default_projects = [
                ProjectORM(
                    id="proj-empa-01",
                    title="Empagliflozin Cardio-Renal Brand Strategy Plan",
                    target_molecule_name="Empagliflozin",
                    brand_working_name="Cardioflo (Empagliflozin)",
                    therapy_area="Cardiometabolic & Renal",
                    primary_indication="Heart Failure & Chronic Kidney Disease in Type 2 Diabetes",
                    target_geography="Global",
                    status="active",
                    created_at=now,
                    updated_at=now,
                ),
                ProjectORM(
                    id="proj-sema-02",
                    title="Semaglutide Obesity & MACE Reduction Strategic Launch",
                    target_molecule_name="Semaglutide",
                    brand_working_name="Semavive (Semaglutide 2.4mg)",
                    therapy_area="Metabolic & Cardiovascular",
                    primary_indication="Chronic Weight Management & Cardiovascular Event Reduction",
                    target_geography="US & Global",
                    status="active",
                    created_at=now,
                    updated_at=now,
                ),
                ProjectORM(
                    id="proj-pembro-03",
                    title="Pembrolizumab 1st-Line NSCLC & Solid Tumors Strategy",
                    target_molecule_name="Pembrolizumab",
                    brand_working_name="Keytruda (Pembrolizumab)",
                    therapy_area="Immuno-Oncology",
                    primary_indication="First-Line Metastatic Non-Small Cell Lung Cancer",
                    target_geography="Global",
                    status="active",
                    created_at=now,
                    updated_at=now,
                ),
                ProjectORM(
                    id="proj-apix-04",
                    title="Apixaban Stroke Prevention in Atrial Fibrillation",
                    target_molecule_name="Apixaban",
                    brand_working_name="Eliquis (Apixaban)",
                    therapy_area="Hematology & Cardiology",
                    primary_indication="Stroke Prevention in Non-Valvular Atrial Fibrillation",
                    target_geography="Global",
                    status="active",
                    created_at=now,
                    updated_at=now,
                ),
            ]
            session.add_all(default_projects)
            session.commit()
    finally:
        session.close()


def db_healthy() -> bool:
    """Return whether the database actually answers a trivial query."""
    session = SessionLocal()
    try:
        session.execute(text("SELECT 1"))
        return True
    except Exception:
        logger.exception("Database health check failed")
        return False
    finally:
        session.close()


def _to_pydantic_project(orm: ProjectORM) -> Project:
    data = {
        "id": orm.id,
        "title": orm.title,
        "target_molecule_name": orm.target_molecule_name,
        "brand_working_name": orm.brand_working_name,
        "therapy_area": orm.therapy_area,
        "primary_indication": orm.primary_indication,
        "target_geography": orm.target_geography,
        "status": orm.status,
        "created_at": orm.created_at,
        "updated_at": orm.updated_at,
    }
    return Project(**data)


def db_list_projects() -> List[Project]:
    session = SessionLocal()
    try:
        rows = session.query(ProjectORM).order_by(ProjectORM.created_at.desc()).all()
        return [_to_pydantic_project(r) for r in rows]
    finally:
        session.close()


def db_get_project(project_id: str) -> Optional[Project]:
    session = SessionLocal()
    try:
        orm = session.get(ProjectORM, project_id)
        if orm:
            return _to_pydantic_project(orm)
        return None
    finally:
        session.close()


def db_save_project(proj: Project) -> Project:
    session = SessionLocal()
    try:
        orm = ProjectORM(
            id=proj.id,
            title=proj.title,
            target_molecule_name=proj.target_molecule_name,
            brand_working_name=proj.brand_working_name,
            therapy_area=proj.therapy_area,
            primary_indication=proj.primary_indication,
            target_geography=proj.target_geography,
            status=proj.status,
            created_at=proj.created_at,
            updated_at=proj.updated_at,
        )
        session.merge(orm)
        session.commit()
        return proj
    finally:
        session.close()


def db_save_brand_plan(project_id: str, plan_data: Dict[str, Any]):
    session = SessionLocal()
    try:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        data_json = json.dumps(plan_data)
        orm = BrandPlanORM(project_id=project_id, data_json=data_json, updated_at=now)
        session.merge(orm)
        session.commit()
    finally:
        session.close()


def db_get_brand_plan(project_id: str) -> Optional[Dict[str, Any]]:
    session = SessionLocal()
    try:
        orm = session.get(BrandPlanORM, project_id)
        if orm:
            return json.loads(orm.data_json)
        return None
    finally:
        session.close()


def db_list_mlr_audit_logs():
    """Return all MLR audit log entries as dicts ordered by timestamp desc."""
    session = SessionLocal()
    try:
        rows = session.query(MLRAuditLogORM).order_by(MLRAuditLogORM.timestamp.desc()).all()
        return [
            {
                "id": r.id,
                "timestamp": r.timestamp,
                "action_type": r.action_type,
                "item_reference": r.item_reference,
                "verified_source": r.verified_source,
                "status": r.status,
                "auditor": r.auditor,
            }
            for r in rows
        ]
    finally:
        session.close()


def db_save_mlr_audit_log(entry: Dict[str, Any]):
    """Persist an MLR audit log entry dict into the database."""
    session = SessionLocal()
    try:
        orm = MLRAuditLogORM(
            id=entry.get("id"),
            timestamp=entry.get("timestamp") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            action_type=entry.get("action_type"),
            item_reference=entry.get("item_reference"),
            verified_source=entry.get("verified_source"),
            status=entry.get("status"),
            auditor=entry.get("auditor"),
        )
        session.merge(orm)
        session.commit()
    finally:
        session.close()

