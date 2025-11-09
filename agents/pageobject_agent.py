# ============================================================================
# FILE: agents/pageobject_agent.py
# ============================================================================
"""Page Object Agent - Generates Selenium page object classes."""
import json
import re
from typing import Dict, List, Any
from core.logger import log, log_agent_action


class PageObjectAgent:
    """Agent responsible for generating Selenium page object classes."""
    
    def __init__(self, llm_client, vectorizer):
        self.llm_client = llm_client
        self.vectorizer = vectorizer
        self.prompt_template = llm_client.load_prompt_template("pageobject_prompt")
    
    def generate(
        self,
        stepdef_content: str,
        html_elements: List[Dict],
        existing_pageobjects: Dict = None,
        feedback: List[str] = None
    ) -> Dict[str, Any]:
        """Generate page object Java class."""
        log_agent_action("PageObjectAgent", "Generating page objects")
        
        # Extract required methods from step definitions
        required_methods = self._extract_required_methods(stepdef_content)
        
        # Get existing page object methods to reuse
        existing_methods_text = self._get_existing_methods_context()
        
        # Format HTML elements with selectors
        html_context = self._format_html_elements_detailed(html_elements)
        
        # Build prompt
        prompt = self.llm_client.format_prompt(
            self.prompt_template,
            html_elements=html_context,
            required_methods="\n".join(required_methods),
            existing_methods=existing_methods_text
        )
        
        # Add feedback if retrying
        if feedback:
            prompt += f"\n\n## PREVIOUS ATTEMPT ERRORS:\n"
            prompt += "\n".join(feedback)
            prompt += "\n\nPlease fix these errors and regenerate."
        
        # Generate
        pageobj_content = self.llm_client.generate(prompt)
        
        log_agent_action("PageObjectAgent", f"Generated page object ({len(pageobj_content)} chars)")
        
        return {
            'content': pageobj_content,
            'metadata': {
                'methods_count': len(required_methods),
                'elements_count': len(html_elements)
            }
        }
    
    def _extract_required_methods(self, stepdef_content: str) -> List[str]:
        """Extract method calls from step definitions."""
        # Pattern: someObject.methodName(...)
        pattern = r'(\w+)\.(\w+)\s*\('
        matches = re.findall(pattern, stepdef_content)
        
        methods = set()
        for obj, method in matches:
            if obj not in ['driver', 'Assert', 'System', 'String']:
                methods.add(method)
        
        return list(methods)
    
    def _get_existing_methods_context(self) -> str:
        """Retrieve existing page object methods from vector DB."""
        try:
            results = self.vectorizer.search(
                "page object selenium method",
                top_k=15,
                filter_type="pageobject"
            )
            
            if not results:
                return "No existing page object methods found."
            
            methods = []
            for result in results:
                full_method = result['metadata'].get('full_method', '')
                if full_method:
                    # Escape braces in Java code to prevent template formatting errors
                    escaped_method = full_method.replace('{', '{{').replace('}', '}}')
                    methods.append(escaped_method)
            
            return "\n\n".join(methods[:10])
        except Exception as e:
            log.error(f"Failed to retrieve existing methods: {e}")
            return "No existing page object methods found."
    
    def _format_html_elements_detailed(self, html_elements: List[Dict]) -> str:
        """Format HTML elements with full selector information."""
        if not html_elements:
            return "No HTML elements available."
        
        formatted = []
        for elem in html_elements[:25]:
            selector_info = elem.get('preferred_selector', {})
            formatted.append(f"""
Element: {elem['type']}
  Text: {elem['text']}
  ID: {elem.get('id', 'N/A')}
  Selector Strategy: {selector_info.get('strategy', 'N/A')}
  Selector Value: {selector_info.get('value', 'N/A')}
  Selenium Code: {selector_info.get('method', 'N/A')}
""")
        
        return "\n".join(formatted)