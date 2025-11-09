def create_sample_project_structure():
    """Create sample project structure with example files."""
    from pathlib import Path
    import os
    
    # Create directories
    dirs = [
        "input",
        "input/existing",
        "output",
        "data",
        "logs",
        "tests/samples"
    ]
    
    for dir_path in dirs:
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    # Write sample files
    Path("tests/samples/sample.html").write_text(SAMPLE_HTML)
    Path("tests/samples/scenarios.txt").write_text(SAMPLE_SCENARIOS)
    Path("tests/samples/old.feature").write_text(SAMPLE_OLD_FEATURE)
    Path("tests/samples/StepDefsOld.java").write_text(SAMPLE_OLD_STEPDEF)
    Path("tests/samples/PageObjectsOld.java").write_text(SAMPLE_OLD_PAGEOBJECT)
    
    # Copy to input directory for easy testing
    Path("input/page.html").write_text(SAMPLE_HTML)
    Path("input/scenarios.txt").write_text(SAMPLE_SCENARIOS)
    Path("input/existing/old.feature").write_text(SAMPLE_OLD_FEATURE)
    Path("input/existing/StepDefsOld.java").write_text(SAMPLE_OLD_STEPDEF)
    Path("input/existing/PageObjectsOld.java").write_text(SAMPLE_OLD_PAGEOBJECT)
    
    print("✓ Sample project structure created!")
    print("✓ Sample files created in tests/samples/ and input/")
    print("\nRun: python main.py --html input/page.html --scenarios input/scenarios.txt --existing-dir input/existing/")


if __name__ == "__main__":
    create_sample_project_structure()