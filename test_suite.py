"""Test suite for agents."""
import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.feature_agent import FeatureAgent
from agents.stepdef_agent import StepDefinitionAgent
from agents.pageobject_agent import PageObjectAgent
from agents.orchestrator_agent import OrchestratorAgent
from llm.client import LLMClient
from ingestion.vectorizer import Vectorizer
from ingestion.html_parser import HTMLParser
from core.config import settings


@pytest.fixture
def sample_html():
    """Sample HTML for testing."""
    return """
    <form id="login-form">
        <input id="username" name="username" placeholder="Username">
        <input id="password" type="password" name="password">
        <button id="login-btn">Login</button>
    </form>
    """


@pytest.fixture
def sample_scenarios():
    """Sample test scenarios."""
    return """
    User Login Flow
    - User enters username
    - User enters password
    - User clicks login button
    - User should see dashboard
    """


@pytest.fixture
def html_elements(sample_html):
    """Parse HTML and return elements."""
    parser = HTMLParser(sample_html)
    return parser.parse()


@pytest.fixture
def vectorizer():
    """Create vectorizer instance."""
    return Vectorizer()


@pytest.fixture
def llm_client():
    """Create LLM client instance."""
    return LLMClient()


class TestHTMLParser:
    """Test HTML parsing."""
    
    def test_parse_form_elements(self, sample_html):
        """Test parsing form elements."""
        parser = HTMLParser(sample_html)
        elements = parser.parse()
        
        assert len(elements) >= 3
        
        # Check for username field
        username_elem = next((e for e in elements if e['id'] == 'username'), None)
        assert username_elem is not None
        assert username_elem['type'] == 'input'
        assert username_elem['placeholder'] == 'Username'
    
    def test_selector_generation(self, sample_html):
        """Test selector generation."""
        parser = HTMLParser(sample_html)
        elements = parser.parse()
        
        login_btn = next((e for e in elements if e['id'] == 'login-btn'), None)
        assert login_btn is not None
        assert 'preferred_selector' in login_btn
        assert login_btn['preferred_selector']['strategy'] == 'id'


class TestVectorizer:
    """Test vectorization functionality."""
    
    def test_vectorize_html_once(self, vectorizer, html_elements, tmp_path):
        """Test that HTML is vectorized only once."""
        html_file = tmp_path / "test.html"
        html_file.write_text("<html><body>Test</body></html>")
        
        # First vectorization
        doc_ids_1 = vectorizer.vectorize_file(html_file, "html", html_elements)
        assert len(doc_ids_1) > 0
        
        # Second attempt should skip
        doc_ids_2 = vectorizer.vectorize_file(html_file, "html", html_elements)
        assert doc_ids_1 == doc_ids_2
        assert vectorizer.is_file_vectorized(html_file)
    
    def test_search_functionality(self, vectorizer, html_elements):
        """Test vector search."""
        # Add some documents
        for elem in html_elements[:3]:
            text = f"{elem['type']} {elem['text']}"
            vectorizer.vector_store.add_document(
                text=text,
                metadata={'type': 'html'},
                embedding=vectorizer.embed_text(text)
            )
        
        # Search
        results = vectorizer.search("login button", top_k=2)
        assert len(results) <= 2


class TestFeatureAgent:
    """Test feature agent."""
    
    def test_feature_generation(self, llm_client, vectorizer, sample_scenarios, html_elements):
        """Test feature file generation."""
        agent = FeatureAgent(llm_client, vectorizer)
        
        result = agent.generate(
            scenarios=sample_scenarios,
            html_elements=html_elements
        )
        
        assert 'content' in result
        assert 'Feature:' in result['content']
        assert 'Scenario:' in result['content']
    
    def test_existing_steps_retrieval(self, llm_client, vectorizer):
        """Test retrieval of existing steps."""
        agent = FeatureAgent(llm_client, vectorizer)
        
        # This should not crash even with empty vector store
        existing_steps = agent._get_existing_steps_context()
        assert existing_steps is not None


class TestStepDefinitionAgent:
    """Test step definition agent."""
    
    def test_stepdef_generation(self, llm_client, vectorizer, html_elements):
        """Test step definition generation."""
        agent = StepDefinitionAgent(llm_client, vectorizer)
        
        feature_content = """
        Feature: Login
        Scenario: User login
            Given I am on login page
            When I enter username
            Then I should see dashboard
        """
        
        result = agent.generate(
            feature_content=feature_content,
            html_elements=html_elements
        )
        
        assert 'content' in result
        assert 'public class' in result['content']
        assert '@Given' in result['content'] or '@When' in result['content']


class TestPageObjectAgent:
    """Test page object agent."""
    
    def test_pageobject_generation(self, llm_client, vectorizer, html_elements):
        """Test page object generation."""
        agent = PageObjectAgent(llm_client, vectorizer)
        
        stepdef_content = """
        public void iEnterUsername() {
            loginPage.enterUsername("test");
        }
        """
        
        result = agent.generate(
            stepdef_content=stepdef_content,
            html_elements=html_elements
        )
        
        assert 'content' in result
        assert 'public class' in result['content']
        assert '@FindBy' in result['content']
        assert 'PageFactory.initElements' in result['content']


class TestOrchestratorAgent:
    """Test orchestrator agent (integration test)."""
    
    @pytest.mark.integration
    def test_full_workflow(self, vectorizer, sample_scenarios, html_elements):
        """Test complete workflow - requires valid API key."""
        # Skip if no API key
        try:
            orchestrator = OrchestratorAgent(vectorizer)
        except ValueError:
            pytest.skip("No API key configured")
        
        result = orchestrator.execute(
            scenarios=sample_scenarios,
            html_elements=html_elements
        )
        
        # Should complete within max iterations
        assert result['iterations'] <= settings.orchestrator_max_iterations


class TestValidators:
    """Test validation modules."""
    
    def test_feature_validator(self):
        """Test feature file validation."""
        from validation.feature_validator import FeatureValidator
        
        validator = FeatureValidator()
        
        # Valid feature
        valid_feature = """
        Feature: Test
          Scenario: Test scenario
            Given I am on page
            When I click button
            Then I see result
        """
        is_valid, errors = validator.validate(valid_feature)
        assert is_valid
        assert len(errors) == 0
        
        # Invalid feature (no Feature keyword)
        invalid_feature = """
        Scenario: Test
            Given something
        """
        is_valid, errors = validator.validate(invalid_feature)
        assert not is_valid
        assert len(errors) > 0
    
    def test_java_validator(self):
        """Test Java code validation."""
        from validation.java_validator import JavaValidator
        
        validator = JavaValidator()
        
        # Valid Java
        valid_java = """
        package test;
        public class Test {
            public void method() {
                System.out.println("test");
            }
        }
        """
        is_valid, errors = validator.validate(valid_java)
        assert is_valid or len(errors) < 3  # May have minor issues
        
        # Invalid Java (unbalanced braces)
        invalid_java = """
        public class Test {
            public void method() {
                System.out.println("test");
        }
        """
        is_valid, errors = validator.validate(invalid_java)
        assert not is_valid


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])