describe('Student Registration Test', () => {
  // Define credentials we'll use across tests - use a specific email format
  const studentCredentials = {
    firstName: 'Test',
    lastName: 'Student',
    email: 'test.student.5@example.com',
    password: 'password123'
  };

  // Log the credentials to the console for use in other tests
  before(() => {
    console.log('Student test credentials:', studentCredentials);
    // Write credentials to fixture file for other tests to use
    cy.writeFile('cypress/fixtures/student-credentials.json', studentCredentials);
  });

  beforeEach(() => {
    // Set up API intercepts - FIXED endpoint to match actual URL
    cy.intercept('POST', '**/auths/signup').as('signup'); // Removed 'api/v1/' to match actual endpoint
    cy.intercept('GET', '**/api/config').as('config');
    cy.intercept('GET', '**/auths/user-count').as('userCount');
    
    // Visit auth page
    cy.visit('/auth');
    cy.get('h2.text-2xl').should('be.visible');
  });

  it('should register a new student account', () => {
    // Switch to signup mode
    cy.contains('button', /sign up/i).click();
    cy.wait('@userCount');
    cy.contains('h1.text-3xl', 'Choose Your Role').should('be.visible');
    
    // Select student role
    cy.contains('.text-xl', 'Student')
      .parents('.bg-white')
      .find('button')
      .first()
      .click();

    // Fill registration form with our predefined credentials
    cy.get('#firstName').type(studentCredentials.firstName);
    cy.get('#lastName').type(studentCredentials.lastName);
    cy.get('#email').type(studentCredentials.email);
    cy.get('#password').type(studentCredentials.password);
    cy.get('#terms').check();
    
    // Submit form
    cy.get('form button[type="submit"]').click();

    // Verify signup success
    cy.wait('@signup', { timeout: 20000 })
      .its('response.statusCode')
      .should('be.oneOf', [200, 201]);
    
    // Verify redirect to dashboard
    cy.url().should('include', '/student/dashboard', { timeout: 20000 });
    
    // Log success message
    cy.log(`Successfully registered student: ${studentCredentials.email}`);
  });
});