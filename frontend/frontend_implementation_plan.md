# Frontend Development & Implementation Plan

This plan outlines the strategy for building the frontend application for the Coinfrs platform, aligning with the established backend architecture and Phase 1 MVP goals.

## Change Log

### Version 2.0 - 2025-07-24
**Major Revisions for MVP Focus**
- **Timeline**: Reduced from 12 weeks to 9 weeks for faster MVP delivery
- **Team Size**: Reduced from 4-5 to 2-3 developers
- **Technology Stack**: 
  - Kept MUI (Material-UI) for rapid component development
  - Retained Redux Toolkit for complex state management
  - Simplified monitoring and analytics for MVP phase
- **Project Structure**: Streamlined folder structure, removed unnecessary layers
- **Implementation Phases**: Consolidated from 10 phases to 5 focused phases
- **Testing Strategy**: Simplified to basic coverage for MVP
- **Removed from MVP Scope**:
  - Custom design system development
  - E2E testing infrastructure
  - Advanced monitoring and analytics
  - Mobile responsiveness optimization
  - Full accessibility compliance (relying on MUI defaults)
  - Performance optimization beyond basics
- **Added Clarifications**:
  - Explicit MVP vs Post-MVP feature delineation
  - Risk mitigation strategies
  - Progressive enhancement approach
  - Vertical slice development methodology

### Version 1.0 - Initial Draft
- Initial comprehensive plan with full feature set
- 12-week timeline with larger team
- Included advanced features and infrastructure

---

## 1. Technology Stack & Core Libraries

To ensure a modern, maintainable, and high-performance user interface while optimizing for MVP delivery speed:

### Core Stack
- **Framework:** **React 18** with **TypeScript** - Robust, type-safe foundation ideal for financial applications
- **Build Tool:** **Vite** - Fast development experience and optimal build performance
- **UI Library:** **MUI (Material-UI)** - Comprehensive, accessible components for rapid B2B dashboard development
- **State Management:** **Redux Toolkit** - Industry standard for complex financial state management
- **Routing:** **React Router v6** - Standard routing solution for React applications
- **HTTP Client:** **Axios** - Robust HTTP library with interceptor support for JWT handling
- **Charts:** **Recharts** - React-based charting library for financial visualizations
- **Forms:** **React Hook Form** - Performant forms with built-in validation
- **Testing:** **Vitest** and **React Testing Library** - Modern, fast testing framework

### Additional Libraries
- **Date Handling:** **date-fns** - Lightweight date manipulation
- **Validation:** **Zod** - Runtime type validation
- **Development:** **ESLint**, **Prettier** - Code quality and formatting

## 2. Project Setup & Structure

The frontend will be created as a new directory at the project root, parallel to the backend.

### Initial Setup

1. **Bootstrap the application:**
   ```bash
   npm create vite@latest frontend -- --template react-ts
   cd frontend
   ```

2. **Install core dependencies:**
   ```bash
   # Core libraries
   npm install @mui/material @emotion/react @emotion/styled @mui/x-data-grid
   npm install @reduxjs/toolkit react-redux react-router-dom
   npm install axios react-hook-form zod @hookform/resolvers
   npm install recharts date-fns
   
   # Development dependencies
   npm install -D vitest @testing-library/react @testing-library/user-event
   npm install -D @types/react @types/react-dom
   npm install -D eslint prettier eslint-config-prettier
   ```

