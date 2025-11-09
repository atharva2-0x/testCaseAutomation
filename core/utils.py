"""Utility functions for file operations, validation, and text processing."""
import json
import hashlib
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from core.logger import log


def read_file(file_path: Path) -> str:
    """Read file content safely."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        log.error(f"Failed to read file {file_path}: {e}")
        raise


def write_file(file_path: Path, content: str):
    """Write content to file safely."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        log.info(f"Written file: {file_path}")
    except Exception as e:
        log.error(f"Failed to write file {file_path}: {e}")
        raise


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA256 hash of file content."""
    try:
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception as e:
        log.error(f"Failed to compute hash for {file_path}: {e}")
        raise


def load_json(file_path: Path) -> Dict:
    """Load JSON file."""
    try:
        if not file_path.exists():
            return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        log.error(f"Failed to load JSON from {file_path}: {e}")
        return {}


def save_json(file_path: Path, data: Dict):
    """Save data to JSON file."""
    try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, default=str)
        log.info(f"Saved JSON to {file_path}")
    except Exception as e:
        log.error(f"Failed to save JSON to {file_path}: {e}")
        raise


def sanitize_identifier(text: str) -> str:
    """Convert text to valid Java identifier."""
    # Remove special characters, keep alphanumeric and underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', text.replace(' ', '_'))
    # Ensure it doesn't start with a number
    if sanitized and sanitized[0].isdigit():
        sanitized = 'step_' + sanitized
    return sanitized or 'step_method'


def camel_case(text: str) -> str:
    """Convert text to camelCase."""
    words = re.findall(r'[a-zA-Z0-9]+', text)
    if not words:
        return 'method'
    return words[0].lower() + ''.join(word.capitalize() for word in words[1:])


def extract_step_text(step_line: str) -> str:
    """Extract step text from Gherkin line."""
    # Remove Given/When/Then/And/But keywords
    pattern = r'^\s*(Given|When|Then|And|But)\s+'
    return re.sub(pattern, '', step_line, flags=re.IGNORECASE).strip()


def extract_java_method_name(step_def: str) -> Optional[str]:
    """Extract method name from Java step definition."""
    # Pattern: public void methodName(...)
    pattern = r'public\s+void\s+(\w+)\s*\('
    match = re.search(pattern, step_def)
    return match.group(1) if match else None


def extract_annotation_text(step_def: str) -> Optional[str]:
    """Extract text from @Given/@When/@Then annotation."""
    # Pattern: @Given("text here")
    pattern = r'@(?:Given|When|Then|And|But)\s*\(\s*"([^"]+)"\s*\)'
    match = re.search(pattern, step_def)
    return match.group(1) if match else None


def normalize_step_text(text: str) -> str:
    """Normalize step text for comparison (remove parameters, extra spaces)."""
    # First, replace Cucumber parameter formats: {string}, {int}, {word}, etc. -> "{}"
    # This must come first to catch {string} before it gets processed as {}
    text = re.sub(r'\{[a-zA-Z0-9_]+\}', '"{}"', text)
    # Replace quoted strings with placeholder
    text = re.sub(r'"[^"]*"', '"{}"', text)
    # Replace numbers with placeholder
    text = re.sub(r'\b\d+\b', '{}', text)
    # Replace any remaining unquoted {} placeholders with "{}" for consistency
    text = re.sub(r'(?<!")\{\}(?!")', '"{}"', text)
    # Normalize whitespace
    text = ' '.join(text.split())
    return text.lower()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks for vectorization."""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if chunk:
            chunks.append(chunk)
    
    return chunks if chunks else [text]


def validate_gherkin_syntax(feature_content: str) -> tuple[bool, List[str]]:
    """Basic Gherkin syntax validation."""
    errors = []
    lines = feature_content.split('\n')
    
    # Check for Feature keyword
    has_feature = any(line.strip().startswith('Feature:') for line in lines)
    if not has_feature:
        errors.append("Missing 'Feature:' keyword")
    
    # Check for at least one Scenario
    has_scenario = any(
        line.strip().startswith('Scenario:') or 
        line.strip().startswith('Scenario Outline:') 
        for line in lines
    )
    if not has_scenario:
        errors.append("No scenarios found")
    
    # Check step indentation
    in_scenario = False
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped.startswith('Scenario'):
            in_scenario = True
        elif in_scenario and stripped and not stripped.startswith('#'):
            if stripped.split()[0] in ['Given', 'When', 'Then', 'And', 'But']:
                if not line.startswith('  ') and not line.startswith('\t'):
                    errors.append(f"Line {i}: Steps should be indented")
    
    return len(errors) == 0, errors


def validate_java_syntax_basic(java_content: str) -> tuple[bool, List[str]]:
    """Basic Java syntax validation."""
    errors = []
    
    # Check for class declaration
    if not re.search(r'public\s+class\s+\w+', java_content):
        errors.append("Missing public class declaration")
    
    # Check for balanced braces
    open_braces = java_content.count('{')
    close_braces = java_content.count('}')
    if open_braces != close_braces:
        errors.append(f"Unbalanced braces: {open_braces} open, {close_braces} close")
    
    # Check for balanced parentheses
    open_parens = java_content.count('(')
    close_parens = java_content.count(')')
    if open_parens != close_parens:
        errors.append(f"Unbalanced parentheses: {open_parens} open, {close_parens} close")
    
    return len(errors) == 0, errors


def timestamp() -> str:
    """Get current timestamp string."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text for logging."""
    return text[:max_length] + '...' if len(text) > max_length else text