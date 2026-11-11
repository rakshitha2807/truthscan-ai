
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="TruthScan AI API",
    description="Backend API for TruthScan AI",
    version="1.0.0"
)

# Development CORS configuration
# Restrict this to your actual frontend origin before deployment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "project": "TruthScan AI",
        "message": "Backend is running",
        "status": "success"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "frontend_integration": "ready",
        "evidence_module": "available",
        "forensic_module": "pending",
        "cs_module": "pending"
    }
