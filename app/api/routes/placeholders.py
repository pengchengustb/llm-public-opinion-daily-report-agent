from fastapi import APIRouter

router = APIRouter()


@router.get("/modules")
def planned_modules() -> dict[str, list[str]]:
    return {
        "planned_modules": [
            "ingestion",
            "preprocessing",
            "llm_analysis",
            "risk_scoring",
            "report_generation",
            "evaluation",
        ]
    }

