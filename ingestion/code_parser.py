"""Parse existing .feature and .java files for reuse."""
import re
from typing import List, Dict, Any
from pathlib import Path
from core.logger import log
from core.utils import extract_step_text, extract_annotation_text, extract_java_method_name, normalize_step_text


class FeatureFileParser:
    """Parse Cucumber .feature files."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.content = self._read_file()
        self.features = []
        self.scenarios = []
        self.steps = []
    
    def _read_file(self) -> str:
        """Read feature file."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            log.error(f"Failed to read feature file {self.file_path}: {e}")
            return ""
    
    def parse(self) -> Dict[str, Any]:
        """Parse feature file and extract structure."""
        if not self.content:
            return {"features": [], "scenarios": [], "steps": []}
        
        lines = self.content.split('\n')
        current_feature = None
        current_scenario = None
        
        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                continue
            
            # Feature
            if stripped.startswith('Feature:'):
                current_feature = {
                    "line": line_num,
                    "title": stripped[8:].strip(),
                    "description": []
                }
                self.features.append(current_feature)
            
            # Scenario
            elif stripped.startswith('Scenario:') or stripped.startswith('Scenario Outline:'):
                is_outline = stripped.startswith('Scenario Outline:')
                title = stripped.split(':', 1)[1].strip()
                current_scenario = {
                    "line": line_num,
                    "title": title,
                    "type": "outline" if is_outline else "scenario",
                    "steps": []
                }
                self.scenarios.append(current_scenario)
            
            # Steps
            elif stripped.split()[0] in ['Given', 'When', 'Then', 'And', 'But']:
                keyword = stripped.split()[0]
                step_text = extract_step_text(stripped)
                normalized = normalize_step_text(step_text)
                
                step = {
                    "line": line_num,
                    "keyword": keyword,
                    "text": step_text,
                    "normalized": normalized,
                    "full_line": stripped
                }
                
                self.steps.append(step)
                if current_scenario:
                    current_scenario['steps'].append(step)
        
        log.info(f"Parsed {self.file_path}: {len(self.features)} features, {len(self.scenarios)} scenarios, {len(self.steps)} steps")
        
        return {
            "features": self.features,
            "scenarios": self.scenarios,
            "steps": self.steps,
            "content": self.content
        }
    
    def get_unique_steps(self) -> List[Dict]:
        """Get list of unique steps (normalized)."""
        seen = set()
        unique = []
        for step in self.steps:
            if step['normalized'] not in seen:
                seen.add(step['normalized'])
                unique.append(step)
        return unique


class StepDefinitionParser:
    """Parse Java step definition files."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.content = self._read_file()
        self.step_definitions = []
        self.imports = []
        self.class_name = ""
    
    def _read_file(self) -> str:
        """Read Java file."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            log.error(f"Failed to read step definition file {self.file_path}: {e}")
            return ""
    
    def parse(self) -> Dict[str, Any]:
        """Parse step definition file."""
        if not self.content:
            return {"step_definitions": [], "imports": [], "class_name": ""}
        
        # Extract imports
        import_pattern = r'import\s+[\w.]+;'
        self.imports = re.findall(import_pattern, self.content)
        
        # Extract class name
        class_pattern = r'public\s+class\s+(\w+)'
        class_match = re.search(class_pattern, self.content)
        self.class_name = class_match.group(1) if class_match else ""
        
        # Extract step definitions
        # Pattern: @Given/@When/@Then("...") followed by method
        step_pattern = r'(@(?:Given|When|Then|And|But)\s*\([^)]+\))\s*\n\s*public\s+void\s+(\w+)\s*\([^)]*\)\s*(\{[^}]*\})'
        
        matches = re.finditer(step_pattern, self.content, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            annotation = match.group(1)
            method_name = match.group(2)
            method_body = match.group(3)
            
            # Extract step text from annotation
            step_text = extract_annotation_text(annotation)
            
            if step_text:
                step_def = {
                    "annotation": annotation,
                    "step_text": step_text,
                    "normalized": normalize_step_text(step_text),
                    "method_name": method_name,
                    "method_body": method_body,
                    "full_definition": match.group(0)
                }
                self.step_definitions.append(step_def)
        
        log.info(f"Parsed {self.file_path}: {len(self.step_definitions)} step definitions")
        
        return {
            "step_definitions": self.step_definitions,
            "imports": self.imports,
            "class_name": self.class_name,
            "content": self.content
        }
    
    def find_step_by_text(self, step_text: str) -> Dict[str, Any]:
        """Find step definition by matching text."""
        normalized = normalize_step_text(step_text)
        for step_def in self.step_definitions:
            if step_def['normalized'] == normalized:
                return step_def
        return None


class PageObjectParser:
    """Parse Java page object files."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.content = self._read_file()
        self.methods = []
        self.locators = []
        self.imports = []
        self.class_name = ""
    
    def _read_file(self) -> str:
        """Read Java file."""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            log.error(f"Failed to read page object file {self.file_path}: {e}")
            return ""
    
    def parse(self) -> Dict[str, Any]:
        """Parse page object file."""
        if not self.content:
            return {"methods": [], "locators": [], "imports": [], "class_name": ""}
        
        # Extract imports
        import_pattern = r'import\s+[\w.]+;'
        self.imports = re.findall(import_pattern, self.content)
        
        # Extract class name
        class_pattern = r'public\s+class\s+(\w+)'
        class_match = re.search(class_pattern, self.content)
        self.class_name = class_match.group(1) if class_match else ""
        
        # Extract @FindBy locators
        locator_pattern = r'@FindBy\s*\([^)]+\)\s*\n\s*(?:private|public)\s+WebElement\s+(\w+);'
        locator_matches = re.finditer(locator_pattern, self.content, re.MULTILINE)
        
        for match in locator_matches:
            self.locators.append({
                "element_name": match.group(1),
                "annotation": match.group(0)
            })
        
        # Extract methods
        method_pattern = r'public\s+(?:void|[\w<>]+)\s+(\w+)\s*\([^)]*\)\s*\{([^}]*)\}'
        method_matches = re.finditer(method_pattern, self.content, re.MULTILINE | re.DOTALL)
        
        for match in method_matches:
            method_name = match.group(1)
            method_body = match.group(2)
            
            # Skip constructor
            if method_name == self.class_name:
                continue
            
            self.methods.append({
                "name": method_name,
                "body": method_body,
                "full_method": match.group(0)
            })
        
        log.info(f"Parsed {self.file_path}: {len(self.methods)} methods, {len(self.locators)} locators")
        
        return {
            "methods": self.methods,
            "locators": self.locators,
            "imports": self.imports,
            "class_name": self.class_name,
            "content": self.content
        }