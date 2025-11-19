"""Analytics routes (Admin only)"""
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.infrastructure.database import get_db
from app.presentation.api.dependencies.auth import get_service_container, require_admin
from app.domain.entities.User import User

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
    """Show analytics dashboard"""
    # Get statistics
    stats = container.analytics_use_case.get_order_statistics()
    revenue_stats = container.analytics_use_case.get_revenue_statistics()
    
    # Combine stats and revenue_stats into kpis for template
    kpis = {
        **stats,
        "revenue": revenue_stats["revenue"],
        "expected_earnings": revenue_stats["expected_earnings"]
    }
    
    # Get chart data
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

