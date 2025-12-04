# Web UI Setup Guide

Complete setup instructions for the Model Train Control System Web UI.

## Quick Start (TL;DR)

```bash
cd frontend/web
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:3000

## Detailed Setup

### Step 1: System Requirements

**Required:**

- Node.js 18.x or higher
- npm 9.x or higher (comes with Node.js)

**Optional:**

- yarn or pnpm (alternative package managers)

**Verify installation:**

```bash
node --version  # Should be v18.0.0 or higher
npm --version   # Should be 9.0.0 or higher
```

### Step 2: Install Dependencies

```bash
cd frontend/web
npm install
```

This installs:

- React and React DOM
- TypeScript
- Vite build tool
- TailwindCSS
- React Query
- Axios
- All other dependencies

**Troubleshooting:**

- If you see peer dependency warnings, they're usually safe to ignore
- For `EACCES` errors, avoid using `sudo`. Fix npm permissions instead
- Clear cache if installation fails: `npm cache clean --force`

### Step 3: Environment Configuration

```bash
cp .env.example .env
```

Edit `.env`:

```env
# Central API URL (required)
VITE_API_BASE_URL=http://localhost:8000

# Optional: Adjust polling intervals (milliseconds)
VITE_TRAIN_STATUS_POLL_INTERVAL=2000
VITE_TRAIN_LIST_POLL_INTERVAL=5000
```

**Important:**

- Ensure the Central API is running before starting the web UI
- The API URL must include the protocol (`http://` or `https://`)
- No trailing slash on the URL

### Step 4: Start Development Server

```bash
npm run dev
```

Output:

```
VITE v5.1.6  ready in 423 ms

➜  Local:   http://localhost:3000/
➜  Network: use --host to expose
➜  press h to show help
```

**Vite Dev Server Features:**

- Hot Module Replacement (HMR) - Changes reflect instantly
- Fast startup (~500ms)
- Automatic browser refresh on file changes

### Step 5: Verify Setup

1. Open http://localhost:3000 in your browser
2. You should see the Dashboard page
3. Check browser console for errors (F12)
4. Verify API connection:
   - If trains are configured, they should appear
   - If no trains, you'll see "No trains configured"
   - If API is down, you'll see a connection error

## Development Workflow

### Running Commands

```bash
# Start dev server
npm run dev

# Type check (without building)
npx tsc --noEmit

# Lint code
npm run lint

# Format code
npm run format

# Build for production
npm run build

# Preview production build
npm run preview
```

### File Watching

Vite watches these files automatically:

- `src/**/*.{ts,tsx,js,jsx}`
- `index.html`
- `vite.config.ts`
- `tailwind.config.js`
- `package.json`

**Note:** Changes to `.env` require server restart.

### Hot Module Replacement (HMR)

HMR updates the browser without full page reload:

- ✅ Component state preserved
- ✅ Fast feedback loop
- ✅ CSS updates instantly

If HMR breaks:

1. Save file again
2. Refresh browser
3. Restart dev server

## Building for Production

### Standard Build

```bash
npm run build
```

Output: `dist/` directory

Build process:

1. Type checking with TypeScript
2. Bundling with Vite
3. Minification
4. Code splitting
5. Asset optimization

Build output:

```
dist/
├── assets/
│   ├── index-[hash].js    # Main bundle
│   ├── vendor-[hash].js   # Dependencies
│   └── index-[hash].css   # Styles
├── index.html
└── vite.svg
```

### Production Preview

```bash
npm run preview
```

Serves the `dist/` folder at http://localhost:4173

**Use this to:**

- Test production build locally
- Verify bundle size
- Check for build issues

### Environment-Specific Builds

**Staging:**

```bash
VITE_API_BASE_URL=https://staging-api.example.com npm run build
```

**Production:**

```bash
VITE_API_BASE_URL=https://api.example.com npm run build
```

Or use `.env.production`:

```env
VITE_API_BASE_URL=https://api.example.com
```

Then: `npm run build` (automatically uses `.env.production`)

## Deployment

### Static File Hosting

The built app is static files that can be hosted anywhere:

**Nginx:**

```nginx
server {
    listen 80;
    server_name train-control.example.com;
    root /var/www/train-control/dist;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API proxy (optional)
    location /api {
        proxy_pass http://localhost:8000;
    }
}
```

**Apache (.htaccess):**

```apache
<IfModule mod_rewrite.c>
  RewriteEngine On
  RewriteBase /
  RewriteRule ^index\.html$ - [L]
  RewriteCond %{REQUEST_FILENAME} !-f
  RewriteCond %{REQUEST_FILENAME} !-d
  RewriteRule . /index.html [L]
</IfModule>
```

### Docker Deployment

**Dockerfile:**

```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

**Build and run:**

```bash
docker build -t train-control-web .
docker run -p 80:80 train-control-web
```

### Cloud Platforms

**Netlify:**

```bash
npm install -g netlify-cli
netlify deploy --prod
```

**Vercel:**

```bash
npm install -g vercel
vercel --prod
```

**AWS S3 + CloudFront:**

```bash
aws s3 sync dist/ s3://your-bucket-name
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

## Troubleshooting

### Port Already in Use

**Error:** `Port 3000 is already in use`

**Solution:**

```bash
# Change port
npm run dev -- --port 3001

# Or kill process using port 3000
lsof -ti:3000 | xargs kill
```

### Module Not Found

**Error:** `Cannot find module '@/components/...'`

**Solution:**

1. Verify path aliases in `tsconfig.json`
2. Restart TypeScript server in VS Code (Cmd+Shift+P → "Restart TS Server")
3. Restart dev server

### Type Errors

**Error:** TypeScript compilation errors

**Solution:**

```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install

# Update TypeScript
npm install typescript@latest --save-dev
```

### Build Fails

**Error:** Build process crashes

**Solution:**

```bash
# Increase Node memory
NODE_OPTIONS=--max-old-space-size=4096 npm run build

# Check for circular dependencies
npx madge --circular src/
```

### Styles Not Applying

**Error:** Tailwind classes not working

**Solution:**

1. Verify `globals.css` imports Tailwind directives
2. Check `tailwind.config.js` content paths
3. Restart dev server
4. Clear browser cache

### API Connection Failed

**Error:** `Failed to fetch trains` or CORS error

**Solution:**

1. Verify API is running: `curl http://localhost:8000/api/health`
2. Check `VITE_API_BASE_URL` in `.env`
3. Verify API CORS settings allow frontend origin
4. Check browser network tab for actual error

## Performance Tips

### Development

- Use `npm run dev` (not `npm start`)
- Close unused browser tabs
- Disable browser extensions during development
- Use React DevTools for debugging

### Production

- Enable gzip/brotli compression on server
- Use CDN for static assets
- Enable caching headers
- Monitor bundle size: `npm run build -- --report`

## IDE Setup

### VS Code Extensions

Recommended extensions:

- ESLint
- Prettier
- Tailwind CSS IntelliSense
- TypeScript Error Translator
- Error Lens

### Settings

`.vscode/settings.json`:

```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  },
  "typescript.tsdk": "node_modules/typescript/lib"
}
```

## Next Steps

After setup:

1. Read `ARCHITECTURE.md` for system design
2. Explore `src/components/` for examples
3. Check `src/api/` for API integration patterns
4. Review `src/pages/` for routing structure

## Getting Help

- GitHub Issues: https://github.com/bunchc/model-train-control-system/issues
- Documentation: See `docs/` in repository root
- Architecture: See `ARCHITECTURE.md` in this directory

---

**Happy Building! 🚂**
