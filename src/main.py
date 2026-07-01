"""
Application entrypoint.

Run locally with:
    uvicorn src.main:app --reload

Docs available at /docs (Swagger UI) once running.
"""

from fastapi import FastAPI

from src.api.error_handlers import register_error_handlers
from src.api.routes import admin, cart, checkout, orders, products
from src.config.settings import settings

app = FastAPI(title=settings.app_name, version=settings.app_version)

register_error_handlers(app)

app.include_router(products.router)
app.include_router(cart.router)
app.include_router(checkout.router)
app.include_router(orders.router)
app.include_router(admin.router)


@app.get("/health", tags=["Health"])
def health_check():
    """Unauthenticated liveness probe - the only route with no JWT requirement."""
    return {"status": "ok"}
