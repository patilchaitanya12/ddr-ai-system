import os
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()


class Settings(BaseModel):
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")


settings = Settings()