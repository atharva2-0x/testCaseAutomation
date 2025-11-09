# ============================================================================
# EXAMPLE: tests/samples/old.feature
# ============================================================================
SAMPLE_OLD_FEATURE = """Feature: User Authentication
  As a user
  I want to log into the system
  So that I can access my account

  Background:
    Given I am on the login page

  Scenario: Successful login
    When I enter "admin@example.com" in username field
    And I enter "Admin123" in password field
    And I click on login button
    Then I should see "Dashboard" page
"""
