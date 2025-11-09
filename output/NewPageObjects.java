```java
package pageobjects;

import org.openqa.selenium.WebDriver;
import org.openqa.selenium.WebElement;
import org.openqa.selenium.NoSuchElementException;
import org.openqa.selenium.support.FindBy;
import org.openqa.selenium.support.PageFactory;
import org.openqa.selenium.support.ui.WebDriverWait;
import org.openqa.selenium.support.ui.ExpectedConditions;
import java.time.Duration;

public class NewPageObject {

    private WebDriver driver;
    private WebDriverWait wait;

    @FindBy(id = "login-btn")
    private WebElement loginButton;

    @FindBy(id = "forgot-link")
    private WebElement forgotPasswordLink;

    @FindBy(id = "username")
    private WebElement usernameField;

    @FindBy(id = "password")
    private WebElement passwordField;

    @FindBy(id = "remember")
    private WebElement rememberMeCheckbox;

    @FindBy(xpath = "//label[contains(text(), 'Username:')]")
    private WebElement usernameLabel;

    @FindBy(xpath = "//label[contains(text(), 'Password:')]")
    private WebElement passwordLabel;

    @FindBy(xpath = "//label[contains(text(), 'Remember me')]")
    private WebElement rememberMeLabel;

    @FindBy(css = "div.form-group")
    private WebElement formGroupDiv;

    public NewPageObject(WebDriver driver) {
        this.driver = driver;
        this.wait = new WebDriverWait(driver, Duration.ofSeconds(10));
        PageFactory.initElements(driver, this);
    }

    public void navigateToLoginPage() {
        driver.get("https://example.com/login");
    }

    public void enterUsername(String username) {
        wait.until(ExpectedConditions.visibilityOf(usernameField));
        usernameField.clear();
        usernameField.sendKeys(username);
    }

    public void enterPassword(String password) {
        wait.until(ExpectedConditions.visibilityOf(passwordField));
        passwordField.clear();
        passwordField.sendKeys(password);
    }

    public void clickLoginButton() {
        wait.until(ExpectedConditions.elementToBeClickable(loginButton));
        loginButton.click();
    }

    public void checkRememberMe() {
        wait.until(ExpectedConditions.elementToBeClickable(rememberMeCheckbox));
        if (!rememberMeCheckbox.isSelected()) {
            rememberMeCheckbox.click();
        }
    }

    public String getWelcomeMessage() {
        WebElement welcomeMessageElement = wait.until(ExpectedConditions.visibilityOfElementLocated(By.id("welcome-message")));
        return welcomeMessageElement.getText();
    }

    public boolean isLoginButtonVisible() {
        try {
            return loginButton.isDisplayed();
        } catch (NoSuchElementException e) {
            return false;
        }
    }

    public String getErrorMessage() {
        WebElement errorMessageElement = wait.until(ExpectedConditions.visibilityOfElementLocated(By.className("error-message")));
        return errorMessageElement.getText();
    }

    public boolean toLowerCase(String text) {
        return text.toLowerCase().equals(text);
    }

    public boolean contains(String container, String content) {
        return container.contains(content);
    }
}
```