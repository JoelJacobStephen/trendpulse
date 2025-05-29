# TrendPulse - Frontend

A modern Vue.js 3 frontend for the TrendPulse application that visualizes global news topic trends in real-time.

## 🚀 Features

- **Real-time Topic Monitoring**: Live feed showing trending news topics as they emerge
- **Interactive World Map**: Geographic visualization of topic prevalence by country
- **Topic Analysis**: Detailed analytics including sentiment analysis and trend directions
- **Predictive Analytics**: AI-powered predictions for future topic trends
- **Responsive Design**: Modern, mobile-friendly interface built with Tailwind CSS
- **Date Range Filtering**: Flexible date selection with preset options
- **Auto-refresh**: Optional automatic updates for live data

## 🛠️ Tech Stack

- **Vue 3** - Progressive JavaScript framework with Composition API
- **Vuex 4** - State management for centralized data handling
- **Axios** - HTTP client for API communication
- **Tailwind CSS** - Utility-first CSS framework for styling
- **date-fns** - Modern JavaScript date utility library
- **Chart.js & Vue-ChartJS** - Data visualization components
- **Leaflet & Vue3-Leaflet** - Interactive maps (planned integration)

## 📦 Installation

### Prerequisites

- Node.js 16+ and npm
- Running TrendPulse backend server

### Quick Start

1. **Install dependencies**

   ```bash
   npm install
   ```

2. **Configure environment**

   ```bash
   cp env.example .env.local
   ```

   Edit `.env.local` and set your backend URL:

   ```env
   VUE_APP_API_URL=http://localhost:8000/api/v1
   ```

3. **Start development server**

   ```bash
   npm run dev
   ```

4. **Open browser**
   Navigate to `http://localhost:8080`

## 🔧 Configuration

### Environment Variables

| Variable                   | Default                        | Description                |
| -------------------------- | ------------------------------ | -------------------------- |
| `VUE_APP_API_URL`          | `http://localhost:8000/api/v1` | Backend API base URL       |
| `VUE_APP_TITLE`            | `TrendPulse`                   | Application title          |
| `VUE_APP_DEBUG`            | `true`                         | Enable debug mode          |
| `VUE_APP_REFRESH_INTERVAL` | `300000`                       | Auto-refresh interval (ms) |

### Backend Requirements

The frontend expects a backend server running with the following endpoints:

- `GET /api/v1/health` - Health check
- `GET /api/v1/topics` - Available topics
- `GET /api/v1/live` - Live trending topics
- `GET /api/v1/trends/{topic}` - Topic trend data
- `GET /api/v1/countries/{country}/topics` - Country-specific topics
- `GET /api/v1/predictions` - Trend predictions
- `GET /api/v1/statistics` - Application statistics

## 🏗️ Project Structure

```
frontend/
├── src/
│   ├── components/           # Vue components
│   │   ├── TopicSelector.vue        # Topic selection dropdown
│   │   ├── DateRangeSlider.vue      # Date range picker
│   │   ├── LiveFeed.vue             # Real-time trending feed
│   │   ├── WorldMapVisualization.vue # Global map component
│   │   └── TrendAnalysis.vue        # Analytics dashboard
│   ├── services/
│   │   └── APIService.js            # Backend API client
│   ├── store/
│   │   └── index.js                 # Vuex store configuration
│   ├── assets/
│   │   └── styles.css               # Global styles
│   ├── App.vue                      # Main application component
│   └── main.js                      # Application entry point
├── public/                          # Static assets
├── package.json                     # Dependencies and scripts
└── README.md                        # This file
```

## 🎨 Key Components

### TopicSelector

- Dropdown for selecting news topics
- Shows article counts and trend scores
- Automatically loads available topics from backend

### LiveFeed

- Real-time trending topics display
- Auto-refresh capability
- Interactive topic selection
- Trend indicators and sentiment analysis

### WorldMapVisualization

- Global view of topic trends by country
- Country selection for detailed analysis
- Trend intensity visualization
- Top countries ranking

### TrendAnalysis

- Detailed topic analytics
- Geographic distribution insights
- Predictive trend forecasting
- Sentiment analysis summaries

### DateRangeSlider

- Flexible date range selection
- Quick preset options (7 days, 30 days, etc.)
- Custom date input fields

## 📊 State Management

The application uses Vuex for centralized state management:

### Store Modules

- **Connection**: Backend connectivity status
- **Topics**: Available topics and selections
- **Trends**: Topic trend data and live updates
- **Geography**: Country-specific data
- **Predictions**: AI-generated forecasts
- **UI**: User interface state

### Key Actions

- `checkBackendConnection()` - Verify backend availability
- `loadAvailableTopics()` - Fetch topic list
- `loadLiveTrends()` - Get trending topics
- `loadTopicTrends()` - Load specific topic data
- `startAutoRefresh()` - Enable live updates

## 🚀 Available Scripts

| Command           | Description              |
| ----------------- | ------------------------ |
| `npm run serve`   | Start development server |
| `npm run dev`     | Alias for serve          |
| `npm run build`   | Build for production     |
| `npm run lint`    | Run ESLint               |
| `npm run preview` | Preview production build |

## 🎯 Usage Guide

### Basic Workflow

1. **Select a Topic**: Use the topic selector to choose a news category
2. **Set Date Range**: Pick a time period using presets or custom dates
3. **Monitor Live Feed**: Watch real-time trending topics in the sidebar
4. **Explore Geography**: Click countries on the map for detailed analysis
5. **Review Analytics**: Scroll down for in-depth topic insights
6. **Check Predictions**: View AI-powered trend forecasts

### Live Updates

- Enable auto-refresh in the live feed for real-time updates
- The app automatically refreshes trend data every 5 minutes
- Connection status indicator shows backend availability

### Filtering & Selection

- **Topic Filter**: Select specific news categories
- **Country Filter**: Focus on particular countries
- **Date Range**: Analyze historical or recent trends
- **Live vs Historical**: Switch between real-time and historical data

## 🐛 Troubleshooting

### Common Issues

**Backend Connection Failed**

- Verify backend server is running
- Check `VUE_APP_API_URL` in `.env.local`
- Ensure CORS is properly configured on backend

**No Data Loading**

- Check browser console for API errors
- Verify backend has processed some news articles
- Try refreshing with the refresh button

**Map Not Loading**

- Future feature - currently shows placeholder
- Will be implemented with Leaflet integration

### Development Tips

- Use Vue DevTools browser extension for debugging
- Check browser console for detailed error messages
- Monitor network tab for API request/response details

## 🚀 Deployment

### Production Build

```bash
npm run build
```

The `dist/` folder contains the production-ready files.

### Static Hosting

Deploy to any static hosting service:

- **Vercel**: Connect GitHub repo for auto-deployment
- **Netlify**: Drag and drop `dist` folder
- **GitHub Pages**: Enable in repository settings
- **AWS S3**: Upload to S3 bucket with static website hosting

### Environment Configuration

For production, set environment variables in your hosting platform:

- Set `VUE_APP_API_URL` to your production backend URL
- Configure any other environment-specific variables

## 🤝 Contributing

1. Follow Vue.js style guide
2. Use Composition API for new components
3. Add proper TypeScript types where beneficial
4. Test components before submitting
5. Update documentation for new features

## 📄 License

This project is part of the TrendPulse application suite.
