# Auto Test Case Generator

Multi-agent system for automated Cucumber test case generation from HTML and natural language scenarios.

## Features

- **HTML Parsing**: Extracts actionable elements (buttons, inputs, links) with XPath/ID/text selectors
- **Vector Storage**: One-time vectorization of HTML and existing test files
- **Multi-Agent Workflow**:
  - **Orchestrator**: Validates outputs, manages retries, ensures consistency
  - **Feature Generator**: Creates Gherkin .feature files with BDD best practices
  - **Step Definition Generator**: Generates Java step definitions with TestNG
  - **Page Object Generator**: Creates Selenium-based page object classes
- **Intelligent Reuse**: Leverages existing test files to avoid duplication

## Installation

```bash
# Clone repository
git clone <repo-url>
cd auto_testcase_gen

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

2. Edit `.env` with your settings:
```env
# LLM Configuration
LLM_PROVIDER=openai  # or anthropic
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
MODEL_NAME=gpt-4-turbo-preview

# Vector DB
VECTOR_DB_PATH=./data/vector_db
EMBEDDING_MODEL=text-embedding-3-small

# Paths
INPUT_HTML_PATH=./input/page.html
INPUT_SCENARIOS_PATH=./input/scenarios.txt
EXISTING_FEATURE_PATH=./input/existing/old.feature
EXISTING_STEPDEF_PATH=./input/existing/StepDefsOld.java
EXISTING_PAGEOBJ_PATH=./input/existing/PageObjectsOld.java

# Output
OUTPUT_DIR=./output
```

## Usage

### Basic Usage

```bash
python main.py \
  --html input/page.html \
  --scenarios input/scenarios.txt \
  --existing-dir input/existing/
```

### Input Format

**scenarios.txt** (natural language test scenarios):
```
User Login Flow
- User navigates to login page
- User enters valid username
- User enters valid password
- User clicks login button
- User should see dashboard

Shopping Cart
- User adds product to cart
- User proceeds to checkout
- User enters shipping details
```

**page.html** (HTML to parse):
```html
<form id="login-form">
  <input id="username" name="username" placeholder="Username">
  <input id="password" type="password" name="password">
  <button id="login-btn" class="btn primary">Login</button>
</form>
```

### Output

The system generates:
1. **NewTests.feature** - Cucumber feature file with new scenarios
2. **NewStepDefinitions.java** - Java step definitions
3. **NewPageObjects.java** - Selenium page object methods

## Architecture

```
User Input (HTML + Scenarios)
         ↓
    HTML Parser → Vector DB
         ↓
   Orchestrator Agent
         ↓
    ┌────┴────┬────────┬─────────┐
    ↓         ↓        ↓         ↓
Feature   StepDef  PageObj   Validator
 Agent     Agent    Agent     
    └────┬────┴────────┴─────────┘
         ↓
   Final Output (3 files)
```

## Advanced Options

```bash
# Custom model
python main.py --model gpt-4 --html input/page.html

# Skip vectorization (if already done)
python main.py --skip-vectorization --html input/page.html

# Debug mode
python main.py --debug --html input/page.html

# Max retry attempts
python main.py --max-retries 5 --html input/page.html
```

## Development

```bash
# Run tests
pytest tests/

# Specific test
pytest tests/test_agents.py -v

# With coverage
pytest --cov=. --cov-report=html
```

## Troubleshooting

### Vector DB not persisting
- Check `VECTOR_DB_PATH` permissions
- Ensure `.vectorized_files.json` is writable

### LLM hallucination
- Increase temperature for creativity: `--temperature 0.3`
- Provide more context in existing files
- Use GPT-4 instead of GPT-3.5

### Java compilation errors
- Ensure proper package structure
- Check Java syntax in prompts
- Validate with `javac` if available

## License

MIT