# Test Module Documentation

This directory contains all test files for the frontend React components. Each test file is thoroughly documented with JSDoc comments explaining what each test does and why.

## Test Structure

```
src/__tests__/
├── About.test.jsx          # Tests for About component
├── AstroGallery.test.jsx   # Tests for AstroGallery component
├── Footer.test.jsx         # Tests for Footer component
├── Gallery.test.jsx        # Tests for Gallery component
├── HomePage.test.jsx       # Tests for HomePage component
├── Navbar.test.jsx         # Tests for Navbar component
└── README.md              # This documentation file
```

## Test Categories

### 1. **HomePage Component Tests**

- **Purpose**: Tests the main landing page functionality
- **Key Features Tested**:
  - Loading states during API calls
  - Profile data rendering after successful API calls
  - Error handling when API calls fail
  - Router integration

### 2. **AstroGallery Component Tests**

- **Purpose**: Tests the dynamic astrophotography gallery
- **Key Features Tested**:
  - Loading states during API calls
  - Filter functionality (Landscape, Deep Sky, etc.)
  - Image rendering with proper alt text
  - Modal functionality when images are clicked
  - Error handling for failed API calls

### 3. **About Component Tests**

- **Purpose**: Tests the user profile/about section
- **Key Features Tested**:
  - Conditional rendering when no profile data exists
  - Bio text rendering with line breaks
  - Profile image rendering with correct attributes

### 4. **Gallery Component Tests**

- **Purpose**: Tests the static gallery with predefined categories
- **Key Features Tested**:
  - Static gallery items rendering (ASTRO PHOTOGRAPHY, LANDSCAPE PHOTOGRAPHY, PROGRAMMING)
  - Text content with line breaks
  - Background image styling (no img tags)

### 5. **Navbar Component Tests**

- **Purpose**: Tests the site navigation
- **Key Features Tested**:
  - Logo rendering with alt text
  - Navigation links (Astrophotography, Programming, Contact)
  - Transparent styling prop functionality
  - React Router integration

### 6. **Footer Component Tests**

- **Purpose**: Tests the site footer
- **Key Features Tested**:
  - Copyright text rendering
  - Static content display

## Running Tests

### In Docker (Recommended)

```bash
# Run all tests
docker-compose exec portfolio-fe npm test

# Run tests in watch mode
docker-compose exec portfolio-fe npm test -- --watch

# Run tests with coverage
docker-compose exec portfolio-fe npm test -- --coverage
```

### Locally (if Node.js is installed)

```bash
cd frontend
npm test
```

## Test Configuration

Tests are configured using:

- **Jest**: Test runner and assertion library
- **React Testing Library**: Component testing utilities
- **@testing-library/jest-dom**: Custom DOM matchers
- **JSDOM**: Browser environment simulation

## Mock Strategy

### API Services

All API calls are mocked using Jest mocks:

- `fetchProfile`: Mocked in About and HomePage tests
- `fetchBackground`: Mocked in HomePage and AstroGallery tests
- `fetchAstroImages`: Mocked in AstroGallery tests
- `fetchAstroImage`: Mocked in AstroGallery tests

### Router Context

Components using React Router are wrapped in `BrowserRouter` for testing:

```javascript
const renderWithRouter = component => {
  return render(<BrowserRouter>{component}</BrowserRouter>);
};
```

## Test Best Practices

### 1. **Async Testing**

- Use `waitFor()` for async operations
- Wrap state updates in `act()` when needed
- Mock slow API calls to test loading states

### 2. **Accessibility Testing**

- Test alt text for images
- Verify proper text content
- Check for proper semantic HTML structure

### 3. **Error Handling**

- Test error states and error messages
- Verify graceful degradation
- Ensure user-friendly error messages

### 4. **Mock Management**

- Clear mocks between tests using `beforeEach`
- Use realistic mock data
- Test both success and failure scenarios

## Test Documentation

Each test file includes:

- **File-level documentation**: Explains what the component does
- **Test suite documentation**: Describes the component's features
- **Individual test documentation**: Explains what each test verifies
- **Inline comments**: Clarify complex test logic

## Coverage Goals

Current test coverage includes:

- ✅ Component rendering
- ✅ User interactions (clicks, filters)
- ✅ API integration (mocked)
- ✅ Error handling
- ✅ Loading states
- ✅ Router integration

## Adding New Tests

When adding new tests:

1. **Follow the existing pattern**:

   ```javascript
   /**
    * Test: [Brief description]
    *
    * Verifies that:
    * - [Specific behavior 1]
    * - [Specific behavior 2]
    * - [Specific behavior 3]
    */
   it('[test description]', async () => {
     // Test implementation
   });
   ```

2. **Mock external dependencies** (APIs, router, etc.)

3. **Test both success and error scenarios**

4. **Include accessibility considerations**

5. **Use descriptive test names and documentation**

## Troubleshooting

### Common Issues

1. **"toBeInTheDocument is not a function"**

   - Ensure `@testing-library/jest-dom` is imported in each test file

2. **"useLocation() may be used only in the context of a <Router>"**

   - Wrap components in `BrowserRouter` for testing

3. **React act() warnings**

   - Wrap async operations in `act()` when needed
   - Use `waitFor()` for assertions on async state changes

4. **Tests timing out**
   - Check for infinite loops in mocks
   - Ensure proper cleanup in `beforeEach`/`afterEach`

### Debug Tips

- Use `screen.debug()` to see the rendered DOM
- Add `console.log()` statements in tests for debugging
- Use `--verbose` flag for detailed test output
- Check Jest configuration in `jest.config.js`
