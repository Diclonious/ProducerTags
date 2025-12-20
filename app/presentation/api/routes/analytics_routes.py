
from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from pathlib import Path
import os

from app.infrastructure.database import get_db
from app.presentation.api.dependencies.auth import get_service_container, require_admin
from app.domain.entities.User import User
from app.infrastructure.database.startup import initialize_database

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter()


@router.get("/analytics")
async def analytics(
    request: Request,
    range_q: str = "monthly",
    current_user: User = Depends(require_admin),
    container = Depends(get_service_container)
):
   

    stats = container.analytics_use_case.get_order_statistics()
    revenue_stats = container.analytics_use_case.get_revenue_statistics()


    kpis = {
        **stats,
        "revenue": revenue_stats["revenue"],
        "expected_earnings": revenue_stats["expected_earnings"]
    }


    labels, revenue_series, completed_series, cancelled_series, cancelled_revenue_series = (
        container.analytics_use_case.calculate_chart_data(range_q)
    )

    return templates.TemplateResponse(
        "analytics.html",
        {
            "request": request,
            "kpis": kpis,
            "stats": stats,
            "revenue": revenue_stats["revenue"],
            "cancelled_revenue": revenue_stats["cancelled_revenue"],
            "expected_earnings": revenue_stats["expected_earnings"],
            "labels": labels,
            "chart_labels": labels,
            "revenue_series": revenue_series,
            "chart_revenue": revenue_series,
            "completed_series": completed_series,
            "chart_completed": completed_series,
            "cancelled_series": cancelled_series,
            "chart_cancelled": cancelled_series,
            "cancelled_revenue_series": cancelled_revenue_series,
            "range": range_q
        }
    )


@router.post("/admin/reinitialize-db")
async def reinitialize_database(
    request: Request,
    secret_key: str = Query(..., description="Secret key to authorize reinitialization")
):
    """
    Reinitialize database (admin only, requires secret key)
    
    This endpoint recreates all database tables and seeds initial data.
    Use this after deleting database volumes or when you need to reset the database.
    
    Security: Requires a secret key set in REINIT_SECRET environment variable.
    """
    # Check secret key
    expected_secret = os.getenv("REINIT_SECRET", "change-me-in-production")
    if secret_key != expected_secret:
        raise HTTPException(status_code=403, detail="Invalid secret key")
    
    try:
        print("[*] Manual database reinitialization triggered via API")
        initialize_database()
        return JSONResponse(content={
            "success": True,
            "message": "Database reinitialized successfully"
        })
    except Exception as e:
        print(f"[ERROR] Database reinitialization failed: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Database reinitialization failed: {str(e)}"
        )

