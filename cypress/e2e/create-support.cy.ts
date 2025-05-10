describe('Support Creation Test', () => {
  beforeEach(() => {
    // Load the stored student credentials
    cy.fixture('student-credentials.json').then((credentials) => {
      // Visit auth page and login
      cy.visit('/auth');
      cy.get('#email').type(credentials.email);
      cy.get('#password').type(credentials.password);
      cy.get('form button[type="submit"]').click();

      // Wait for redirect to dashboard
      cy.url().should('include', '/student/dashboard');
    });
  });

  it('should create a new support session', () => {
    // Click the + Support button
    cy.contains('button', 'Support').click();

    // Navigate to support creation page
    cy.visit('/student/support');

    // Step 1: Subject
    // Fill in the required fields
    cy.get('#supportTitle')
      .should('be.visible')
      .type('Understanding Linear Equations');
    
    cy.get('#shortDescription')
      .should('be.visible')
      .type('This support covers the basics of solving linear equations');
    
    // Select Mathematics subject
    cy.get('.grid-cols-1.sm\\:grid-cols-2.md\\:grid-cols-3.lg\\:grid-cols-4')
      .contains('Mathematics')
      .click();

    // Click Next
    cy.contains('button', 'Next')
      .should('not.be.disabled')
      .click();

    // Step 2: Course
    // Just click Next since course selection is optional
    cy.contains('button', 'Next')
      .should('not.be.disabled')
      .click();

    // Step 3: Objectives
    // Fill in learning objective
    cy.get('#learningObjective')
      .should('be.visible')
      .type('By the end of this support, I should be able to solve any linear equation');
    
    // Select "I'm preparing for an exam" option
    cy.contains("I'm preparing for an exam")
      .should('be.visible')
      .click();

    // Click Next
    cy.contains('button', 'Next')
      .should('not.be.disabled')
      .click();

    // Step 4: Level
    // Select High school level
    cy.contains('High school')
      .should('be.visible')
      .click();

    // Click Next
    cy.contains('button', 'Next')
      .should('not.be.disabled')
      .click();

    // Step 5: Details
    // Just click Next
    cy.contains('button', 'Next')
      .should('not.be.disabled')
      .click();

    // Step 6: Avatar
    // Just click Next
    cy.contains('button', 'Next')
      .should('not.be.disabled')
      .click();

    // Step 7: Review
    // Click Start
    cy.contains('button', 'Start')
      .should('not.be.disabled')
      .click();

    // Verify redirect to chat
    cy.url().should('include', '/student/chat');
  });
}); 