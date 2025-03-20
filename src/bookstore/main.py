from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from bookstore.auth.routes import router as auth_router
from bookstore.books.routes import router as book_router
from bookstore.borrowing.routes import router as borrow_router

from .middleware import LoggingMiddleware
from .config import config

app = FastAPI(
    title=config.PROJECT_NAME,
    openapi_url=f"{config.API_V1_STR}/openapi.json",
    docs_url=f"{config.API_V1_STR}/docs",
    redoc_url=f"{config.API_V1_STR}/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LoggingMiddleware)

app.include_router(auth_router, prefix=f"{config.API_V1_STR}/auth")
app.include_router(book_router, prefix=f"{config.API_V1_STR}/books")
app.include_router(borrow_router, prefix=f"{config.API_V1_STR}/borrowing")

@app.get("/")
async def root():
    return {"message": "Welcome to the Bookstore API!"}