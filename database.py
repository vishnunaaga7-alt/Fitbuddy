from datetime import datetime, timezone
from sqlalchemy import DateTime, Float, Integer, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from .config import get_settings


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    username: Mapped[str] = mapped_column(String(80))
    age: Mapped[int] = mapped_column(Integer)
    weight: Mapped[float] = mapped_column(Float)
    goal: Mapped[str] = mapped_column(String(50))
    intensity: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class Plan(Base):
    __tablename__ = "plans"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    original_plan: Mapped[str] = mapped_column(Text)
    updated_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    nutrition_tip: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


settings = get_settings()
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def save_user(db: Session, data) -> User:
    user = db.scalar(select(User).where(User.user_id == data.user_id))
    if user is None:
        user = User(user_id=data.user_id, username=data.username, age=data.age, weight=data.weight,
                    goal=data.goal, intensity=data.intensity)
        db.add(user)
    else:
        user.username, user.age, user.weight = data.username, data.age, data.weight
        user.goal, user.intensity = data.goal, data.intensity
    db.commit()
    db.refresh(user)
    return user


def save_plan(db: Session, user_id: str, original_plan: str, nutrition_tip: str) -> Plan:
    plan = db.scalar(select(Plan).where(Plan.user_id == user_id))
    if plan is None:
        plan = Plan(user_id=user_id, original_plan=original_plan, nutrition_tip=nutrition_tip)
        db.add(plan)
    else:
        plan.original_plan = original_plan
        plan.updated_plan = None
        plan.nutrition_tip = nutrition_tip
        plan.updated_at = None
    db.commit()
    db.refresh(plan)
    return plan


def get_user(db: Session, user_id: str) -> User | None:
    return db.scalar(select(User).where(User.user_id == user_id))


def get_plan(db: Session, user_id: str) -> Plan | None:
    return db.scalar(select(Plan).where(Plan.user_id == user_id))


def update_plan(db: Session, user_id: str, updated_plan: str, nutrition_tip: str | None = None) -> Plan | None:
    plan = get_plan(db, user_id)
    if plan is None:
        return None
    plan.updated_plan = updated_plan
    if nutrition_tip:
        plan.nutrition_tip = nutrition_tip
    plan.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(plan)
    return plan


def get_all_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc())))


def delete_user(db: Session, user_id: str) -> bool:
    user = get_user(db, user_id)
    plan = get_plan(db, user_id)
    if user is None:
        return False
    if plan:
        db.delete(plan)
    db.delete(user)
    db.commit()
    return True
