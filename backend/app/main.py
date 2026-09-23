from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.error_handlers import register_error_handlers
from app.api.routes import router
from app.config import settings


def create_app() -> FastAPI:
    app = FastAPI(title="SearchProp Listing Search API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=["*"],
        allow_credentials=True,
    )

    app.include_router(router)
    register_error_handlers(app)

    return app


app = create_app()
