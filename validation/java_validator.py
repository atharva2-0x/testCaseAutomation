
# ============================================================================
# FILE: validation/java_validator.py
# ============================================================================
"""Validator for Java code (step definitions and page objects)."""
import re
from typing import Tuple, List
from core.logger import log, log_validation_result
from core.utils import validate_java_syntax_basic


class JavaValidator:
    """Validates Java code for syntax and structure."""
    
    def validate(self, java_content: str, file_type: str = "generic") -> Tuple[bool, List[str]]:
        """
        Validate Java file content.
        
        Args:
            java_content: Java source code
            file_type: "stepdef" or "pageobject" for specific validation
        
        Returns:
            (is_valid, errors_list)
        """
        errors = []
        
        # Basic syntax validation
        syntax_valid, syntax_errors = validate_java_syntax_basic(java_content)
        if not syntax_valid:
            errors.extend(syntax_errors)
        
        # Check for package declaration
        if not re.search(r'package\s+[\w.]+;', java_content):
            errors.append("Missing package declaration")
        
        # Check for class declaration
        if not re.search(r'public\s+class\s+\w+', java_content):
            errors.append("Missing public class declaration")
        
        # File-specific validation
        if file_type == "stepdef":
            errors.extend(self._validate_stepdef_specific(java_content))
        elif file_type == "pageobject":
            errors.extend(self._validate_pageobject_specific(java_content))
        
        # Check for common issues
        errors.extend(self._check_common_issues(java_content))
        
        is_valid = len(errors) == 0
        log_validation_result(f"Java ({file_type})", is_valid, errors)
        
        return is_valid, errors
    
    def _validate_stepdef_specific(self, content: str) -> List[str]:
        """Validate step definition specific requirements."""
        errors = []
        
        # Check for Cucumber imports
        required_imports = ['cucumber.java.en']
        for req_import in required_imports:
            if req_import not in content:
                errors.append(f"Missing import for {req_import}")
        
        # Check for step annotations
        has_annotations = any(
            annotation in content 
            for annotation in ['@Given', '@When', '@Then']
        )
        if not has_annotations:
            errors.append("No step annotations (@Given/@When/@Then) found")
        
        # Check annotation format
        annotation_pattern = r'@(?:Given|When|Then|And|But)\s*\(\s*"[^"]+"\s*\)'
        if not re.search(annotation_pattern, content):
            errors.append("Invalid annotation format - should be @Given(\"step text\")")
        
        # Check for constructor
        if 'WebDriver driver' not in content:
            errors.append("Missing WebDriver initialization in constructor")
        
        # Check for placeholder methods
        if '// TODO' in content or '// Implementation' in content:
            errors.append("Found placeholder comments - all methods must be implemented")
        
        return errors
    
    def _validate_pageobject_specific(self, content: str) -> List[str]:
        """Validate page object specific requirements."""
        errors = []
        
        # Check for Selenium imports
        required_imports = ['selenium.WebDriver', 'selenium.WebElement']
        for req_import in required_imports:
            if req_import not in content:
                errors.append(f"Missing import for {req_import}")
        
        # Check for @FindBy annotations
        if '@FindBy' not in content:
            errors.append("No @FindBy annotations found - page objects should have element locators")
        
        # Check for PageFactory.initElements
        if 'PageFactory.initElements' not in content:
            errors.append("Missing PageFactory.initElements() call in constructor")
        
        # Check for WebDriverWait
        if 'WebDriverWait' not in content:
            errors.append("Missing WebDriverWait - should use explicit waits")
        
        # Check for at least one public method
        if not re.search(r'public\s+(?:void|[\w<>]+)\s+\w+\s*\([^)]*\)\s*\{', content):
            errors.append("No public methods found")
        
        return errors
    
    def _check_common_issues(self, content: str) -> List[str]:
        """Check for common Java issues."""
        errors = []
        
        # Check for unclosed strings
        # Count quotes (should be even)
        quote_count = content.count('"') - content.count('\\"')
        if quote_count % 2 != 0:
            errors.append("Unclosed string literal detected")
        
        # Check for empty method bodies
        empty_method_pattern = r'public\s+(?:void|[\w<>]+)\s+\w+\s*\([^)]*\)\s*\{\s*\}'
        empty_methods = re.findall(empty_method_pattern, content)
        if empty_methods:
            errors.append(f"Found {len(empty_methods)} empty method(s) - all methods must have implementation")
        
        return errors

