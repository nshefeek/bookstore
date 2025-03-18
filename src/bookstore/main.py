from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bookstore.auth.router import router as auth_router
from bookstore.books.router import router as book_router
from .config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(book_router, prefix=f"{settings.API_V1_STR}/books", tags=["books"])

@app.get("/")
async def root():
    return {"message": "Welcome to the Bookstore API!"}