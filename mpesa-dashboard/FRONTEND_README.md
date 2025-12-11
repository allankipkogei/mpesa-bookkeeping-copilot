# M-Pesa Bookkeeping Dashboard

A comprehensive React dashboard for managing M-Pesa transactions with AI-powered categorization and analytics.

## Features

### 🔐 Authentication
- JWT-based authentication with access and refresh tokens
- Secure login and registration
- Protected routes with automatic token refresh
- Logout functionality

### 📊 Dashboard
- Total amount, transaction count, and today's summary
- Weekly transaction trends chart
- Real-time data updates

### 💳 Transactions
- Upload M-Pesa statements (CSV, PDF, SMS exports)
- Automatic transaction parsing and import
- AI-powered auto-categorization (Food, Transport, Inventory, Personal, Utilities, Business)
- Category-based spending visualization
- Recent transactions table with filtering

### 📈 Analytics
- Monthly spending trends
- Cash flow analysis (incoming vs outgoing)
- Category breakdown with pie charts
- Recurring payment detection
- Budget insights

## Tech Stack

- **React 19.2** - UI framework
- **React Router 7.10** - Client-side routing
- **Axios 1.13** - HTTP client with JWT interceptors
- **Recharts 3.5** - Data visualization
- **TailwindCSS 3.4** - Utility-first styling

## Getting Started

### Prerequisites
- Node.js 18+ and npm
- Backend API running on http://127.0.0.1:8000

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at http://localhost:5173

## Authentication Flow

1. **Register**: Create new account at `/register`
   - Auto-login after successful registration
   - Redirects to dashboard

2. **Login**: Sign in at `/login`
   - JWT access token (expires in 15 minutes)
   - JWT refresh token (expires in 7 days)
   - Tokens stored in localStorage

3. **Protected Routes**: All routes except `/login` and `/register` require authentication
   - Automatic redirect to login if unauthenticated
   - Token refresh on 401 responses

4. **Logout**: Click logout in header
   - Clears tokens from localStorage
   - Redirects to login page

## API Endpoints Used

### Authentication
- `POST /api/auth/register/` - Create account
- `POST /api/auth/token/` - Get access + refresh tokens
- `POST /api/auth/token/refresh/` - Refresh access token

### Transactions
- `GET /api/transactions/` - List transactions
- `GET /api/transactions/summary/` - Dashboard summary
- `POST /api/transactions/upload/` - Upload statement
- `POST /api/transactions/categorize-all/` - AI categorization

### Analytics
- `GET /api/analytics/monthly/` - Monthly trends
- `GET /api/analytics/top-categories/` - Category breakdown
- `GET /api/analytics/cashflow/` - Cash flow analysis
- `GET /api/analytics/recurring-payments/` - Recurring patterns

## Project Structure

```
mpesa-dashboard/
├── src/
│   ├── components/
│   │   ├── CategoryStats.jsx       # Category pie chart
│   │   ├── CashflowChart.jsx       # Cash flow area chart
│   │   ├── Header.jsx              # App header with logout
│   │   ├── MonthlyAnalytics.jsx    # Monthly trends line chart
│   │   ├── PrivateRoute.jsx        # Auth route wrapper
│   │   ├── RecurringPayments.jsx   # Recurring payment detector
│   │   ├── Sidebar.jsx             # Navigation sidebar
│   │   ├── StatsCard.jsx           # Dashboard stat cards
│   │   ├── TransactionsTable.jsx   # Transaction list
│   │   ├── UploadStatement.jsx     # File upload component
│   │   └── WeeklyChart.jsx         # Weekly trends chart
│   ├── pages/
│   │   ├── Analytics.jsx           # Analytics dashboard
│   │   ├── Dashboard.jsx           # Main dashboard
│   │   ├── Login.jsx               # Login page
│   │   ├── Register.jsx            # Registration page
│   │   └── Transactions.jsx        # Transactions page
│   ├── utils/
│   │   └── axios.js                # Axios instance with interceptors
│   ├── App.jsx                     # Route configuration
│   └── main.jsx                    # App entry point
└── package.json
```

## Environment Variables

Create a `.env` file if you need to configure the backend URL:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api
```

## Common Issues

### 401 Unauthorized
- Tokens may have expired - try logging in again
- Backend might not be running on port 8000
- CORS configuration might need adjustment

### Blank Page
- Check browser console for errors
- Ensure TailwindCSS config has correct content paths
- Verify backend API is accessible

### File Upload Issues
- Ensure file is valid CSV, PDF, or TXT (SMS)
- Check file size (backend may have limits)
- Verify M-Pesa format matches expected structure

## Development

```bash
# Development mode with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Lint code
npm run lint
```

## License

MIT
