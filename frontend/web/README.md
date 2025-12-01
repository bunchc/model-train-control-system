# Model Train Control System - Web UI

A modern, accessible React web application for real-time model train control and monitoring.

## Features

- 🚂 **Real-time Train Control** - Control speed, direction, and send commands to trains
- 📊 **Live Telemetry** - Monitor voltage, current, speed, and position in real-time
- 📱 **Responsive Design** - Mobile-first design that works on all devices
- 🌙 **Dark Mode** - System-aware theme switching (light/dark/system)
- ♿ **Accessible** - WCAG 2.2 AA compliant with keyboard navigation
- ⚡ **Fast & Modern** - Built with Vite, React 18, and TypeScript

## Tech Stack

- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite
- **Routing:** React Router v6
- **State Management:** TanStack Query (React Query)
- **Styling:** TailwindCSS
- **UI Components:** Headless UI + Heroicons
- **API Client:** Axios
- **Form Handling:** React Hook Form + Zod
- **Charts:** Recharts
- **Notifications:** React Hot Toast

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- Model Train Control System API running (default: http://localhost:8000)

### Installation

1. **Install dependencies:**

```bash
cd frontend/web
npm install
```

2. **Create environment file:**

```bash
cp .env.example .env
```

Edit `.env` and configure:

```env
# API Base URL
VITE_API_BASE_URL=http://localhost:8000

# Polling intervals (milliseconds)
VITE_TRAIN_STATUS_POLL_INTERVAL=2000
VITE_TRAIN_LIST_POLL_INTERVAL=5000
```

3. **Start development server:**

```bash
npm run dev
```

The application will be available at `http://localhost:3000`

### Build for Production

```bash
npm run build
```

Build output will be in `dist/` directory.

### Preview Production Build

```bash
npm run preview
```

## Development

### Available Scripts

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint
- `npm run format` - Format code with Prettier

## API Integration

The web UI integrates with the Model Train Control System API via:

1. **REST API** - For train commands and configuration
2. **Auto-polling** - React Query automatically refreshes data:
   - Train status: every 2 seconds
   - Train list: every 5 seconds
   - Controllers: every 10 seconds

## Accessibility

This application follows WCAG 2.2 AA guidelines:

- ✅ Semantic HTML5 elements
- ✅ ARIA labels and roles
- ✅ Keyboard navigation support
- ✅ Focus visible indicators
- ✅ Sufficient color contrast (4.5:1 minimum)

## Browser Support

- Chrome/Edge: last 2 versions
- Firefox: last 2 versions
- Safari: last 2 versions

## License

MIT License - See LICENSE file for details
