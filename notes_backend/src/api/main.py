from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.config import get_settings
from src.api.routers.auth import router as auth_router
from src.api.routers.notes import router as notes_router
from src.api.routers.tags import router as tags_router

settings = get_settings()

openapi_tags = [
    {"name": "health", "description": "Health checks"},
    {"name": "auth", "description": "Authentication (signup/login/me) using JWT Bearer tokens"},
    {"name": "notes", "description": "Notes CRUD, tagging, search (all scoped per authenticated user)"},
    {"name": "tags", "description": "Tag operations (scoped per authenticated user)"},
]

app = FastAPI(
    title=settings.app_name,
    description=(
        "Secure Notes backend API.\n\n"
        "Authentication: use `Authorization: Bearer <access_token>` header.\n"
        "All notes/tags are private and scoped to the authenticated user."
    ),
    version="1.0.0",
    openapi_tags=openapi_tags,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"], summary="Health check")
def health_check():
    """
    Health check endpoint.

    Returns a simple message when the API server is running.
    """
    return {"message": "Healthy"}


app.include_router(auth_router)
app.include_router(notes_router)
app.include_router(tags_router)
