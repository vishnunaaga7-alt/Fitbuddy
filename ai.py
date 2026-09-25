import json
from .config import get_settings
from .schemas import NutritionTip, UserInput, WorkoutPlan

settings = get_settings()


def _client():
    from google import genai
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured. Add it to .env before generating a plan.")
    return genai.Client(api_key=settings.gemini_api_key)


def _generate(model: str, prompt: str, schema):
    client = _client()
    from google.genai import types
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema,
            temperature=0.6,
        ),
    )
    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")
    return response.text


def generate_workout_gemini(user: UserInput) -> WorkoutPlan:
    prompt = f"""
You are FitBuddy, a careful fitness-planning assistant. Create a practical 7-day workout plan.
User: name={user.username}, age={user.age}, weight_kg={user.weight}, goal={user.goal}, intensity={user.intensity}.
Return exactly 7 days. Each day must have a focus, warm-up, 2-6 exercises with sets/reps-or-duration/rest,
and a cooldown. Include sensible rest/recovery. Avoid diagnosing conditions or making medical claims.
For a minor (age under 18), keep the plan age-appropriate, avoid maximal loads, and emphasize adult/professional supervision.
The plan is general wellness information, not medical advice.
"""
    return WorkoutPlan.model_validate_json(_generate(settings.gemini_workout_model, prompt, WorkoutPlan))


def update_workout_plan(original_plan: WorkoutPlan, user: UserInput, feedback: str) -> WorkoutPlan:
    prompt = f"""
Revise the existing FitBuddy 7-day workout plan using the user's feedback.
User goal={user.goal}; intensity={user.intensity}; age={user.age}; weight_kg={user.weight}.
Feedback: {feedback}
Existing plan JSON:
{original_plan.model_dump_json(indent=2)}
Preserve the user's goal and intensity unless the feedback explicitly requests a change. Return exactly 7 days.
Do not diagnose conditions or provide medical treatment. Keep safety notes.
"""
    return WorkoutPlan.model_validate_json(_generate(settings.gemini_workout_model, prompt, WorkoutPlan))


def generate_nutrition_tip_with_flash(user: UserInput) -> NutritionTip:
    prompt = f"""
Give one concise, practical nutrition and recovery suggestion for a FitBuddy user.
Goal={user.goal}; intensity={user.intensity}; age={user.age}.
Avoid individualized medical or disease treatment advice, extreme dieting, or unsafe supplement advice.
Mention hydration or recovery when relevant. Keep the response concise and actionable.
"""
    return NutritionTip.model_validate_json(_generate(settings.gemini_tip_model, prompt, NutritionTip))


def plan_to_text(plan: WorkoutPlan) -> str:
    lines = [plan.summary, ""]
    for day in plan.days:
        lines.append(f"{day.day} — {day.focus}")
        lines.append(f"Warm-up: {day.warmup}")
        for ex in day.exercises:
            lines.append(f"• {ex.name}: {ex.sets} sets × {ex.reps_or_duration}; rest {ex.rest}")
        lines.append(f"Cooldown: {day.cooldown}")
        lines.append("")
    lines.append("Safety notes:")
    lines.extend(f"• {note}" for note in plan.safety_notes)
    return "\n".join(lines)


def nutrition_to_text(tip: NutritionTip) -> str:
    return f"{tip.tip}\n\nRecovery: {tip.recovery_note}"
