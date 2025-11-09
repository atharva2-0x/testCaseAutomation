# ============================================================================
# FILE: validation/feature_validator.py
# ============================================================================

"""Validator for Cucumber .feature files."""
import re
from typing import Tuple, List
from core.logger import log, log_validation_result
from core.utils import validate_gherkin_syntax


class FeatureValidator:
    """Validates Cucumber feature files for syntax and completeness."""
    
    def validate(self, feature_content: str) -> Tuple[bool, List[str]]:
        """
        Validate feature file content.
        
        Returns:
            (is_valid, errors_list)
        """
        errors = []
        
        # Check basic syntax
        syntax_valid, syntax_errors = validate_gherkin_syntax(feature_content)
        if not syntax_valid:
            errors.extend(syntax_errors)
        
        # Check for required elements
        if 'Feature:' not in feature_content:
            errors.append("Missing 'Feature:' declaration")
        
        if not re.search(r'Scenario:', feature_content):
            errors.append("No scenarios found")
        
        # Check for proper step keywords
        lines = feature_content.split('\n')
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                words = stripped.split()
                if words:
                    first_word = words[0]
                    
                    # Check for proper Given/When/Then usage
                    if first_word in ['Given', 'When', 'Then']:
                        # Ensure there's text after the keyword
                        if len(words) < 2:
                            errors.append(f"Line {i}: Empty step - '{stripped}'")
        
        # Check for placeholders
        placeholder_patterns = ['TODO', 'XXX', '...', '<placeholder>']
        for pattern in placeholder_patterns:
            if pattern in feature_content:
                errors.append(f"Found placeholder: '{pattern}' - all steps must be concrete")
        
        # Check indentation
        in_scenario = False
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith('Scenario'):
                in_scenario = True
            elif in_scenario and stripped:
                if stripped.split()[0] in ['Given', 'When', 'Then', 'And', 'But']:
                    if not line.startswith('  ') and not line.startswith('\t'):
                        errors.append(f"Line {i}: Steps must be indented under scenarios")
        
        is_valid = len(errors) == 0
        log_validation_result("Feature", is_valid, errors)
        
        return is_valid, errors

