# ============================================================================
# EXAMPLE: tests/samples/StepDefsOld.java
# ============================================================================
SAMPLE_OLD_STEPDEF = """package stepdefinitions;

import io.cucumber.java.en.Given;
import io.cucumber.java.en.When;
import io.cucumber.java.en.Then;
import org.testng.Assert;
import org.openqa.selenium.WebDriver;
import pageobjects.LoginPage;

public class LoginStepDefinitions {
    
    private WebDriver driver;
    private LoginPage loginPage;
    
    public LoginStepDefinitions(WebDriver driver) {
        this.driver = driver;
        this.loginPage = new LoginPage(driver);
    }
    
    @Given("I am on the login page")
    public void iAmOnTheLoginPage() {
        loginPage.navigateToLoginPage();
    }
    
    @When("I enter {string} in username field")
    public void iEnterInUsernameField(String username) {
        loginPage.enterUsername(username);
    }
    
    @When("I enter {string} in password field")
    public void iEnterInPasswordField(String password) {
        loginPage.enterPassword(password);
    }
    
    @When("I click on login button")
    public void iClickOnLoginButton() {
        loginPage.clickLoginButton();
    }
    
    @Then("I should see {string} page")
    public void iShouldSeePage(String pageName) {
        String currentUrl = driver.getCurrentUrl();
        Assert.assertTrue(currentUrl.contains(pageName.toLowerCase()));
    }
}
"""
