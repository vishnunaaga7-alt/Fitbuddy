from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session
import secrets

from .ai import generate_nutrition_tip_with_flash, generate_workout_gemini, plan_to_text, nutrition_to_text, update_workout_plan
from .config import get_settings
from .database import delete_user, get_all_users, get_db, get_plan, get_user, init_db, save_plan, save_user, update_plan
from .schemas import FeedbackRequest, UserInput

router = APIRouter()
templates = Jinja2Templates(directory="templates")
settings = get_settings()
security = HTTPBasic()


def admin_required(credentials: HTTPBasicCredentials = Depends(security)):
    ok_user = secrets.compare_digest(credentials.username, settings.admin_username)
    ok_pass = secrets.compare_digest(credentials.password, settings.admin_password)
    if not (ok_user and ok_pass):
        from fastapi import status
        from fastapi.responses import Response
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials",
                            headers={"WWW-Authenticate": "Basic"})
    return True


@router.on_event("startup")
def startup():
    init_db()


@router.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@router.post("/generate-workout", response_class=HTMLResponse)
def generate_workout(request: Request, username: str = Form(...), user_id: str = Form(...), age: int = Form(...),
                     weight: float = Form(...), goal: str = Form(...), intensity: str = Form(...), db: Session = Depends(get_db)):
    try:
        data = UserInput(username=username.strip(), user_id=user_id.strip(), age=age, weight=weight, goal=goal, intensity=intensity)
        user = save_user(db, data)
        plan = generate_workout_gemini(data)
        tip = generate_nutrition_tip_with_flash(data)
        plan_text = plan_to_text(plan)
        tip_text = nutrition_to_text(tip)
        save_plan(db, user.user_id, plan.model_dump_json(), tip_text)
        return templates.TemplateResponse("result.html", {"request": request, "user": user, "workout_plan": plan_text,
                                                            "nutrition_tip": tip_text, "updated": False})
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI generation failed: {exc}") from exc


@router.post("/submit-feedback", response_class=HTMLResponse)
def submit_feedback(request: Request, user_id: str = Form(...), feedback: str = Form(...), db: Session = Depends(get_db)):
    user = get_user(db, user_id.strip())
    plan_record = get_plan(db, user_id.strip())
    if user is None or plan_record is None:
        raise HTTPException(status_code=404, detail="User or plan not found")
    try:
        data = UserInput(username=user.username, user_id=user.user_id, age=user.age, weight=user.weight,
                         goal=user.goal, intensity=user.intensity)
        from .schemas import WorkoutPlan
        original_obj = WorkoutPlan.model_validate_json(plan_record.original_plan)
        revised = update_workout_plan(original_obj, data, feedback.strip())
        revised_text = plan_to_text(revised)
        update_plan(db, user.user_id, revised.model_dump_json())
        return templates.TemplateResponse("result.html", {"request": request, "user": user, "workout_plan": revised_text,
                                                            "nutrition_tip": plan_record.nutrition_tip, "updated": True})
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"AI update failed: {exc}") from exc



@router.get("/view-all-users", response_class=HTMLResponse)
def view_all_users(request: Request, _: bool = Depends(admin_required), db: Session = Depends(get_db)):
    users = get_all_users(db)
    rows = []
    for user in users:
        plan = get_plan(db, user.user_id)
        rows.append({"user": user, "plan": plan})
    return templates.TemplateResponse("all_users.html", {"request": request, "rows": rows})


@router.post("/admin/users/{user_id}/delete")
def admin_delete_user(user_id: str, _: bool = Depends(admin_required), db: Session = Depends(get_db)):
    delete_user(db, user_id)
    return RedirectResponse(url="/view-all-users", status_code=303)


@router.get("/health")
def health():
    return {"status": "ok", "app": settings.app_name}
