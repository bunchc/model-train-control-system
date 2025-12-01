# Model Train Control System - Web UI Architecture

## System Overview

The Web UI is a modern single-page application (SPA) built with React 18 and TypeScript, designed to provide real-time control and monitoring of model trains through a responsive, accessible interface.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Browser                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    React Application                      │  │
│  │                                                            │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │  │
│  │  │   Pages      │  │  Components  │  │   Hooks      │   │  │
│  │  │  (Routes)    │  │   (UI/Biz)   │  │  (State)     │   │  │
│  │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘   │  │
│  │         │                  │                  │            │  │
│  │         └──────────────────┴──────────────────┘            │  │
│  │                            │                                │  │
│  │                  ┌─────────▼─────────┐                     │  │
│  │                  │  React Query      │                     │  │
│  │                  │  (State Manager)  │                     │  │
│  │                  └─────────┬─────────┘                     │  │
│  │                            │                                │  │
│  │                  ┌─────────▼─────────┐                     │  │
│  │                  │  API Client       │                     │  │
│  │                  │  (Axios)          │                     │  │
│  │                  └─────────┬─────────┘                     │  │
│  └────────────────────────────┼──────────────────────────────┘  │
└────────────────────────────────┼─────────────────────────────────┘
                                 │ HTTP/REST
                                 ▼
                    ┌────────────────────────┐
                    │  Central API Server    │
                    │  (FastAPI - Port 8000) │
                    └────────────────────────┘
```

## Core Technologies

### Frontend Framework
- **React 18.3** - Component-based UI with concurrent features
- **TypeScript 5.4** - Static typing for better DX and fewer bugs
- **Vite 5.1** - Fast build tool with HMR

### State Management
- **TanStack Query 5.28** - Server state management with automatic caching, polling, and refetching
- **React Context** - Client state (theme, UI preferences)

### Routing
- **React Router 6.22** - Declarative routing with nested routes

### Styling
- **TailwindCSS 3.4** - Utility-first CSS framework
- **Headless UI 1.7** - Unstyled, accessible UI components
- **Heroicons 2.1** - Beautiful SVG icons

### Data Fetching
- **Axios 1.6** - HTTP client with interceptors for logging and error handling

### Form Management
- **React Hook Form 7.51** - Performant form handling
- **Zod 3.22** - Runtime type validation

### UI Enhancements
- **Recharts 2.12** - Composable charting library
- **React Hot Toast 2.4** - Lightweight notifications
- **date-fns 3.3** - Modern date utility library

## Project Structure

### Directory Organization

```
src/
├── api/                    # API client and data fetching
│   ├── client.ts          # Axios instance configuration
│   ├── types.ts           # TypeScript types from OpenAPI
│   ├── queries.ts         # React Query hooks
│   └── endpoints/         # API endpoint functions
│       ├── trains.ts      # Train CRUD operations
│       ├── config.ts      # Configuration endpoints
│       └── controllers.ts # Controller endpoints
│
├── components/            # React components
│   ├── ui/               # Base/primitive components
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Badge.tsx
│   │   ├── Modal.tsx
│   │   ├── Input.tsx
│   │   ├── Spinner.tsx
│   │   └── index.ts
│   │
│   ├── trains/           # Train-specific components
│   │   ├── TrainCard.tsx
│   │   ├── TrainGrid.tsx
│   │   ├── SpeedGauge.tsx
│   │   ├── ControlPanel.tsx
│   │   └── TelemetryDisplay.tsx
│   │
│   ├── layout/           # Layout components
│   │   ├── Header.tsx
│   │   ├── Footer.tsx
│   │   └── PageLayout.tsx
│   │
│   └── common/           # Shared components
│       ├── LoadingState.tsx
│       ├── EmptyState.tsx
│       ├── ErrorBoundary.tsx
│       └── StatusBadge.tsx
│
├── pages/                # Route components
│   ├── Dashboard.tsx     # Main dashboard
│   ├── TrainDetail.tsx   # Individual train view
│   ├── Configuration.tsx # System config
│   ├── Controllers.tsx   # Edge controllers
│   └── NotFound.tsx      # 404 page
│
├── hooks/                # Custom React hooks
│   └── useTheme.ts       # Theme management
│
├── utils/                # Utility functions
│   ├── cn.ts            # Class name utility
│   ├── formatting.ts    # Data formatters
│   └── constants.ts     # App constants
│
├── styles/               # Global styles
│   └── globals.css      # Tailwind + custom CSS
│
├── App.tsx              # Root component
├── main.tsx             # Application entry
├── router.tsx           # Route configuration
└── queryClient.ts       # React Query setup
```

## Data Flow

### 1. Component → API Request

```typescript
// User clicks button in component
const { mutate: sendCommand } = useSendCommand();

