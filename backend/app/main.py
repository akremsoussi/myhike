from fastapi import FastAPI

from app.errors import install_error_handlers
from app.routers import (
    auth,
    communities,
    friends,
    health,
    moderation,
    outings,
    posts,
    refuges,
    reports,
    users,
)

app = FastAPI(
    title="Refuges API",
    docs_url="/api/docs",
    redoc_url=None,
    openapi_url="/api/openapi.json",
)

install_error_handlers(app)
app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(refuges.router, prefix="/api")
app.include_router(communities.router, prefix="/api")
app.include_router(posts.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(friends.router, prefix="/api")
app.include_router(outings.router, prefix="/api")
app.include_router(reports.router, prefix="/api")
app.include_router(moderation.router, prefix="/api")
