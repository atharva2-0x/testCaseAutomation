"""Configuration management for the test case generator."""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # LLM Configuration
    llm_provider: str = Field(default="openai", env="LLM_PROVIDER")
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    model_name: str = Field(default="gpt-4-turbo-preview", env="MODEL_NAME")
    temperature: float = Field(default=0.2, env="TEMPERATURE")
    max_tokens: int = Field(default=4000, env="MAX_TOKENS")
    model_type: str = Field(default="llama4_text", env="MODEL_TYPE")

    # Vector DB Configuration
    vector_db_type: str = Field(default="faiss", env="VECTOR_DB_TYPE")
    vector_db_path: Path = Field(default=Path("./data/vector_db"), env="VECTOR_DB_PATH")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    embedding_dim: int = Field(default=384, env="EMBEDDING_DIM")
    vectorized_files_tracker: Path = Field(
        default=Path("./data/.vectorized_files.json"), 
        env="VECTORIZED_FILES_TRACKER"
    )
    
    # Input Paths
    input_html_path: Optional[Path] = Field(default=None, env="INPUT_HTML_PATH")
    input_scenarios_path: Optional[Path] = Field(default=None, env="INPUT_SCENARIOS_PATH")
    existing_feature_path: Optional[Path] = Field(default=None, env="EXISTING_FEATURE_PATH")
    existing_stepdef_path: Optional[Path] = Field(default=None, env="EXISTING_STEPDEF_PATH")
    existing_pageobj_path: Optional[Path] = Field(default=None, env="EXISTING_PAGEOBJ_PATH")
    
    # Output Configuration
    output_dir: Path = Field(default=Path("./output"), env="OUTPUT_DIR")
    output_feature_file: str = Field(default="NewTests.feature", env="OUTPUT_FEATURE_FILE")
    output_stepdef_file: str = Field(default="NewStepDefinitions.java", env="OUTPUT_STEPDEF_FILE")
    output_pageobj_file: str = Field(default="NewPageObjects.java", env="OUTPUT_PAGEOBJ_FILE")
    
    # Agent Configuration
    max_retries: int = Field(default=3, env="MAX_RETRIES")
    orchestrator_max_iterations: int = Field(default=5, env="ORCHESTRATOR_MAX_ITERATIONS")
    validation_strict_mode: bool = Field(default=True, env="VALIDATION_STRICT_MODE")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: Path = Field(default=Path("./logs/app.log"), env="LOG_FILE")
    
    # Performance
    batch_size: int = Field(default=10, env="BATCH_SIZE")
    top_k_retrieval: int = Field(default=5, env="TOP_K_RETRIEVAL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create necessary directories
        self.vector_db_path.parent.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.vectorized_files_tracker.parent.mkdir(parents=True, exist_ok=True)
    
    def get_api_key(self) -> str:
        """Get the appropriate API key based on provider."""
        if self.llm_provider == "openai":
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY is required when using OpenAI provider")
            return self.openai_api_key
        elif self.llm_provider == "anthropic":
            if not self.anthropic_api_key:
                raise ValueError("ANTHROPIC_API_KEY is required when using Anthropic provider")
            return self.anthropic_api_key
        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")


# Global settings instance
settings = Settings()


# Constants
SUPPORTED_HTML_TAGS = [
    "button", "a", "input", "select", "textarea", 
    "form", "label", "div", "span"
]

ACTIONABLE_ATTRIBUTES = [
    "onclick", "onsubmit", "onchange", "role", 
    "aria-label", "data-testid", "data-action"
]

GHERKIN_KEYWORDS = [
    "Feature", "Background", "Scenario", "Scenario Outline",
    "Given", "When", "Then", "And", "But", "Examples"
]

JAVA_ANNOTATIONS = [
    "@Given", "@When", "@Then", "@And", "@But"
]

# Selenium action patterns
SELENIUM_ACTIONS = {
    "click": "element.click()",
    "sendKeys": "element.sendKeys(text)",
    "clear": "element.clear()",
    "submit": "element.submit()",
    "getText": "element.getText()",
    "isDisplayed": "element.isDisplayed()",
    "isEnabled": "element.isEnabled()",
    "getAttribute": "element.getAttribute(attributeName)"
}