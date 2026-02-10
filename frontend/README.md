# Frontend - Precious Market Watch

React-based user interface for the Precious Market Watch application.

## 🏗️ Architecture
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **Styling**: [Your CSS framework]
- **State Management**: [Redux/Context/Zustand]
- **Routing**: React Router v6
- **API Client**: Apollo Client / React Query
- **Testing**: Jest + React Testing Library

## 📦 Installation
```bash
cd frontend
npm install
```
## 🚀 Development
```bash
# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm test
```
## 🏗️ Project Structure

```text
frontend/
├── src/
│   ├── components/     # Reusable UI components
│   ├── pages/         # Page components
│   ├── hooks/         # Custom React hooks
│   ├── utils/         # Utility functions
│   ├── types/         # TypeScript definitions
│   ├── styles/        # Global styles
│   └── App.tsx        # Root component
├── public/            # Static assets
└── package.json
```

## 🔧 Configuration

Create .env.local file:

```env
VITE_API_URL=http://localhost:4000/graphql
VITE_WORDPRESS_URL=http://localhost:8080
VITE_GOOGLE_ANALYTICS_ID=UA-XXXXX
```

## 📚 Key Components

- MarketDashboard: Real-time precious metals prices
- ArticleFeed: AI-generated content display
- PriceCharts: Interactive historical price charts
- NewsTicker: Latest industry news

[Continue with API integration, theming, testing...]