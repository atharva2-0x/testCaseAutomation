"""Orchestrator Agent - Manages the multi-agent workflow and validates outputs."""
from typing import Dict, List, Any
from core.config import settings
from core.logger import log, log_agent_action
from llm.client import LLMClient
from agents.feature_agent import FeatureAgent
from agents.stepdef_agent import StepDefinitionAgent
from agents.pageobject_agent import PageObjectAgent
from validation.feature_validator import FeatureValidator
from validation.java_validator import JavaValidator
from validation.cross_validator import CrossValidator


class OrchestratorAgent:
    """
    Orchestrator Agent - The Manager
    
    Responsibilities:
    1. Coordinate all sub-agents (Feature, StepDef, PageObject)
    2. Validate outputs at each stage
    3. Manage retry logic when validation fails
    4. Ensure cross-file consistency
    5. Make final decision on output quality
    """
    
    def __init__(self, vectorizer):
        self.vectorizer = vectorizer
        self.llm_client = LLMClient()
        self.max_iterations = settings.orchestrator_max_iterations
        
        # Initialize validators
        self.feature_validator = FeatureValidator()
        self.java_validator = JavaValidator()
        self.cross_validator = CrossValidator()
        
        # Initialize sub-agents
        self.feature_agent = FeatureAgent(self.llm_client, self.vectorizer)
        self.stepdef_agent = StepDefinitionAgent(self.llm_client, self.vectorizer)
        self.pageobject_agent = PageObjectAgent(self.llm_client, self.vectorizer)
        
        log.info("Orchestrator Agent initialized")
    
    def execute(
        self,
        scenarios: str,
        html_elements: List[Dict],
        existing_feature: Dict = None,
        existing_stepdefs: Dict = None,
        existing_pageobjects: Dict = None
    ) -> Dict[str, Any]:
        """
        Main orchestration workflow.
        
        Returns:
            {
                'success': bool,
                'feature_content': str,
                'stepdef_content': str,
                'pageobject_content': str,
                'errors': List[str],
                'iterations': int
            }
        """
        log_agent_action("Orchestrator", "Starting multi-agent workflow")
        
        iteration = 0
        all_errors = []
        
        feature_content = None
        stepdef_content = None
        pageobject_content = None
        
        while iteration < self.max_iterations:
            iteration += 1
            log.info(f"\n{'='*60}")
            log.info(f"ITERATION {iteration}/{self.max_iterations}")
            log.info(f"{'='*60}\n")
            
            try:
                # PHASE 1: Generate Feature File
                log_agent_action("Orchestrator", "Phase 1: Feature Generation")
                feature_result = self.feature_agent.generate(
                    scenarios=scenarios,
                    html_elements=html_elements,
                    existing_feature=existing_feature,
                    feedback=None if iteration == 1 else all_errors
                )
                
                feature_content = feature_result['content']
                
                # Validate feature file
                feature_valid, feature_errors = self.feature_validator.validate(feature_content)
                
                if not feature_valid:
                    log.error(f"Feature validation failed: {feature_errors}")
                    all_errors.extend([f"Feature: {e}" for e in feature_errors])
                    
                    # Give feedback to feature agent for next iteration
                    feedback = self._create_feedback("feature", feature_errors, feature_content)
                    continue
                
                log.success("✓ Feature file validation passed")
                
                # PHASE 2: Generate Step Definitions
                log_agent_action("Orchestrator", "Phase 2: Step Definition Generation")
                stepdef_result = self.stepdef_agent.generate(
                    feature_content=feature_content,
                    html_elements=html_elements,
                    existing_stepdefs=existing_stepdefs,
                    existing_pageobjects=existing_pageobjects,
                    feedback=None if iteration == 1 else all_errors
                )
                
                stepdef_content = stepdef_result['content']
                
                # Validate step definitions
                stepdef_valid, stepdef_errors = self.java_validator.validate(
                    stepdef_content,
                    file_type="stepdef"
                )
                
                if not stepdef_valid:
                    log.error(f"Step definition validation failed: {stepdef_errors}")
                    all_errors.extend([f"StepDef: {e}" for e in stepdef_errors])
                    continue
                
                log.success("✓ Step definition validation passed")
                
                # PHASE 3: Generate Page Objects
                log_agent_action("Orchestrator", "Phase 3: Page Object Generation")
                pageobj_result = self.pageobject_agent.generate(
                    stepdef_content=stepdef_content,
                    html_elements=html_elements,
                    existing_pageobjects=existing_pageobjects,
                    feedback=None if iteration == 1 else all_errors
                )
                
                pageobject_content = pageobj_result['content']
                
                # Validate page objects
                pageobj_valid, pageobj_errors = self.java_validator.validate(
                    pageobject_content,
                    file_type="pageobject"
                )
                
                if not pageobj_valid:
                    log.error(f"Page object validation failed: {pageobj_errors}")
                    all_errors.extend([f"PageObject: {e}" for e in pageobj_errors])
                    continue
                
                log.success("✓ Page object validation passed")
                
                # PHASE 4: Cross-validation
                log_agent_action("Orchestrator", "Phase 4: Cross-validation")
                cross_valid, cross_errors = self.cross_validator.validate(
                    feature_content=feature_content,
                    stepdef_content=stepdef_content,
                    pageobject_content=pageobject_content,
                    html_elements=html_elements
                )
                
                if not cross_valid:
                    log.error(f"Cross-validation failed: {cross_errors}")
                    all_errors.extend([f"Cross-validation: {e}" for e in cross_errors])
                    
                    # Determine which agent needs to fix the issue
                    # For simplicity, retry from feature agent
                    continue
                
                log.success("✓ Cross-validation passed")
                
                # SUCCESS!
                log.info("\n" + "="*60)
                log.success(f"✓ ALL VALIDATIONS PASSED (Iteration {iteration})")
                log.info("="*60)
                
                return {
                    'success': True,
                    'feature_content': feature_content,
                    'stepdef_content': stepdef_content,
                    'pageobject_content': pageobject_content,
                    'errors': [],
                    'iterations': iteration
                }
            
            except Exception as e:
                log.error(f"Error in iteration {iteration}: {e}", exc_info=True)
                all_errors.append(f"System error: {str(e)}")
        
        # Max iterations reached without success
        log.error(f"\nMax iterations ({self.max_iterations}) reached without producing valid output")
        
        return {
            'success': False,
            'feature_content': feature_content,
            'stepdef_content': stepdef_content,
            'pageobject_content': pageobject_content,
            'errors': all_errors,
            'iterations': self.max_iterations
        }
    
    def _create_feedback(self, agent_type: str, errors: List[str], content: str) -> str:
        """Create structured feedback for agent to fix issues."""
        feedback = f"""
VALIDATION FAILED for {agent_type.upper()}

Errors found:
"""
        for i, error in enumerate(errors, 1):
            feedback += f"{i}. {error}\n"
        
        feedback += f"""

Current output (first 500 chars):
{content[:500]}...

Please fix these issues and regenerate. Focus on:
- Addressing each error specifically
- Maintaining valid syntax
- Ensuring consistency with HTML elements and existing code
"""
        return feedback
    
    def _determine_responsible_agent(self, error: str) -> str:
        """Determine which agent is responsible for fixing an error."""
        if "feature" in error.lower() or "gherkin" in error.lower():
            return "feature"
        elif "step definition" in error.lower() or "annotation" in error.lower():
            return "stepdef"
        elif "page object" in error.lower() or "selector" in error.lower():
            return "pageobject"
        else:
            return "feature"  # Default to starting over