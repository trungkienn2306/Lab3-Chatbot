import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    MODEL_NAME = "gemini-2.5-flash"
    TEMPERATURE = 0.1
    TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
    USE_TOOLS = os.getenv("USE_TOOLS", "True").lower() == "true"

settings = Settings()