
# ============================================================================
# FILE: validation/cross_validator.py
# ============================================================================
"""Cross-file validation to ensure consistency across feature, stepdef, and page object files."""
import re
from typing import Tuple, List, Dict
from core.logger import log, log_validation_result
from core.utils import extract_step_text, normalize_step_text, extract_annotation_text


class CrossValidator:
    """Validates consistency across all three generated files."""
    
    def validate(
        self,
        feature_content: str,
        stepdef_content: str,
        pageobject_content: str,
        html_elements: List[Dict]
    ) -> Tuple[bool, List[str]]:
        """
        Perform cross-file validation.
        
        Checks:
        1. All feature steps have corresponding step definitions
        2. All step definitions call page object methods
        3. Page object has required methods
        4. Selectors reference actual HTML elements
        """
        errors = []
        
        # Extract components
        feature_steps = self._extract_feature_steps(feature_content)
        stepdef_annotations = self._extract_stepdef_annotations(stepdef_content)
        stepdef_method_calls = self._extract_method_calls(stepdef_content)
        pageobj_methods = self._extract_pageobj_methods(pageobject_content)
        
        log.info(f"Cross-validation: {len(feature_steps)} steps, {len(stepdef_annotations)} definitions, {len(pageobj_methods)} methods")
        
        # Validation 1: Feature steps have step definitions
        missing_stepdefs = self._check_missing_stepdefs(feature_steps, stepdef_annotations)
        if missing_stepdefs:
            errors.append(f"Missing step definitions for: {', '.join(missing_stepdefs[:5])}")
        
        # Validation 2: Step definitions call page object methods
        undefined_methods = self._check_undefined_methods(stepdef_method_calls, pageobj_methods)
        if undefined_methods:
            errors.append(f"Step definitions call undefined page object methods: {', '.join(undefined_methods[:5])}")
        
        # Validation 3: Page object methods are not empty
        if not pageobj_methods:
            errors.append("Page object has no public methods")
        
        # Validation 4: Check selector references (basic check)
        if html_elements:
            selector_errors = self._check_selectors(pageobject_content, html_elements)
            if selector_errors:
                errors.extend(selector_errors)
        
        is_valid = len(errors) == 0
        log_validation_result("Cross-file", is_valid, errors)
        
        return is_valid, errors
    
    def _extract_feature_steps(self, feature_content: str) -> List[str]:
        """Extract all steps from feature file."""
        steps = []
        for line in feature_content.split('\n'):
            stripped = line.strip()
            if stripped and stripped.split()[0] in ['Given', 'When', 'Then', 'And', 'But']:
                step_text = extract_step_text(stripped)
                normalized = normalize_step_text(step_text)
                steps.append(normalized)
        return list(set(steps))  # Unique steps
    
    def _extract_stepdef_annotations(self, stepdef_content: str) -> List[str]:
        """Extract step texts from annotations."""
        pattern = r'@(?:Given|When|Then|And|But)\s*\(\s*"([^"]+)"\s*\)'
        matches = re.findall(pattern, stepdef_content)
        return [normalize_step_text(m) for m in matches]
    
    def _extract_method_calls(self, stepdef_content: str) -> List[str]:
        """Extract method calls from step definitions."""
        # Pattern: objectName.methodName(...)
        pattern = r'(\w+)\.(\w+)\s*\('
        matches = re.findall(pattern, stepdef_content)
        
        methods = set()
        for obj, method in matches:
            # Ignore common Java/Selenium classes
            if obj not in ['driver', 'Assert', 'System', 'String', 'wait', 'ExpectedConditions']:
                methods.add(method)
        
        return list(methods)
    
    def _extract_pageobj_methods(self, pageobj_content: str) -> List[str]:
        """Extract public method names from page object."""
        pattern = r'public\s+(?:void|[\w<>]+)\s+(\w+)\s*\('
        matches = re.findall(pattern, pageobj_content)
        
        # Filter out constructor
        class_match = re.search(r'public\s+class\s+(\w+)', pageobj_content)
        class_name = class_match.group(1) if class_match else ""
        
        return [m for m in matches if m != class_name]
    
    def _check_missing_stepdefs(self, feature_steps: List[str], stepdef_annotations: List[str]) -> List[str]:
        """Check if all feature steps have corresponding definitions."""
        missing = []
        for step in feature_steps:
            # Check if any annotation matches (normalized comparison)
            if step not in stepdef_annotations:
                # Also check with relaxed matching (parameter placeholders)
                if not self._relaxed_match(step, stepdef_annotations):
                    missing.append(step[:50])  # Truncate for readability
        return missing
    
    def _relaxed_match(self, step: str, annotations: List[str]) -> bool:
        """Check if step matches any annotation with parameter placeholders."""
        # Replace parameter placeholders with wildcards
        step_pattern = re.sub(r'\{\}', r'.+', step)
        for annotation in annotations:
            if re.match(step_pattern, annotation):
                return True
        return False
    
    def _check_undefined_methods(self, called_methods: List[str], defined_methods: List[str]) -> List[str]:
        """Check if all called methods are defined."""
        return [m for m in called_methods if m not in defined_methods]
    
    def _check_selectors(self, pageobj_content: str, html_elements: List[Dict]) -> List[str]:
        """Basic check if selectors reference valid HTML elements."""
        errors = []
        
        # Extract @FindBy selectors
        findby_pattern = r'@FindBy\s*\(\s*(\w+)\s*=\s*"([^"]+)"'
        selectors = re.findall(findby_pattern, pageobj_content)
        
        # Build list of available IDs, names, etc from HTML
        available_ids = {e.get('id') for e in html_elements if e.get('id')}
        available_names = {e.get('name') for e in html_elements if e.get('name')}
        
        for selector_type, selector_value in selectors:
            if selector_type == 'id' and selector_value not in available_ids:
                errors.append(f"Selector references non-existent ID: '{selector_value}'")
            elif selector_type == 'name' and selector_value not in available_names:
                errors.append(f"Selector references non-existent name: '{selector_value}'")
        
        return errors[:5]  # Limit error count