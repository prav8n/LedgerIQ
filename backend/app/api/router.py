"""Top-level API router that mounts every module router.

``main.py`` includes this single router under the configured API prefix
(e.g. ``/api/v1``), so all module endpoints get a consistent base path.
"""

from fastapi import APIRouter

from app.api.routes import (
    analytics,
    auth,
    budgets,
    credit_cards,
    dashboard,
    emis,
    expenses,
    goals,
    imports,
    income,
    insights,
    investments,
    net_worth,
    notifications,
    subscriptions,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(income.router)
api_router.include_router(expenses.router)
api_router.include_router(credit_cards.router)
api_router.include_router(budgets.router)
api_router.include_router(goals.router)
api_router.include_router(investments.router)
api_router.include_router(subscriptions.router)
api_router.include_router(emis.router)
api_router.include_router(net_worth.router)
api_router.include_router(notifications.router)
api_router.include_router(dashboard.router)
api_router.include_router(analytics.router)
api_router.include_router(insights.router)
api_router.include_router(imports.router)
