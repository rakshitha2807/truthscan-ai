# TruthScan AI — Frontend

A responsive React + Vite frontend for an AI-powered fact-checking product. It is intentionally backend-agnostic so the team can build the API independently.

## Run locally

Requirements: Node.js 18+

```bash
npm install
npm run dev
```

Open the local URL printed by Vite (usually http://localhost:5173).

## Production build

```bash
npm run build
npm run preview
```

## What's included

- Responsive workspace shell with sidebar navigation
- Overview dashboard with stats, recent investigations, and a trend panel
- Fact checker with Claim / URL modes and image attachments
- Analysis History with localStorage persistence, verdict filters, search, details, and confirmed clearing
- Evidence Explorer with demo source cards, stance filters, and search
- Clearly marked demo analysis with sample verdict, score, explanation, and evidence
- Loading, error, and empty states for the analysis flow
- A backend-neutral API service boundary and centralized API base URL configuration
- Modular CSS and React components in `src/main.jsx`

## Demo mode

Analysis currently uses `src/services/mockAnalysis.js`; sample verdicts rotate only to demonstrate the UI. History is saved locally through `src/services/mockHistory.js`. The Evidence Explorer uses `src/services/mockEvidence.js`. Its dates, stance labels, credibility indicators, and summaries are illustrative only; they are not genuine fact-checking results or source assessments. Source links open publisher websites, but do not validate the associated demo metadata. No API requests are made in demo mode.

## Backend integration (later)

Copy `.env.example` to `.env.local` when configuring the frontend. Set `VITE_API_BASE_URL` only after the backend base URL is known; it has no default, so the generic request helper will not send requests until configured. `VITE_API_TIMEOUT_MS` controls the request timeout and defaults to 15000 ms; if set, it must be a positive whole number.

React components use `src/services/api.js` for analysis, evidence, and history data. The current provider in that facade is `src/services/mockApi.js`, which delegates to the individual mock services. `requestApi` is a generic transport helper with timeout, network, HTTP-status, empty-body, and invalid-JSON handling; it does not select endpoints or run as part of demo operations. Once the backend team provides its contract, add backend adapters in the service layer and switch providers deliberately. Do not map or display backend data until the agreed request and response shapes are implemented.

The current URL and image inputs are passed to the mock service only. They are not uploaded or analyzed by a backend.

### Backend details still needed

- API base URL and endpoint paths/methods for analysis, evidence, and history
- Authentication requirements and expected request headers
- Request fields and response schemas, including error response format
- Image upload method and encoding (for example multipart form data or a URL)
- Whether history is server-persisted, user-scoped, or remains local to the browser
