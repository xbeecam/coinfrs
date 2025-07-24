# Frontend Development & Implementation Plan

This plan outlines the strategy for building the frontend application for the Coinfrs platform, aligning with the established backend architecture and Phase 1 MVP goals.

### **1. Technology Stack & Core Libraries**

To ensure a modern, maintainable, and high-performance user interface, I recommend the following stack:

*   **Framework:** **React 18** with **TypeScript**. This provides a robust, type-safe foundation that is ideal for a data-intensive financial application.
*   **Bootstrapping:** **Vite**. It offers a significantly faster development experience compared to Create React App.
*   **Styling:** **MUI (Material-UI)**. MUI provides a comprehensive suite of well-tested, accessible UI components that are perfect for building a professional, data-heavy dashboard quickly. It aligns well with the B2B SaaS nature of the product.
*   **State Management:** **Redux Toolkit**. For a financial application with complex state (user data, portfolios, transactions, UI state), Redux Toolkit is the industry standard, providing predictable state management and excellent developer tools.
*   **Routing:** **React Router v6**. The standard for routing in React applications.
*   **API Communication:** **Axios**. A dedicated library for making HTTP requests, with built-in support for interceptors, which will be crucial for handling JWT token injection and refresh logic.
*   **Charting:** **Recharts**. A composable charting library built with React and D3, suitable for displaying financial data.
*   **Testing:** **Vitest** and **React Testing Library**. A modern testing framework that is fast, compatible with Vite, and encourages good testing practices.

### **2. Project Setup & Structure**

A new `frontend` directory will be created at the project root, parallel to the `backend` directory.

1.  **Bootstrap the application:**
    ```bash
    npm create vite@latest frontend -- --template react-ts
    ```
2.  **Install core dependencies:**
    ```bash
    cd frontend
    npm install @mui/material @emotion/react @emotion/styled @reduxjs/toolkit react-redux react-router-dom axios recharts
    npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event
    ```
3.  **Proposed Folder Structure (`frontend/src`):**
    ```
    src/
    ├── api/              # Axios instances and API endpoint definitions
    ├── app/              # Redux store, slices, and configuration
    ├── assets/           # Static assets (images, fonts)
    ├── components/       # Reusable UI components (e.g., Button, Chart, DataTable)
    ├── features/         # Components and logic for specific features (e.g., auth, portfolio)
    ├── hooks/            # Custom React hooks (e.g., useAuth)
    ├── layouts/          # Main application layouts (e.g., DashboardLayout, AuthLayout)
    ├── pages/            # Top-level page components for each route
    ├── styles/           # Global styles and theme configuration
    ├── types/            # TypeScript type definitions
    └── utils/            # Utility functions
    ```

### **3. Phased Implementation Plan**

This plan aligns with the backend epics and the user journey defined in the PRD.

**Phase 1: Foundation & Authentication**

*   **Objective:** Allow users to sign up and log in. Establish the basic application shell.
*   **Tasks:**
    1.  **Setup Project:** Initialize the React app with Vite, install dependencies, and set up the folder structure.
    2.  **Configure MUI Theme:** Create a custom MUI theme (`styles/theme.ts`) to align with the Coinfrs brand.
    3.  **Implement Routing:** Set up React Router with public (login, register) and private (dashboard) routes. Create a `PrivateRoute` component that checks for authentication status.
    4.  **Build Layouts:** Create an `AuthLayout` for login pages and a `DashboardLayout` (with a sidebar and header) for the main application.
    5.  **Implement Authentication Flow:**
        *   Create Login and Registration pages based on the `authentication_guide.md`.
        *   Implement the **Google OAuth** and **Email OTP** flows.
        *   Create an `authSlice` in Redux to manage user state, tokens, and authentication status.
        *   Set up an Axios interceptor to automatically attach the JWT access token to all outgoing requests.
        *   Implement token refresh logic within another Axios interceptor to handle expired access tokens seamlessly.

**Phase 2: Core Portfolio & Entity Management**

*   **Objective:** Enable users to create their organizational structure and view their core data.
*   **Tasks:**
    1.  **Portfolio & Entity API:** Define API functions in `api/portfolio.ts` and `api/entity.ts` to interact with the backend CRUD endpoints.
    2.  **Redux State:** Create `portfolioSlice` and `entitySlice` to manage the respective data in the store.
    3.  **Dashboard Page:** Create a main dashboard page that provides an overview of portfolios.
    4.  **Portfolio/Entity Forms:** Build reusable forms (using libraries like `Formik` or `React Hook Form`) for creating and editing portfolios and entities.
    5.  **Data Display:** Use MUI's `DataGrid` component to display lists of portfolios and entities in a clean, sortable, and filterable table.

**Phase 3: Data Source Management & Onboarding**

*   **Objective:** Fulfill the dynamic onboarding user journey from the PRD.
*   **Tasks:**
    1.  **Data Source API & State:** Create `dataSourceApi.ts` and a `dataSourceSlice` to manage API keys and validation status.
    2.  **Onboarding Workflow:** Build a multi-step form/wizard for the onboarding process.
    3.  **Add Data Source:** Create a secure form for users to input their Binance/Fireblocks API keys.
    4.  **API Key Validation:** Implement the frontend logic to call the `/api/v1/datasources/{id}/validate` endpoint and provide real-time feedback to the user.
    5.  **Location Group Mapping:** After successful validation, fetch and display the sub-accounts, allowing the user to map them to Location Groups as described in the PRD.

**Phase 4: Financial Statement Close Process (FSCP) - MVP**

*   **Objective:** Deliver the core value proposition: transaction classification and PnL calculation.
*   **Tasks:**
    1.  **Transaction View:** Create a page to display transactions from the canonical layer, using a virtualized list or infinite scrolling for performance.
    2.  **Transaction Classification:** Implement the UI for manual transaction classification. This will likely involve dropdowns or editable fields within the transaction table.
    3.  **PnL Calculation Trigger:** Add a button to initiate the asynchronous PnL calculation Celery task.
    4.  **Display Results:** Fetch and display the results of the PnL calculation, likely in a summary view and with updated transaction details.
    5.  **CSV Export:** Implement a button to download the generated Journal Entry CSV file.