3. **Project Structure (`frontend/src`):**
   ```
   src/
   ├── api/              # API endpoint definitions and axios configuration
   │   ├── client.ts     # Axios instance with interceptors
   │   ├── auth.ts       # Authentication endpoints
   │   ├── portfolio.ts  # Portfolio management endpoints
   │   ├── entity.ts     # Entity management endpoints
   │   ├── datasource.ts # Data source endpoints
   │   └── transaction.ts # Transaction endpoints
   ├── app/              # Redux store configuration
   │   ├── store.ts      # Store setup
   │   ├── hooks.ts      # Typed Redux hooks
   │   └── slices/       # Redux slices
   │       ├── authSlice.ts
   │       ├── portfolioSlice.ts
   │       ├── entitySlice.ts
   │       └── transactionSlice.ts
   ├── components/       # Reusable UI components
   │   ├── common/       # Generic components (LoadingSpinner, ErrorBoundary)
   │   ├── forms/        # Form components
   │   └── charts/       # Chart components
   ├── features/         # Feature-specific components and logic
   │   ├── auth/         # Authentication components
   │   ├── portfolio/    # Portfolio management
   │   ├── entity/       # Entity management
   │   ├── datasources/  # Data source management
   │   ├── onboarding/   # Onboarding flow
   │   └── transactions/ # Transaction management
   ├── hooks/            # Custom React hooks
   ├── layouts/          # Layout components
   │   ├── AuthLayout.tsx
   │   └── DashboardLayout.tsx
   ├── pages/            # Page components (route endpoints)
   ├── types/            # TypeScript type definitions
   ├── utils/            # Helper functions
   └── config/           # Configuration files
       ├── constants.ts
       └── theme.ts      # MUI theme configuration
   ```

## 3. MVP Implementation Timeline (9 Weeks)

### Phase 1: Foundation & Authentication (Weeks 1-2)

**Objective:** Establish the application foundation and implement authentication flows.

**Deliverables:**
1. **Project Setup**
   - Initialize Vite + React + TypeScript project
   - Configure ESLint, Prettier, and git hooks
   - Set up folder structure and initial routing

2. **MUI Theme Configuration**
   - Create custom theme matching Coinfrs branding
   - Configure typography, colors, and spacing
   - Set up global styles

3. **Authentication Implementation**
   - Create login and registration pages
   - Implement Google OAuth redirect flow
   - Build Email OTP request/verify forms
   - Create auth Redux slice for state management
   - Configure axios interceptors for JWT handling
   - Implement automatic token refresh

4. **Layout Components**
   - Build AuthLayout for public pages
   - Create DashboardLayout with navigation
   - Implement PrivateRoute wrapper

### Phase 2: Portfolio & Entity Management (Weeks 3-4)

**Objective:** Enable users to create and manage their organizational structure.

**Deliverables:**
1. **API Integration**
   - Create portfolio and entity API functions
   - Implement error handling and loading states

2. **State Management**
   - Build portfolioSlice and entitySlice
   - Implement CRUD operations in Redux

3. **UI Components**
   - Portfolio dashboard overview
   - Create/Edit forms with validation
   - MUI DataGrid for listings
   - Delete confirmation dialogs

4. **Navigation**
   - Portfolio detail pages
   - Entity management within portfolios

### Phase 3: Data Source Management & Onboarding (Weeks 5-6)

**Objective:** Implement the dynamic onboarding flow and exchange connections.

**Deliverables:**
1. **Onboarding Wizard**
   - Multi-step form component
   - Progress indicator
   - Step validation and navigation

2. **Data Source Connection**
   - Secure API key input forms
   - Real-time validation UI
   - Connection status display

3. **Account Mapping**
   - Fetch and display sub-accounts
   - Location group mapping interface
   - Mapping confirmation flow

4. **State Management**
   - dataSourceSlice for connection state
   - Persist onboarding progress

### Phase 4: Financial Statement Close Process (Weeks 7-8)

**Objective:** Deliver core MVP functionality for transaction management and PnL calculation.

**Deliverables:**
1. **Transaction Management**
   - Transaction list with virtualization
   - Filtering and search capabilities
   - Bulk selection support

2. **Classification Interface**
   - Inline editing for classification
   - Dropdown menus for categories
   - Validation and error handling

3. **PnL Calculation**
   - Trigger calculation button
   - Progress indicator for async task
   - Results display dashboard

