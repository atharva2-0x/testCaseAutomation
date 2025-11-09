# ============================================================================
# FILE: agents/feature_agent.py
# ============================================================================
"""Feature Agent - Generates Cucumber .feature files."""
import json
from typing import Dict, List, Any
from core.logger import log, log_agent_action
from core.utils import truncate_text


class FeatureAgent:
    """Agent responsible for generating Cucumber feature files."""
    
    def __init__(self, llm_client, vectorizer):
        self.llm_client = llm_client
        self.vectorizer = vectorizer
        self.prompt_template = llm_client.load_prompt_template("feature_prompt")
    
    def generate(
        self,
        scenarios: str,
        html_elements: List[Dict],
        existing_feature: Dict = None,
        feedback: List[str] = None
    ) -> Dict[str, Any]:
        """Generate feature file content."""
        log_agent_action("FeatureAgent", "Generating .feature file")
        
        # Retrieve relevant existing steps from vector DB
        existing_steps_text = self._get_existing_steps_context()
        
        # Format HTML elements for context
        html_context = self._format_html_elements(html_elements)
        
        # Build prompt
        prompt = self.llm_client.format_prompt(
            self.prompt_template,
            scenarios=scenarios,
            html_elements=html_context,
            existing_steps=existing_steps_text
        )
        
        # Add feedback if retrying
        if feedback:
            prompt += f"\n\n## PREVIOUS ATTEMPT ERRORS:\n"
            prompt += "\n".join(feedback)
            prompt += "\n\nPlease fix these errors and regenerate."
        
        # Generate
        feature_content = self.llm_client.generate(prompt)
        
        log_agent_action("FeatureAgent", f"Generated feature file ({len(feature_content)} chars)")
        
        return {
            'content': feature_content,
            'metadata': {
                'scenarios_count': scenarios.count('Scenario:'),
                'used_existing_steps': existing_steps_text != "No existing steps found."
            }
        }
    
    def _get_existing_steps_context(self) -> str:
        """Retrieve existing step patterns from vector DB."""
        try:
            results = self.vectorizer.search(
                "cucumber step definition",
                top_k=20,
                filter_type="feature"
            )
            
            if not results:
                return "No existing steps found."
            
            steps = set()
            for result in results:
                if result['metadata'].get('is_unique_step'):
                    steps.add(result['text'])
            
            return "\n".join(sorted(steps)[:15])  # Return top 15 unique steps
        except Exception as e:
            log.error(f"Failed to retrieve existing steps: {e}")
            return "No existing steps found."
    
    def _format_html_elements(self, html_elements: List[Dict]) -> str:
        """Format HTML elements for prompt context."""
        if not html_elements:
            return "No HTML elements available."
        
        formatted = []
        for elem in html_elements[:30]:  # Limit to avoid token overflow
            formatted.append(f"- {elem['type']}: '{elem['text']}' (id={elem.get('id', 'N/A')})")
        
        return "\n".join(formatted)
