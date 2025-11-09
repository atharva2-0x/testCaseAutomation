# Automated Test Case Generator - Complete Usage Guide

## Table of Contents
1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Setup Instructions](#setup-instructions)
4. [Usage Examples](#usage-examples)
5. [Configuration](#configuration)
6. [Agent Details](#agent-details)
7. [Vectorization Strategy](#vectorization-strategy)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Quick Start

### 1. Setup Environment

```bash
# Clone repository
git clone <repo-url>
cd auto_testcase_gen

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### 2. Create Sample Project

```bash
# Generate sample files and structure
python -c "from init_files_and_examples import create_sample_project_structure; create_sample_project_structure()"
```

### 3. Run First Generation

```bash
python main.py \
  --html input/page.html \
  --scenarios input/scenarios.txt \
  --existing-dir input/existing/
```

### 4. Check Output

Generated files will be in `./output/`:
- `NewTests.feature` - Cucumber feature file
- `NewStepDefinitions.java` - Step definition class
- `NewPageObjects.java` - Page object class

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INPUT                               │
│  • HTML file (page.html)                                    │
│  • Test scenarios (scenarios.txt)                           │
│  • Existing files (optional)                                │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              INGESTION LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ HTML Parser  │  │ Code Parser  │  │ Vectorizer   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┴──────────────────┘              │
│                            │                                 │
│                            ▼                                 │
│                   ┌─────────────────┐                       │
│                   │  Vector Store   │                       │
│                   │  (FAISS/Chroma) │                       │
│                   └─────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              MULTI-AGENT WORKFLOW                           │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │         ORCHESTRATOR AGENT (Manager)                 │   │
│  │  • Validates all outputs                             │   │
│  │  • Manages retry logic                               │   │
│  │  • Ensures consistency                               │   │
│  └───────────┬──────────────────────────────────────────┘   │
│              │                                               │
│     ┌────────┼────────┬──────────────┐                      │
│     ▼        ▼        ▼              ▼                      │
│  ┌─────┐ ┌──────┐ ┌─────────┐ ┌──────────┐                │
│  │Agent│ │Agent │ │ Agent   │ │Validators│                │
│  │  2  │ │  3   │ │   4     │ │          │                │
│  │     │ │      │ │         │ │          │                │
│  │Feat │ │Step  │ │  Page   │ │Feature   │                │
│  │ure  │ │Def   │ │ Object  │ │Java      │                │
│  │Gen  │ │Gen   │ │  Gen    │ │Cross-Val │                │
│  └─────┘ └──────┘ └─────────┘ └──────────┘                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   OUTPUT FILES                              │
│  • NewTests.feature                                         │
│  • NewStepDefinitions.java                                  │
│  • NewPageObjects.java                                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Setup Instructions

### Prerequisites

- Python 3.8+
- OpenAI API key OR Anthropic API key
- 4GB RAM minimum
- 1GB disk space for vector database

### Step-by-Step Setup

#### 1. Environment Configuration

Create `.env` file:

```bash
# Choose your LLM provider
LLM_PROVIDER=openai  # or anthropic

# OpenAI Configuration
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-4-turbo-preview

# OR Anthropic Configuration
# ANTHROPIC_API_KEY=sk-ant-...
# MODEL_NAME=claude-3-opus-20240229

# Paths
INPUT_HTML_PATH=./input/page.html
INPUT_SCENARIOS_PATH=./input/scenarios.txt
OUTPUT_DIR=./output

# Tuning
TEMPERATURE=0.2
MAX_RETRIES=3
ORCHESTRATOR_MAX_ITERATIONS=5
```

#### 2. Project Structure

```
auto_testcase_gen/
├── .env                    # Your configuration
├── main.py                 # Entry point
├── requirements.txt
│
├── input/
│   ├── page.html          # Your HTML to parse
│   ├── scenarios.txt      # Test scenarios
│   └── existing/          # Existing test files
│       ├── old.feature
│       ├── StepDefsOld.java
│       └── PageObjectsOld.java
│
├── output/                # Generated files appear here
├── data/
│   ├── vector_db/         # FAISS index
│   └── .vectorized_files.json  # Tracking
│
└── logs/
    └── app.log            # Detailed logs
```

---

## Usage Examples

### Example 1: Basic Usage

```bash
python main.py \
  --html input/login_page.html \
  --scenarios input/login_scenarios.txt
```

### Example 2: With Existing Files

```bash
python main.py \
  --html input/checkout_page.html \
  --scenarios input/checkout_scenarios.txt \
  --existing-dir input/existing/
```

### Example 3: Custom Model and Output

```bash
python main.py \
  --html input/page.html \
  --scenarios input/scenarios.txt \
  --model gpt-4 \
  --output-dir custom_output/ \
  --max-retries 5
```

### Example 4: Debug Mode

```bash
python main.py \
  --html input/page.html \
  --scenarios input/scenarios.txt \
  --debug
```

### Example 5: Skip Vectorization (After First Run)

```bash
python main.py \
  --html input/page.html \
  --scenarios input/scenarios.txt \
  --skip-vectorization
```

---

## Configuration

### LLM Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `LLM_PROVIDER` | `openai` or `anthropic` | `openai` |
| `MODEL_NAME` | Model to use | `gpt-4-turbo-preview` |
| `TEMPERATURE` | Creativity (0-1) | `0.2` |
| `MAX_TOKENS` | Max response length | `4000` |

**Model Recommendations:**
- **Best Quality**: `gpt-4-turbo-preview` or `claude-3-opus-20240229`
- **Balanced**: `gpt-4` or `claude-3-sonnet-20240229`
- **Fast/Cheap**: `gpt-3.5-turbo` (may hallucinate more)

### Vector Database Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `VECTOR_DB_TYPE` | `faiss` or `chroma` | `faiss` |
| `EMBEDDING_MODEL` | Embedding model | `text-embedding-3-small` |
| `TOP_K_RETRIEVAL` | Results per search | `5` |

### Agent Settings

| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_RETRIES` | Retries per agent | `3` |
| `ORCHESTRATOR_MAX_ITERATIONS` | Full workflow retries | `5` |
| `VALIDATION_STRICT_MODE` | Strict validation | `true` |

---

## Agent Details

### 1. Orchestrator Agent (Manager)

**Role**: Coordinates all agents and ensures quality

**Responsibilities**:
- Execute agents in sequence
- Validate each output
- Retry on failures with context
- Make final quality decision

**Workflow**:
```
1. Run Feature Agent
2. Validate feature file
3. If invalid → retry with feedback
4. Run StepDef Agent
5. Validate step definitions
6. If invalid → retry with feedback
7. Run PageObject Agent
8. Validate page objects
9. If invalid → retry with feedback
10. Cross-validate all files
11. If issues → determine responsible agent and retry
12. Return final result
```

### 2. Feature Agent

**Role**: Generate Cucumber .feature files

**Key Capabilities**:
- Converts natural language → Gherkin
- Reuses existing step patterns
- Maintains BDD structure
- References actual UI elements

**Prompt Strategy**:
- Retrieves similar existing steps from vector DB
- Formats HTML elements as context
- Enforces Given/When/Then structure
- Validates step actionability

### 3. Step Definition Agent

**Role**: Generate Java step definition classes

**Key Capabilities**:
- Maps Gherkin steps → Java methods
- Reuses existing step definitions
- Calls page object methods
- Uses TestNG annotations

**Prompt Strategy**:
- Extracts steps from feature file
- Retrieves existing step defs from vector DB
- Enforces @Given/@When/@Then usage
- Ensures method-to-page-object mapping

### 4. Page Object Agent

**Role**: Generate Selenium page object classes

**Key Capabilities**:
- Creates @FindBy locators from HTML
- Chooses optimal selector strategy
- Implements WebDriver wait patterns
- Generates action methods

**Prompt Strategy**:
- Prioritizes selectors: data-testid > id > name > css > xpath
- Includes explicit waits
- Enforces PageFactory pattern
- Maps to step definition requirements

---

## Vectorization Strategy

### One-Time Vectorization

The system vectorizes each file **only once** to prevent:
- Redundant processing
- Wasted API calls
- Inconsistent results
- Performance issues

### Tracking Mechanism

```python
# Stored in data/.vectorized_files.json
{
  "/path/to/file.html": {
    "hash": "sha256...",
    "doc_ids": ["doc_1", "doc_2", ...],
    "timestamp": "1234567890",
    "name": "file.html"
  }
}
```

### Process

```
1. Check if file exists in tracker
2. If exists, compute current hash
3. If hash matches → SKIP (already vectorized)
4. If hash different → RE-VECTORIZE (file changed)
5. If not in tracker → VECTORIZE (first time)
6. Update tracker with new hash
```

### Manual Reset

To force re-vectorization:

```bash
# Delete tracker
rm data/.vectorized_files.json

# Or delete entire vector DB
rm -rf data/vector_db/

# Next run will vectorize everything fresh
python main.py --html input/page.html --scenarios input/scenarios.txt
```

---

## Troubleshooting

### Issue: "No API key found"

**Solution**:
```bash
# Check .env file
cat .env | grep API_KEY

# Ensure correct provider
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...

# Or
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

### Issue: "Validation failed repeatedly"

**Causes**:
1. Model hallucinating
2. Insufficient context
3. Complex scenarios

**Solutions**:
```bash
# 1. Use better model
MODEL_NAME=gpt-4-turbo-preview

# 2. Increase retries
MAX_RETRIES=5
ORCHESTRATOR_MAX_ITERATIONS=7

# 3. Simplify scenarios (break into smaller chunks)

# 4. Provide more existing examples
```

### Issue: "Vector DB errors"

**Solution**:
```bash
# Clear and rebuild
rm -rf data/vector_db/
rm data/.vectorized_files.json

# Reinstall FAISS
pip uninstall faiss-cpu
pip install faiss-cpu==1.12.0
```

### Issue: "Java syntax errors in output"

**Solution**:
```bash
# Use stricter validation
VALIDATION_STRICT_MODE=true

# Lower temperature (less creative, more accurate)
TEMPERATURE=0.1

# Try different model
MODEL_NAME=gpt-4  # More precise than 3.5
```

---

## Best Practices

### 1. Input Preparation

**HTML**:
- Clean, well-formed HTML
- Include IDs and data-testid attributes
- Remove unnecessary elements

**Scenarios**:
- One clear action per line
- Use consistent terminology
- Match HTML element names

**Existing Files**:
- Keep them updated
- Use consistent naming
- Follow best practices

### 2. Model Selection

| Use Case | Recommended Model |
|----------|------------------|
| Production | GPT-4 Turbo, Claude Opus |
| Development | GPT-4, Claude Sonnet |
| Testing | GPT-3.5 Turbo |

### 3. Iteration Strategy

1. **First run**: Let it fail, learn from errors
2. **Second run**: Adjust scenarios based on errors
3. **Third run**: Should succeed with refined input

### 4. Vector DB Maintenance

- Clear after major HTML changes
- Keep existing files in sync
- Monitor `.vectorized_files.json` size

### 5. Output Review

Always review generated files:
```bash
# Check feature file
cat output/NewTests.feature

# Validate Java compilation (if javac available)
javac output/NewStepDefinitions.java output/NewPageObjects.java

# Run through linters
cucumber-lint output/NewTests.feature
checkstyle output/*.java
```

---

## Advanced Usage

### Custom Prompts

Edit prompt templates in `llm/prompts/`:

```bash
# Feature generation
llm/prompts/feature_prompt.txt

# Step definition generation
llm/prompts/stepdef_prompt.txt

# Page object generation
llm/prompts/pageobject_prompt.txt
```

### Programmatic Usage

```python
from core.config import settings
from agents.orchestrator_agent import OrchestratorAgent
from ingestion.vectorizer import Vectorizer
from ingestion.html_parser import HTMLParser

# Parse HTML
html_content = open('page.html').read()
parser = HTMLParser(html_content)
elements = parser.parse()

# Setup
vectorizer = Vectorizer()
orchestrator = OrchestratorAgent(vectorizer)

# Generate
result = orchestrator.execute(
    scenarios="User clicks login button",
    html_elements=elements
)

if result['success']:
    print("Feature:", result['feature_content'])
    print("StepDef:", result['stepdef_content'])
    print("PageObj:", result['pageobject_content'])
```

### Batch Processing

```python
import glob
from pathlib import Path

html_files = glob.glob("input/*.html")

for html_file in html_files:
    print(f"Processing {html_file}...")
    # Run main.py or use programmatic API
```

---

## Support & Contributing

### Getting Help

1. Check logs: `tail -f logs/app.log`
2. Enable debug: `--debug`
3. Review validation errors in output

### Contributing

1. Follow existing code style
2. Add tests for new features
3. Update documentation
4. Submit PR with clear description

---

## License

MIT License - See LICENSE file for details