sendCommand({ 
  trainId: 'train-001', 
  command: { action: 'setSpeed', speed: 50 } 
});

// Hook (queries.ts)
export const useSendCommand = () => {
  return useMutation({
    mutationFn: ({ trainId, command }) => 
      sendTrainCommand(trainId, command),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ 
        queryKey: ['trains', variables.trainId, 'status'] 
      });
    },
  });
};

// API endpoint (endpoints/trains.ts)
export const sendTrainCommand = async (
  trainId: string, 
  command: TrainCommand
) => {
  const response = await apiClient.post(
    `/api/trains/${trainId}/command`, 
    command
  );
  return response.data;
};
```

### 2. API Response → UI Update

```typescript
// React Query automatically:
// 1. Caches the response
// 2. Updates all components using this data
// 3. Re-fetches on interval (if configured)
// 4. Invalidates related queries on mutation

const { data: status, isLoading, error } = useTrainStatus(trainId);

// Component automatically re-renders when:
// - Data is fetched
// - Data is updated
// - Related mutation succeeds
```

## State Management Strategy

### Server State (React Query)
- **Trains list** - Cached, auto-refresh every 5s
- **Train status** - Cached per train, auto-refresh every 2s
- **Controllers** - Cached, auto-refresh every 10s
- **Plugins** - Cached, refresh every 30s
- **Configuration** - Cached, manual refresh

### Client State (React Context/useState)
- **Theme preference** - Persisted to localStorage
- **UI state** - Modal open/closed, form state, etc.

## Real-time Updates

### Polling Strategy

```typescript
// Auto-polling configuration in React Query hooks
useQuery({
  queryKey: queryKeys.trainStatus(trainId),
  queryFn: () => getTrainStatus(trainId),
  refetchInterval: 2000,  // Poll every 2 seconds
  staleTime: 1000,        // Consider stale after 1s
  enabled: !!trainId,     // Only poll if trainId exists
});
```

### Optimistic Updates

```typescript
// UI updates immediately, rolls back on error
onMutate: async (newData) => {
  await queryClient.cancelQueries({ queryKey: ['trains'] });
  const previousData = queryClient.getQueryData(['trains']);
  queryClient.setQueryData(['trains'], (old) => [...old, newData]);
  return { previousData };
},
onError: (err, newData, context) => {
  queryClient.setQueryData(['trains'], context.previousData);
},
```

## Component Patterns

### Compound Components

```tsx
// Card is composed of sub-components
<Card>
  <CardHeader>
    <CardTitle>Train Name</CardTitle>
  </CardHeader>
  <CardContent>
    {/* Content */}
  </CardContent>
</Card>
```

### Render Props / Children as Function

```tsx
// Flexible pattern for customization
<LoadingState>
  {(isLoading) => isLoading ? <Spinner /> : <Content />}
</LoadingState>
```

### Custom Hooks

```tsx
// Encapsulate logic, promote reuse
const useTrainControl = (trainId: string) => {
  const { data: status } = useTrainStatus(trainId);
  const { mutate: sendCommand } = useSendCommand();
  
  const setSpeed = (speed: number) => {
    sendCommand({ trainId, command: { action: 'setSpeed', speed } });
  };
  
  return { status, setSpeed };
};
```

## Error Handling

### Error Boundary

```tsx
// Catches React component errors
<ErrorBoundary>
  <App />
