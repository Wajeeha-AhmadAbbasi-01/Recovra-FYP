from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.modules.auth.router import router as auth_router
from app.modules.customers.router import router as customers_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.imports.router import router as imports_router
from app.modules.invoices.router import router as invoices_router
from app.modules.team.router import router as team_router

settings = get_settings()

app = FastAPI(title="Recovra API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(team_router)
app.include_router(customers_router)
app.include_router(invoices_router)
app.include_router(imports_router)
app.include_router(dashboard_router)


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok", "environment": settings.app_env}