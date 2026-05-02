from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.routes import ddr_route

app = FastAPI(
    title="DDR AI System",
    description="AI-powered DDR report generation from inspection + thermal reports",
    version="1.0.0"
)

# Allow Streamlit / local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/")
def root():
    return {"message": "DDR AI System is running 🚀"}

# Register routes
app.include_router(ddr_route.router, prefix="/ddr", tags=["DDR"])

app.mount("/images", StaticFiles(directory="backend/data/raw/images"), name="images")