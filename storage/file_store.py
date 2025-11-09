# ============================================================================
# FILE: storage/file_store.py
# ============================================================================
"""File storage utilities."""
from pathlib import Path
from typing import List, Dict
from core.utils import read_file, write_file, load_json, save_json


class FileStore:
    """Manage reading and writing of generated and existing files."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def save_generated_files(
        self,
        feature_content: str,
        stepdef_content: str,
        pageobj_content: str,
        output_dir: Path
    ):
        """Save all three generated files."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        write_file(output_dir / "NewTests.feature", feature_content)
        write_file(output_dir / "NewStepDefinitions.java", stepdef_content)
        write_file(output_dir / "NewPageObjects.java", pageobj_content)
    
    def load_existing_files(self, existing_dir: Path) -> Dict:
        """Load existing test files if they exist."""
        result = {
            'feature': None,
            'stepdef': None,
            'pageobject': None
        }
        
        if not existing_dir.exists():
            return result
        
        # Find files
        feature_files = list(existing_dir.glob("*.feature"))
        stepdef_files = list(existing_dir.glob("*StepDef*.java"))
        pageobj_files = list(existing_dir.glob("*Page*.java"))
        
        if feature_files:
            result['feature'] = read_file(feature_files[0])
        
        if stepdef_files:
            result['stepdef'] = read_file(stepdef_files[0])
        
        if pageobj_files:
            result['pageobject'] = read_file(pageobj_files[0])
        
        return result
