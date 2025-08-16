# Architecture Decisions

## Single Page Application Architecture

### Decision
The project uses a React Single Page Application (SPA) for all user interfaces, with the Python Flask backend serving only JSON APIs and the React build.

### Rationale

1. **Clean Separation of Concerns**
   - Frontend: React handles all UI rendering and routing
   - Backend: Flask serves only JSON APIs and static files
   - Clear boundaries between presentation and business logic

2. **Modern Development Experience**
   - React Router for client-side routing
   - Consistent TypeScript throughout the frontend
   - Better tooling and development workflow

3. **Maintainability**
   - All UI code in one place (React)
   - No HTML embedded in Python files
   - Easier to test and debug

4. **User Experience**
   - Seamless navigation between pages
   - No full page reloads
   - Better performance after initial load

### Implementation Details

- **React Router**: Handles `/`, `/config`, `/setup` routes
- **Flask Catch-all**: Serves `index.html` for all non-API routes
- **API Namespace**: All backend endpoints under `/api/*`
- **Static Files**: Served directly from React build folder

### Migration from Mixed Stack

Previously, the config page was embedded HTML in the Flask app. This has been migrated to:
- `ConfigPage.tsx`: Full React component with all configuration features
- `SetupPage.tsx`: WiFi setup and network configuration
- `App.tsx`: Main dashboard display

## Best Practices Implementation

### React (Frontend)
- ✅ Functional components with hooks
- ✅ Proper useEffect cleanup
- ✅ TypeScript for type safety
- ✅ React Router for SPA navigation
- ✅ Centralized API calls
- ✅ Error boundaries for fault tolerance

### Python/Flask (Backend)
- ✅ Configuration management class
- ✅ Proper error handling with specific exceptions
- ✅ RESTful API design
- ✅ Environment variables for secrets
- ✅ Input validation
- ✅ Logging instead of print statements
- ✅ Clean separation - no HTML in Python

### Areas for Future Improvement

1. **API Organization**
   - Consider Flask blueprints for API routes
   - Separate admin endpoints from public endpoints
   - Add API versioning (e.g., `/api/v1/*`)

2. **Testing**
   - Add unit tests for configuration manager
   - Add integration tests for API endpoints
   - Add React component tests with React Testing Library

3. **Performance**
   - Add response caching for expensive API calls
   - Implement proper production WSGI server (Gunicorn)
   - Add CDN for static assets

## Conclusion

The SPA architecture provides a clean, maintainable, and modern approach to building an IoT dashboard. The separation between React frontend and Flask API backend follows industry best practices and makes the codebase easier to understand, test, and extend.