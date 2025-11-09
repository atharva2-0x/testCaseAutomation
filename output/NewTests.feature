```gherkin
Feature: User Authentication
  As a user
  I want to log into the system
  So that I can access my account

  Background:
    Given I am on the login page

  Scenario: Successful Login
    When I enter "testuser@example.com" in username field
    And I enter "SecurePass123" in password field
    And I click on login button
    Then I should see "Dashboard" page
    And I should see welcome message

  Scenario: Failed Login with Invalid Credentials
    When I enter "wronguser@example.com" in username field
    And I enter "WrongPass" in password field
    And I click on login button
    Then I should see error message "Invalid credentials"
    And Login button should still be visible

  Scenario: Login with Remember Me
    When I enter "testuser@example.com" in username field
    And I enter "SecurePass123" in password field
    And I check remember me checkbox
    And I click on login button
    Then I should be redirected to dashboard
```