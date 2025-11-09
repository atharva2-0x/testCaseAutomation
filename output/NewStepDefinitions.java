```java
package stepdefinitions;

import io.cucumber.java.en.Given;
import io.cucumber.java.en.When;
import io.cucumber.java.en.Then;
import org.testng.Assert;
import org.openqa.selenium.WebDriver;
import pageobjects.LoginPage;
import pageobjects.DashboardPage;

public class NewStepDefinitions {

    private WebDriver driver;
    private LoginPage loginPage;
    private DashboardPage dashboardPage;

    public NewStepDefinitions(WebDriver driver) {
        this.driver = driver;
        this.loginPage = new LoginPage(driver);
        this.dashboardPage = new DashboardPage(driver);
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
        Assert.assertTrue(currentUrl.contains(pageName.toLowerCase()), "The current page is not the expected " + pageName + " page.");
    }

    @Then("I should see welcome message")
    public void iShouldSeeWelcomeMessage() {
        String welcomeMessage = dashboardPage.getWelcomeMessage();
        Assert.assertTrue(welcomeMessage.contains("Welcome"), "Welcome message is not displayed.");
    }

    @Then("I should see error message {string}")
    public void iShouldSeeErrorMessage(String errorMessage) {
        String actualErrorMessage = loginPage.getErrorMessage();
        Assert.assertEquals(actualErrorMessage, errorMessage, "Error message is not as expected.");
    }

    @Then("Login button should still be visible")
    public void loginButtonShouldStillBeVisible() {
        Assert.assertTrue(loginPage.isLoginButtonVisible(), "Login button is not visible.");
    }

    @When("I check remember me checkbox")
    public void iCheckRememberMeCheckbox() {
        loginPage.checkRememberMe();
    }

    @Then("I should be redirected to dashboard")
    public void iShouldBeRedirectedToDashboard() {
        String currentUrl = driver.getCurrentUrl();
        Assert.assertTrue(currentUrl.contains("dashboard"), "Not redirected to dashboard.");
    }
}
```