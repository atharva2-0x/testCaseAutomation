"""HTML parsing to extract actionable UI elements."""
import json
from typing import List, Dict, Any
from bs4 import BeautifulSoup, Tag
from core.config import SUPPORTED_HTML_TAGS, ACTIONABLE_ATTRIBUTES
from core.logger import log


class HTMLParser:
    """Parse HTML and extract actionable elements with selectors."""
    
    def __init__(self, html_content: str, source_name: str = "page.html"):
        self.html_content = html_content
        self.source_name = source_name
        self.soup = BeautifulSoup(html_content, 'lxml')
        self.elements = []
    
    def parse(self) -> List[Dict[str, Any]]:
        """Parse HTML and extract all actionable elements."""
        log.info(f"Parsing HTML from {self.source_name}")
        
        # Extract all relevant tags
        for tag_name in SUPPORTED_HTML_TAGS:
            elements = self.soup.find_all(tag_name)
            for element in elements:
                if self._is_actionable(element):
                    parsed_elem = self._parse_element(element)
                    if parsed_elem:
                        self.elements.append(parsed_elem)
        
        log.info(f"Extracted {len(self.elements)} actionable elements")
        return self.elements
    
    def _is_actionable(self, element: Tag) -> bool:
        """Determine if element is actionable (clickable, input, etc)."""
        tag_name = element.name.lower()
        
        # Buttons and links are always actionable
        if tag_name in ['button', 'a', 'input', 'select', 'textarea']:
            return True
        
        # Check for actionable attributes
        for attr in ACTIONABLE_ATTRIBUTES:
            if element.get(attr):
                return True
        
        # Check for form-related elements
        if element.find_parent('form'):
            return True
        
        return False
    
    def _parse_element(self, element: Tag) -> Dict[str, Any]:
        """Parse a single element into structured JSON."""
        elem_data = {
            "type": element.name.lower(),
            "text": self._get_element_text(element),
            "id": element.get('id', ''),
            "name": element.get('name', ''),
            "classes": element.get('class', []),
            "placeholder": element.get('placeholder', ''),
            "aria_label": element.get('aria-label', ''),
            "data_testid": element.get('data-testid', ''),
            "role": element.get('role', ''),
            "href": element.get('href', ''),
            "type_attr": element.get('type', ''),
            "xpath": self._generate_xpath(element),
            "css_selector": self._generate_css_selector(element),
            "context": self._get_context(element),
            "source": self.source_name
        }
        
        # Generate best selector strategy
        elem_data["preferred_selector"] = self._get_preferred_selector(elem_data)
        
        return elem_data
    
    def _get_element_text(self, element: Tag) -> str:
        """Extract visible text from element."""
        # For inputs, use placeholder or label
        if element.name == 'input':
            return element.get('placeholder', element.get('aria-label', ''))
        
        # Get direct text content
        text = element.get_text(strip=True)
        
        # If no text, try to find associated label
        if not text and element.get('id'):
            label = self.soup.find('label', {'for': element.get('id')})
            if label:
                text = label.get_text(strip=True)
        
        return text[:100]  # Limit length
    
    def _generate_xpath(self, element: Tag) -> str:
        """Generate XPath for element."""
        # Prefer ID-based XPath
        if element.get('id'):
            return f"//{element.name}[@id='{element.get('id')}']"
        
        # Try name attribute
        if element.get('name'):
            return f"//{element.name}[@name='{element.get('name')}']"
        
        # Use class-based XPath
        classes = element.get('class', [])
        if classes:
            class_str = ' and '.join([f"contains(@class, '{c}')" for c in classes[:2]])
            return f"//{element.name}[{class_str}]"
        
        # Fallback: use text content
        text = self._get_element_text(element)
        if text:
            return f"//{element.name}[contains(text(), '{text[:30]}')]"
        
        # Last resort: position-based
        siblings = [s for s in element.parent.children if isinstance(s, Tag) and s.name == element.name]
        position = siblings.index(element) + 1
        parent_xpath = self._generate_xpath(element.parent) if element.parent.name != '[document]' else ''
        return f"{parent_xpath}/{element.name}[{position}]"
    
    def _generate_css_selector(self, element: Tag) -> str:
        """Generate CSS selector for element."""
        # Prefer ID
        if element.get('id'):
            return f"#{element.get('id')}"
        
        # Try data-testid
        if element.get('data-testid'):
            return f"[data-testid='{element.get('data-testid')}']"
        
        # Use classes
        classes = element.get('class', [])
        if classes:
            return f"{element.name}.{'.'.join(classes[:2])}"
        
        # Use name attribute
        if element.get('name'):
            return f"{element.name}[name='{element.get('name')}']"
        
        # Fallback
        return element.name
    
    def _get_preferred_selector(self, elem_data: Dict) -> Dict[str, str]:
        """Determine the best selector strategy for Selenium."""
        selectors = {}
        
        # Priority order: data-testid > id > name > aria-label > text > class > xpath
        if elem_data['data_testid']:
            selectors['strategy'] = 'cssSelector'
            selectors['value'] = f"[data-testid='{elem_data['data_testid']}']"
            selectors['method'] = f"driver.findElement(By.cssSelector(\"[data-testid='{elem_data['data_testid']}']\")"
        
        elif elem_data['id']:
            selectors['strategy'] = 'id'
            selectors['value'] = elem_data['id']
            selectors['method'] = f"driver.findElement(By.id(\"{elem_data['id']}\"))"
        
        elif elem_data['name']:
            selectors['strategy'] = 'name'
            selectors['value'] = elem_data['name']
            selectors['method'] = f"driver.findElement(By.name(\"{elem_data['name']}\"))"
        
        elif elem_data['aria_label']:
            selectors['strategy'] = 'cssSelector'
            selectors['value'] = f"[aria-label='{elem_data['aria_label']}']"
            selectors['method'] = f"driver.findElement(By.cssSelector(\"[aria-label='{elem_data['aria_label']}']\")"
        
        elif elem_data['text'] and elem_data['type'] in ['button', 'a']:
            selectors['strategy'] = 'linkText' if elem_data['type'] == 'a' else 'xpath'
            selectors['value'] = elem_data['text'] if elem_data['type'] == 'a' else f"//{elem_data['type']}[contains(text(), '{elem_data['text']}')]"
            if elem_data['type'] == 'a':
                selectors['method'] = f"driver.findElement(By.linkText(\"{elem_data['text']}\"))"
            else:
                selectors['method'] = f"driver.findElement(By.xpath(\"{selectors['value']}\"))"
        
        elif elem_data['classes']:
            selectors['strategy'] = 'cssSelector'
            selectors['value'] = elem_data['css_selector']
            selectors['method'] = f"driver.findElement(By.cssSelector(\"{elem_data['css_selector']}\"))"
        
        else:
            selectors['strategy'] = 'xpath'
            selectors['value'] = elem_data['xpath']
            selectors['method'] = f"driver.findElement(By.xpath(\"{elem_data['xpath']}\"))"
        
        return selectors
    
    def _get_context(self, element: Tag, window=50) -> str:
        """Get surrounding text context for better understanding."""
        # Get parent's text
        parent = element.parent
        if parent:
            parent_text = parent.get_text(strip=True)
            # Find element's position in parent text
            elem_text = self._get_element_text(element)
            if elem_text in parent_text:
                idx = parent_text.find(elem_text)
                start = max(0, idx - window)
                end = min(len(parent_text), idx + len(elem_text) + window)
                return parent_text[start:end]
        
        return ""
    
    def to_json_documents(self) -> List[str]:
        """Convert parsed elements to JSON document strings for vectorization."""
        docs = []
        for elem in self.elements:
            # Create a searchable document
            doc = {
                "element": elem,
                "searchable_text": self._create_searchable_text(elem)
            }
            docs.append(json.dumps(doc, indent=2))
        return docs
    
    def _create_searchable_text(self, elem: Dict) -> str:
        """Create searchable text representation of element."""
        parts = [
            f"Element Type: {elem['type']}",
            f"Text: {elem['text']}" if elem['text'] else "",
            f"ID: {elem['id']}" if elem['id'] else "",
            f"Name: {elem['name']}" if elem['name'] else "",
            f"Placeholder: {elem['placeholder']}" if elem['placeholder'] else "",
            f"ARIA Label: {elem['aria_label']}" if elem['aria_label'] else "",
            f"Context: {elem['context']}" if elem['context'] else "",
        ]
        return " | ".join([p for p in parts if p])