import django_setup  # noqa: F401  (must run before importing Django models)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import accounts, papers

app = FastAPI(title="Teacher/Student Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(accounts.router)
app.include_router(papers.router)