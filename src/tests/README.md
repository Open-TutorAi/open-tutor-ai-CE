# OpenTutorAI Test Suite

This directory contains unit tests for the OpenTutorAI application. The tests are designed to verify the functionality of components, ensure responsive design works correctly, and maintain quality throughout the development process.

## Running Tests

To run the tests, use one of the following npm commands:

```bash
# Run all tests once
npm run test

# Run tests in watch mode (tests rerun when files change)
npm run test:watch

# Run tests with coverage reporting
npm run test:coverage
```

## Test Structure

The tests are organized into the following categories:

- **Component Tests**: Located in `src/tests/components/`, these tests verify the behavior of specific UI components.
- **Application-level Tests**: Tests for application-wide features like the title handling.

## Test Files

- **AvatarSelection.test.js**: Tests for the avatar selection component, including rendering, selection behavior, and responsiveness.
- **responsive.test.js**: Dedicated tests for responsive behavior across different screen sizes.
- **title.test.js**: Tests to ensure the application title is correctly set to "OpenTutorAI".

## Adding New Tests

When adding new features or modifying existing ones, please add or update tests to ensure continued functionality. Follow these guidelines:

1. **Component Tests**: Create a test file in `src/tests/components/` named after the component being tested.
2. **Test Complete Scenarios**: Test both the "happy path" and edge cases.
3. **Mock External Dependencies**: Use Vitest's mocking capabilities to isolate the code being tested.
4. **Test Responsiveness**: For UI components, test behavior across different screen sizes.

## Test Utilities

The test suite uses:

- **Vitest**: For running tests and assertions
- **@testing-library/svelte**: For rendering and interacting with Svelte components
- **jsdom**: For simulating a DOM environment

## Coverage

Run `npm run test:coverage` to generate a coverage report. This will show which parts of the code are covered by tests and which need additional testing.

The coverage report will be available in the `coverage/` directory after running the command.