4. **Export Functionality**
   - CSV download for journal entries
   - Export configuration options
   - Download progress indicator

### Phase 5: Polish & Testing (Week 9)

**Objective:** Ensure quality and stability for MVP launch.

**Deliverables:**
1. **Error Handling**
   - Global error boundary
   - User-friendly error messages
   - Retry mechanisms

2. **Loading States**
   - Skeleton screens
   - Progress indicators
   - Optimistic updates

3. **Testing**
   - Unit tests for critical functions
   - Integration tests for API calls
   - Component tests for key workflows

4. **Performance**
   - Code splitting setup
   - Lazy loading for routes
   - Bundle size optimization

## 4. Development Approach

### Principles
1. **Vertical Slices**: Build complete features end-to-end
2. **API-First**: Generate TypeScript types from OpenAPI schema
3. **Progressive Enhancement**: MVP first, iterate based on feedback
4. **Component Reusability**: Build once, use everywhere

### Code Standards
- TypeScript strict mode enabled
- ESLint + Prettier for consistency
- Conventional commits for clear history
- Component and function documentation

### State Management Strategy
- **Redux Toolkit** for server state and complex UI state
- **React Hook Form** for form state
- **URL state** for filters and pagination
- **Local state** for component-specific UI

## 5. MVP vs Post-MVP Features

### MVP Scope (Must-Have)
- Google OAuth and Email OTP authentication
- Portfolio and entity CRUD operations
- Data source connection (Binance, Fireblocks)
- Basic transaction list and classification
- Manual PnL calculation trigger
- CSV export for journal entries
- Essential error handling and loading states

### Post-MVP Enhancements
- Advanced data visualizations
- Real-time updates via WebSocket
- Bulk operations and shortcuts
- Mobile responsive design
- Full WCAG 2.1 AA accessibility
- Advanced filtering and search
- Audit trail viewing
- Multi-language support
- Dark mode
- Keyboard shortcuts
- Export templates

## 6. Team Structure & Resources

### MVP Team (2-3 developers)
- **1 Senior Frontend Developer** (Lead)
  - Architecture decisions
  - Authentication implementation
  - Code reviews
  
- **1-2 Mid-level Frontend Developers**
  - Feature implementation
  - Testing
  - Bug fixes

### Resource Allocation
- Week 1-2: Entire team on foundation
- Week 3-8: Split features between developers
- Week 9: Entire team on polish and testing

## 7. Risk Mitigation

### Technical Risks
1. **API Integration Delays**
   - Mitigation: Use mock data and MSW for development
   
2. **State Management Complexity**
   - Mitigation: Clear Redux patterns and documentation

3. **Performance Issues**
   - Mitigation: Early virtualization implementation

### Timeline Risks
1. **Feature Creep**
   - Mitigation: Strict MVP scope adherence
   
2. **Integration Issues**
   - Mitigation: Early and continuous backend integration

## 8. Success Metrics

### Technical Metrics
- **Performance**: First Contentful Paint < 2s
- **Bundle Size**: Initial load < 300KB
- **Test Coverage**: >60% for critical paths
- **Build Time**: < 30 seconds

### User Experience Metrics
- **Time to First Transaction**: < 5 minutes
- **Error Rate**: < 0.5%
- **API Response Time**: < 200ms (p95)

## 9. Development Environment

### Prerequisites
- Node.js 18+ LTS
- npm 9+ or yarn 1.22+
- Git 2.34+

### Environment Variables
```env
VITE_API_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=your_google_client_id
VITE_APP_ENV=development
```

### Scripts
```json
{
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "lint": "eslint src --ext ts,tsx",
    "format": "prettier --write src"
  }
}
```

## 10. Deployment Strategy

### MVP Deployment
- Single-page application served via CDN
- Environment-specific builds
- API URL configuration via environment variables

### Post-MVP Considerations
- CI/CD pipeline setup
- Blue-green deployments
- Feature flags for gradual rollouts
- Performance monitoring integration