</ErrorBoundary>
```

### API Error Handling

```typescript
// Axios interceptor logs all errors
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('[API Error]', error);
    return Promise.reject(error);
  }
);

// React Query handles retries
defaultOptions: {
  queries: {
    retry: 2,
    retryDelay: (attemptIndex) => 
      Math.min(1000 * 2 ** attemptIndex, 30000),
  },
}
```

### User-Facing Errors

```tsx
// Toast notifications for mutations
sendCommand(data, {
  onSuccess: () => toast.success('Command sent'),
  onError: (error) => toast.error(`Failed: ${error.message}`),
});

// Error states in UI
{error && (
  <div className="error-banner">
    <p>{error.message}</p>
  </div>
)}
```

## Performance Optimizations

### Code Splitting

```tsx
// Automatic route-based code splitting
const Dashboard = lazy(() => import('./pages/Dashboard'));
```

### Memoization

```tsx
// Prevent unnecessary re-renders
const MemoizedComponent = React.memo(ExpensiveComponent);

// Memoize expensive computations
const sortedTrains = useMemo(() => 
  trains.sort((a, b) => a.name.localeCompare(b.name)),
  [trains]
);
```

### Query Optimization

```typescript
// Prefetch data before navigation
queryClient.prefetchQuery({
  queryKey: ['train', trainId],
  queryFn: () => getTrainStatus(trainId),
});
```

## Accessibility Implementation

### Semantic HTML

```tsx
<nav aria-label="Main navigation">
  <header>
    <h1>Dashboard</h1>
  </header>
  <main>
    <article>...</article>
  </main>
</nav>
```

### ARIA Attributes

```tsx
<button 
  aria-label="Emergency stop train"
  aria-pressed={isActive}
>
  Stop
</button>

<input 
  aria-invalid={hasError}
  aria-describedby="error-message"
/>
```

### Keyboard Navigation

```tsx
// Focus management
const modalRef = useRef<HTMLDivElement>(null);

useEffect(() => {
  if (isOpen) {
    modalRef.current?.focus();
  }
}, [isOpen]);

// Keyboard handlers
onKeyDown={(e) => {
  if (e.key === 'Escape') closeModal();
}}
```

## Testing Strategy

### Unit Tests
- Component rendering
- User interactions
- Custom hooks
- Utility functions

### Integration Tests
- API client
- Query hooks
- Form submissions
- Navigation

### E2E Tests (Future)
- Complete user workflows
- Multi-page scenarios
- Error recovery

## Deployment

### Build Process

```bash
# 1. Install dependencies
npm install

# 2. Type check
npx tsc --noEmit

# 3. Lint
npm run lint

# 4. Build
npm run build

# Output: dist/
```

### Environment Variables

```env
# Production
VITE_API_BASE_URL=https://api.train-control.example.com

# Staging
VITE_API_BASE_URL=https://staging-api.train-control.example.com

# Development
VITE_API_BASE_URL=http://localhost:8000
```

### Static Hosting

Built for deployment to:
- Nginx/Apache
- S3 + CloudFront
- Netlify/Vercel
- GitHub Pages

## Future Enhancements

### Planned Features
- [ ] WebSocket integration for real-time push updates
- [ ] Historical telemetry charts
- [ ] Multi-train orchestration
- [ ] User authentication/authorization
- [ ] Track layout visualization
- [ ] Mobile native apps (React Native)
- [ ] PWA with offline support

### Technical Improvements
- [ ] Cypress E2E tests
- [ ] Storybook component documentation
- [ ] Bundle size optimization
- [ ] Performance monitoring
- [ ] Accessibility audit automation

## Resources

- [React Documentation](https://react.dev)
- [TanStack Query](https://tanstack.com/query)
- [TailwindCSS](https://tailwindcss.com)
- [Headless UI](https://headlessui.com)
- [Vite](https://vitejs.dev)

---

**Last Updated:** November 25, 2025
