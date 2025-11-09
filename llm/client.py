"""LLM client wrapper supporting OpenAI, Anthropic, and FiservAI."""
from typing import List, Dict, Optional
from pathlib import Path
import openai
import anthropic
from fiservai import FiservAI
from tenacity import retry, stop_after_attempt, wait_exponential
from core.config import settings
from core.logger import log


class LLMClient:
    """Unified interface for LLM providers."""
    
    def __init__(self):
        self.provider = settings.llm_provider
        self.model = settings.model_name
        self.temperature = settings.temperature
        self.max_tokens = settings.max_tokens
        
        # Initialize appropriate client
        if self.provider == "openai":
            # OpenAI v1.0+ doesn't accept 'proxies' as a parameter
            # Proxies should be set via HTTP_PROXY/HTTPS_PROXY environment variables
            api_key = settings.get_api_key()
            # Explicitly pass only supported parameters
            self.client = openai.OpenAI(api_key=api_key)
        elif self.provider == "anthropic":
            self.client = anthropic.Anthropic(api_key=settings.get_api_key())
        elif self.provider == "fiservai":
            api_key, api_secret, base_url = settings.get_fiservai_credentials()
            self.client = FiservAI.FiservAI(api_key, api_secret, base_url)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
        
        log.info(f"Initialized LLM client: {self.provider} with model {self.model}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        Generate completion from LLM.
        
        Args:
            prompt: User prompt
            system_prompt: System/instruction prompt
        
        Returns:
            Generated text
        """
        try:
            if self.provider == "openai":
                return self._generate_openai(prompt, system_prompt)
            elif self.provider == "anthropic":
                return self._generate_anthropic(prompt, system_prompt)
            elif self.provider == "fiservai":
                return self._generate_fiservai(prompt, system_prompt)
        except Exception as e:
            log.error(f"LLM generation failed: {e}")
            raise
    
    def _generate_openai(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate using OpenAI API."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_anthropic(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate using Anthropic API."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_prompt if system_prompt else "",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        return message.content[0].text.strip()
    
    def _generate_fiservai(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate using FiservAI API."""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat_completion(messages=messages)
        
        return response.choice[0].message.content.strip()
    
    def load_prompt_template(self, template_name: str) -> str:
        """Load prompt template from file."""
        template_path = Path(__file__).parent / "prompts" / f"{template_name}.txt"
        
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            log.error(f"Failed to load prompt template {template_name}: {e}")
            raise
    
    def format_prompt(self, template: str, **kwargs) -> str:
        """Format prompt template with variables."""
        try:
            return template.format(**kwargs)
        except KeyError as e:
            log.error(f"Missing template variable: {e}")
            raise