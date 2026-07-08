// End-to-end coverage for the teacher classroom management feature.
// Each test seeds its own users via cy.request() (fast, no UI flake), then
// drives the actual UI for the behavior under test, using the existing
// cy.login() custom command (see cypress/support/commands.ts) to authenticate.

const uniqueEmail = (prefix: string) =>
	`${prefix}-${Date.now()}-${Math.floor(Math.random() * 100000)}@e2e.test`;

const PASSWORD = 'password123';

const signupTeacher = (name = 'E2E Teacher') => {
	const email = uniqueEmail('teacher');
	return cy
		.request('POST', '/api/v1/auths/signup', { email, name, password: PASSWORD, role: 'teacher' })
		.then(() => ({ email, password: PASSWORD }));
};

const signupStudent = (name = 'E2E Student') => {
	const email = uniqueEmail('student');
	return cy
		.request('POST', '/api/v1/auths/signup', { email, name, password: PASSWORD, role: 'user' })
		.then(() => ({ email, password: PASSWORD }));
};

const createClassroomViaWizard = (name: string, description: string) => {
	cy.visit('/classrooms/new');

	// Step 1 — Subject
	cy.get('#classroom-name').type(name);
	cy.get('#classroom-description').type(description);
	cy.contains('button', 'Next').should('not.be.disabled').click();

	// Step 2 — Course
	cy.contains('button', 'Next').click();

	// Step 3 — Objectives
	cy.contains('button', 'Next').click();

	// Step 4 — Level
	cy.contains('button', 'Next').click();

	// Step 5 — Details
	cy.contains('button', 'Next').click();

	// Step 6 — Review
	cy.contains('button', 'Create Classroom').click();
};

describe('Classroom management', () => {
	beforeEach(() => {
		cy.clearAuth();
	});

	it('Teacher creates a classroom', () => {
		signupTeacher().then(({ email, password }) => {
			cy.login(email, password);

			createClassroomViaWizard('Algebra I', 'Intro to algebra');

			// Submitting navigates to the new classroom's detail page.
			cy.url().should('match', /\/classrooms\/[^/]+$/);

			cy.visit('/classrooms');
			cy.contains('[data-testid="classroom-card"]', 'Algebra I').should('be.visible');
		});
	});

	it('Teacher deletes a classroom', () => {
		signupTeacher().then(({ email, password }) => {
			cy.login(email, password);

			createClassroomViaWizard('To Delete', 'Will be removed');

			cy.visit('/classrooms');
			cy.contains('[data-testid="classroom-card"]', 'To Delete').within(() => {
				cy.get('[aria-label="Classroom options"]').click();
			});
			cy.contains('button', 'Delete').click();

			cy.get('[data-testid="delete-classroom-modal"]').within(() => {
				cy.contains('button', 'Delete Classroom').click();
			});

			cy.contains('[data-testid="classroom-card"]', 'To Delete').should('not.exist');
		});
	});

	it('Teacher starts a session', () => {
		signupTeacher().then(({ email, password }) => {
			cy.login(email, password);

			createClassroomViaWizard('Session Class', 'For session test');

			cy.url().should('match', /\/classrooms\/[^/]+$/);
			cy.contains('[role="tab"]', 'Présences').click();
			cy.contains('button', 'Démarrer une séance').click();

			cy.get('[data-testid="session-item"]').should('have.length.at.least', 1);
		});
	});

	it("Access control: a student cannot view another teacher's classroom", () => {
		signupTeacher().then(({ email: teacherEmail, password: teacherPassword }) => {
			cy.login(teacherEmail, teacherPassword);

			createClassroomViaWizard('Private Class', 'Owner only');

			cy.url().then((url) => {
				const classroomId = url.split('/classrooms/')[1];

				cy.clearAuth();

				signupStudent().then(({ email: studentEmail, password: studentPassword }) => {
					cy.login(studentEmail, studentPassword);
					cy.visit(`/classrooms/${classroomId}`);
					cy.contains('Accès non autorisé').should('be.visible');
				});
			});
		});
	});
});
