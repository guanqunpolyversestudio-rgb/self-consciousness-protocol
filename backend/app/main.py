"""Self-Consciousness Alignment Protocol — FastAPI Backend."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import alignment, credits, gameplays, handshake, onboarding, scoring, tasks, tools, visualization

app = FastAPI(
    title="Self-Consciousness Alignment API",
    description="Backend for the Self-Consciousness Alignment Protocol.",
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(gameplays.router, prefix="/api/v1/gameplays", tags=["gameplays"])
app.include_router(scoring.router, prefix="/api/v1/scoring", tags=["scoring"])
app.include_router(tasks.router, prefix="/api/v1/tasks", tags=["tasks"])
app.include_router(credits.router, prefix="/api/v1/credits", tags=["credits"])
app.include_router(onboarding.router, prefix="/api/v1/onboarding", tags=["onboarding"])
app.include_router(handshake.router, prefix="/api/v1/handshake", tags=["handshake"])
app.include_router(alignment.router, prefix="/api/v1/alignment", tags=["alignment"])
app.include_router(tools.router, prefix="/api/v1/tools", tags=["tools"])
app.include_router(visualization.router, prefix="/api/v1/viz", tags=["visualization"])


@app.get("/")
def root():
    return {
        "name": "Self-Consciousness Alignment API",
        "version": "0.4.0",
        "endpoints": {
            "gameplays": "/api/v1/gameplays",
            "scoring": "/api/v1/scoring",
            "tasks": "/api/v1/tasks",
            "credits": "/api/v1/credits",
            "onboarding": "/api/v1/onboarding",
            "handshake": "/api/v1/handshake",
            "alignment": "/api/v1/alignment",
            "tools": "/api/v1/tools",
        },
        "docs": "/docs",
    }


@app.get("/health")
def health():
    return {"status": "ok"}
