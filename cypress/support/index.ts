/// <reference types="cypress" />

// Import commands.js using ES2015 syntax:
import './commands';

declare global {
  namespace Cypress {
    interface Chainable {
      login(email: string, password: string): Chainable<void>;
      loginAsTeacher(): Chainable<void>;
      loginAsStudent(): Chainable<void>;
      loginAsParent(): Chainable<void>;
      signup(role: string, firstName: string, lastName: string, email: string, password: string): Chainable<void>;
      clearAuth(): Chainable<void>;
    }
  }
} 