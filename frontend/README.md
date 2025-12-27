# OdyssAI Frontend

Modern React frontend for the OdyssAI travel planning system.

## Tech Stack

- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **shadcn/ui** + **Radix UI** for accessible components
- **React Router** for navigation
- **React Query** for data fetching

## Features

- **Trip Planning Wizard**: Multi-step workflow for planning trips
  - Destination discovery with AI recommendations
  - Flight search and selection
  - Hotel search and booking
  - Day-by-day itinerary generation
  - Transport options between locations
  
- **Conversational Chat**: Natural language interface for describing travel preferences
  
- **User Accounts**: Registration, login, profile management
  
- **Trip Management**: Save, resume, and manage planned trips

## Design System

The UI follows a "cinematic exploration" aesthetic with:

- **Glass-morphism cards** with subtle blur and borders
- **Dark theme** with midnight blue backgrounds
- **Gold and teal accents** for highlights
- **Playfair Display** for headlines, **Inter** for body text
- **Smooth animations** and transitions

## Development

### Prerequisites

- Node.js 18+
- npm or bun

### Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The development server runs at http://localhost:5173

### Environment Variables

Create a `.env.local` file (optional):

```bash
# Backend API URL (defaults to http://localhost:8000)
VITE_API_BASE_URL=http://localhost:8000
```

### Building

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

### Linting

```bash
npm run lint
```

## Project Structure

```
src/
├── components/
│   ├── travel/           # Trip planning components
│   │   ├── agents/       # Agent-specific UI (Destination, Flight, Hotel, etc.)
│   │   ├── ChatSidebar.tsx
│   │   ├── TravelPlannerForm.tsx
│   │   └── ...
│   ├── ui/               # shadcn/ui components
│   └── Header.tsx
├── contexts/
│   ├── AuthContext.tsx   # Authentication state
│   └── TravelFormContext.tsx  # Trip planning form state
├── pages/
│   ├── Index.tsx         # Main planning page
│   ├── Login.tsx
│   ├── Register.tsx
│   ├── Profile.tsx
│   ├── MyTrips.tsx
│   └── ResumePlanning.tsx
├── services/
│   ├── api.ts            # Backend API calls
│   └── authService.ts    # Authentication API
└── lib/
    └── utils.ts          # Utility functions
```

## Docker

The frontend is containerized with nginx for production:

```bash
# Build the image
docker build -t odyssai-frontend .

# Run the container
docker run -p 8080:80 odyssai-frontend
```

Or use docker-compose from the project root:

```bash
docker-compose up frontend
```

The production build is served at http://localhost:8080
