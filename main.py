"""Main entry point for automated test case generator."""
import argparse
from pathlib import Path
from core.config import settings
from core.logger import log
from ingestion.html_parser import HTMLParser
from ingestion.code_parser import FeatureFileParser, StepDefinitionParser, PageObjectParser
from ingestion.vectorizer import Vectorizer
from agents.orchestrator_agent import OrchestratorAgent
from core.utils import read_file, write_file


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Automated Test Case Generator - Multi-Agent System"
    )
    
    parser.add_argument(
        '--html',
        type=Path,
        help='Path to HTML file to parse'
    )
    
    parser.add_argument(
        '--scenarios',
        type=Path,
        help='Path to natural language scenarios file'
    )
    
    parser.add_argument(
        '--existing-dir',
        type=Path,
        help='Directory containing existing .feature, .java files'
    )
    
    parser.add_argument(
        '--skip-vectorization',
        action='store_true',
        help='Skip vectorization if already done'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        help='Override LLM model name'
    )
    
    parser.add_argument(
        '--max-retries',
        type=int,
        default=3,
        help='Maximum retry attempts for agents'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug logging'
    )
    
    parser.add_argument(
        '--output-dir',
        type=Path,
        help='Output directory for generated files'
    )
    
    return parser.parse_args()


def main():
    """Main execution flow."""
    args = parse_arguments()
    
    # Override settings from CLI args
    if args.model:
        settings.model_name = args.model
    if args.max_retries:
        settings.max_retries = args.max_retries
    if args.debug:
        settings.log_level = "DEBUG"
    if args.output_dir:
        settings.output_dir = args.output_dir
    
    log.info("=" * 80)
    log.info("AUTOMATED TEST CASE GENERATOR - Multi-Agent System")
    log.info("=" * 80)
    
    try:
        # Step 1: Initialize Vectorizer
        log.info("\n[STEP 1] Initializing Vectorizer...")
        vectorizer = Vectorizer()
        
        # Step 2: Parse and Vectorize HTML
        html_path = args.html or settings.input_html_path
        html_elements = []
        
        if html_path and html_path.exists():
            log.info(f"\n[STEP 2] Parsing HTML: {html_path}")
            html_content = read_file(html_path)
            html_parser = HTMLParser(html_content, source_name=html_path.name)
            html_elements = html_parser.parse()
            
            if not args.skip_vectorization:
                log.info("Vectorizing HTML elements...")
                vectorizer.vectorize_file(html_path, "html", html_elements)
        else:
            log.warning("No HTML file provided, skipping HTML parsing")
        
        # Step 3: Parse and Vectorize Existing Files
        log.info("\n[STEP 3] Processing Existing Test Files...")
        
        existing_feature_data = None
        existing_stepdef_data = None
        existing_pageobj_data = None
        
        # Look for existing files
        existing_dir = args.existing_dir or Path("./input/existing")
        
        if existing_dir and existing_dir.exists():
            # Find files
            feature_files = list(existing_dir.glob("*.feature"))
            stepdef_files = list(existing_dir.glob("*StepDef*.java"))
            pageobj_files = list(existing_dir.glob("*Page*.java"))
            
            # Parse feature file
            if feature_files:
                feature_path = feature_files[0]
                log.info(f"Parsing feature file: {feature_path.name}")
                feature_parser = FeatureFileParser(feature_path)
                existing_feature_data = feature_parser.parse()
                
                if not args.skip_vectorization:
                    vectorizer.vectorize_file(feature_path, "feature", existing_feature_data)
            
            # Parse step definitions
            if stepdef_files:
                stepdef_path = stepdef_files[0]
                log.info(f"Parsing step definitions: {stepdef_path.name}")
                stepdef_parser = StepDefinitionParser(stepdef_path)
                existing_stepdef_data = stepdef_parser.parse()
                
                if not args.skip_vectorization:
                    vectorizer.vectorize_file(stepdef_path, "stepdef", existing_stepdef_data)
            
            # Parse page objects
            if pageobj_files:
                pageobj_path = pageobj_files[0]
                log.info(f"Parsing page objects: {pageobj_path.name}")
                pageobj_parser = PageObjectParser(pageobj_path)
                existing_pageobj_data = pageobj_parser.parse()
                
                if not args.skip_vectorization:
                    vectorizer.vectorize_file(pageobj_path, "pageobject", existing_pageobj_data)
        
        # Save vector store
        vectorizer.vector_store.save()
        
        # Step 4: Load Test Scenarios
        scenarios_path = args.scenarios or settings.input_scenarios_path
        scenarios_text = ""
        
        if scenarios_path and scenarios_path.exists():
            log.info(f"\n[STEP 4] Loading Test Scenarios: {scenarios_path}")
            scenarios_text = read_file(scenarios_path)
        else:
            log.error("No scenarios file provided!")
            return 1
        
        # Step 5: Run Multi-Agent Workflow
        log.info("\n[STEP 5] Starting Multi-Agent Workflow...")
        orchestrator = OrchestratorAgent(vectorizer)
        
        results = orchestrator.execute(
            scenarios=scenarios_text,
            html_elements=html_elements,
            existing_feature=existing_feature_data,
            existing_stepdefs=existing_stepdef_data,
            existing_pageobjects=existing_pageobj_data
        )
        
        # Step 6: Write Output Files
        if results['success']:
            log.info("\n[STEP 6] Writing Output Files...")
            
            output_dir = settings.output_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Write feature file
            feature_path = output_dir / settings.output_feature_file
            write_file(feature_path, results['feature_content'])
            log.info(f"✓ Feature file: {feature_path}")
            
            # Write step definitions
            stepdef_path = output_dir / settings.output_stepdef_file
            write_file(stepdef_path, results['stepdef_content'])
            log.info(f"✓ Step definitions: {stepdef_path}")
            
            # Write page objects
            pageobj_path = output_dir / settings.output_pageobj_file
            write_file(pageobj_path, results['pageobject_content'])
            log.info(f"✓ Page objects: {pageobj_path}")
            
            log.info("\n" + "=" * 80)
            log.info("SUCCESS! Test files generated successfully")
            log.info("=" * 80)
            
            return 0
        else:
            log.error("\n" + "=" * 80)
            log.error("FAILED! Could not generate valid test files")
            log.error(f"Errors: {results.get('errors', [])}")
            log.error("=" * 80)
            return 1
    
    except Exception as e:
        log.error(f"\nFATAL ERROR: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())