# ============================================================================
# FILE: agents/stepdef_agent.py
# ============================================================================
"""Step Definition Agent - Generates Java step definition classes."""
import json
import re
from typing import Dict, List, Any
from core.logger import log, log_agent_action
from core.utils import extract_step_text, normalize_step_text


class StepDefinitionAgent:
    """Agent responsible for generating Java step definition classes."""
    
    def __init__(self, llm_client, vectorizer):
        self.llm_client = llm_client
        self.vectorizer = vectorizer
        self.prompt_template = llm_client.load_prompt_template("stepdef_prompt")
    
    def generate(
        self,
        feature_content: str,
        html_elements: List[Dict],
        existing_stepdefs: Dict = None,
        existing_pageobjects: Dict = None,
        feedback: List[str] = None
    ) -> Dict[str, Any]:
        """Generate step definition Java class."""
        log_agent_action("StepDefinitionAgent", "Generating step definitions")
        
        # Extract steps from feature file
        feature_steps_raw = self._extract_steps_from_feature(feature_content)
        
        # Extract step text (remove Given/When/Then keywords) and normalize
        feature_steps = []
        for step_line in feature_steps_raw:
            step_text = extract_step_text(step_line)
            if step_text:
                feature_steps.append(step_text)
        
        log.info(f"Extracted {len(feature_steps)} unique steps from feature file")
        if len(feature_steps) > 0:
            log.debug(f"Steps to implement: {feature_steps[:5]}{'...' if len(feature_steps) > 5 else ''}")
        
        # Get existing step definitions to reuse
        existing_stepdefs_text = self._get_existing_stepdefs_context()
        
        # Get available page object methods
        pageobj_methods = self._get_pageobject_methods_context(existing_pageobjects)
        
        # Format HTML elements
        html_context = self._format_html_elements(html_elements)
        
        # Escape braces in inputs to prevent template formatting errors
        # Python's .format() interprets {variable} as template variables
        def escape_braces(text: str) -> str:
            """Escape braces in text to prevent template formatting errors."""
            return text.replace('{', '{{').replace('}', '}}')
        
        # Format feature steps with numbering for clarity
        feature_steps_formatted = []
        for i, step in enumerate(feature_steps, 1):
            feature_steps_formatted.append(f"{i}. {step}")
        
        feature_steps_escaped = "\n".join(escape_braces(step) for step in feature_steps_formatted)
        html_context_escaped = escape_braces(html_context)
        pageobj_methods_escaped = escape_braces(pageobj_methods) if pageobj_methods else pageobj_methods
        
        # Build prompt
        prompt = self.llm_client.format_prompt(
            self.prompt_template,
            feature_steps=feature_steps_escaped,
            existing_stepdefs=existing_stepdefs_text,  # Already escaped in _get_existing_stepdefs_context
            page_object_methods=pageobj_methods_escaped,
            html_elements=html_context_escaped
        )
        
        # Add explicit step count requirement
        prompt += f"\n\n## CRITICAL REQUIREMENT:\n"
        prompt += f"You MUST generate step definitions for ALL {len(feature_steps)} steps listed above.\n"
        prompt += f"Each step must have a corresponding @Given/@When/@Then annotation with matching text.\n"
        prompt += f"Count your generated step definitions - you should have at least {len(feature_steps)} methods.\n"
        
        # Add feedback if retrying
        if feedback:
            prompt += f"\n\n## PREVIOUS ATTEMPT ERRORS:\n"
            prompt += "\n".join(feedback)
            prompt += "\n\nPlease fix these errors and regenerate. Pay special attention to generating ALL required step definitions."
        
        # Generate
        stepdef_content = self.llm_client.generate(prompt)
        
        log_agent_action("StepDefinitionAgent", f"Generated step definitions ({len(stepdef_content)} chars)")
        
        return {
            'content': stepdef_content,
            'metadata': {
                'steps_count': len(feature_steps),
                'reused_existing': existing_stepdefs_text != "No existing step definitions found."
            }
        }
    
    def _extract_steps_from_feature(self, feature_content: str) -> List[str]:
        """Extract step lines from feature file."""
        steps = []
        for line in feature_content.split('\n'):
            stripped = line.strip()
            if stripped and stripped.split()[0] in ['Given', 'When', 'Then', 'And', 'But']:
                steps.append(stripped)
        return list(dict.fromkeys(steps))  # Remove duplicates while preserving order
    
    def _get_existing_stepdefs_context(self) -> str:
        """Retrieve existing step definitions from vector DB."""
        try:
            results = self.vectorizer.search(
                "java step definition method",
                top_k=15,
                filter_type="stepdef"
            )
            
            if not results:
                return "No existing step definitions found."
            
            stepdefs = []
            for result in results:
                full_def = result['metadata'].get('full_definition', '')
                if full_def:
                    # Escape braces in Java code to prevent template formatting errors
                    escaped_def = full_def.replace('{', '{{').replace('}', '}}')
                    stepdefs.append(escaped_def)
            
            return "\n\n".join(stepdefs[:10])
        except Exception as e:
            log.error(f"Failed to retrieve existing stepdefs: {e}")
            return "No existing step definitions found."
    
    def _get_pageobject_methods_context(self, existing_pageobjects: Dict = None) -> str:
        """Get available page object methods."""
        if existing_pageobjects and existing_pageobjects.get('methods'):
            methods = []
            for method in existing_pageobjects['methods'][:15]:
                methods.append(f"- {method['name']}()")
            return "\n".join(methods)
        return "Page object methods will be generated by PageObjectAgent."
    
    def _format_html_elements(self, html_elements: List[Dict]) -> str:
        """Format HTML elements for context."""
        if not html_elements:
            return "No HTML elements available."
        
        formatted = []
        for elem in html_elements[:20]:
            formatted.append(f"- {elem['type']}: '{elem['text']}' (selector: {elem.get('preferred_selector', {}).get('strategy', 'N/A')})")
        
        return "\n".join(formatted)
