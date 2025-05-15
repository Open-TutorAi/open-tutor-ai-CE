/// <reference types="cypress" />

declare namespace Cypress {
  interface Chainable<Subject = any> {
    login(email: string, password: string): Chainable<void>;
    loginAsTeacher(): Chainable<void>;
    loginAsStudent(): Chainable<void>;
    loginAsParent(): Chainable<void>;
    signup(role: string, firstName: string, lastName: string, email: string, password: string): Chainable<void>;
    clearAuth(): Chainable<void>;
  }
}

Cypress.Commands.add('login', (email: string, password: string) => {
  cy.visit('/auth');
  cy.get('input[type="email"]').type(email);
  cy.get('input[type="password"]').type(password);
  cy.get('button[type="submit"]').click();
  // Wait for successful login
  cy.url().should('not.include', '/auth');
});

Cypress.Commands.add('loginAsTeacher', () => {
  cy.login('teacher@example.com', 'password123');
  cy.url().should('include', '/teacher');
});

Cypress.Commands.add('loginAsStudent', () => {
  cy.login('student@example.com', 'password123');
  cy.url().should('include', '/student/dashboard');
});

Cypress.Commands.add('loginAsParent', () => {
  cy.login('parent@example.com', 'password123');
  cy.url().should('include', '/parent');
});

Cypress.Commands.add('signup', (role: string, firstName: string, lastName: string, email: string, password: string) => {
  cy.visit('/auth');
  // Switch to signup mode
  cy.get('button').contains(/sign up/i).click();
  
  // Select role if not first user
  if (role) {
    cy.get(`[data-cy="role-${role}"]`).click();
  }
  
  // Fill in signup form
  cy.get('input[name="firstName"]').type(firstName);
  cy.get('input[name="lastName"]').type(lastName);
  cy.get('input[type="email"]').type(email);
  cy.get('input[type="password"]').type(password);
  cy.get('button[type="submit"]').click();
});

// Command to clear local storage and cookies between tests
Cypress.Commands.add('clearAuth', () => {
  cy.window().then((win) => {
    win.localStorage.clear();
  });
  cy.clearCookies();
  cy.clearLocalStorage();
}); 