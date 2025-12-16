# Slide deck generation prompt — OdyssAI (Agentic Travel Planner + MCP)

Use this document as the **master prompt** for generating a polished 16:9 slide deck.

## Output requirements
- **Format**: 16:9 slidedeck (Google Slides / PowerPoint style).
- **Length**: ~10–14 minutes talk + demo.
- **Tone**: Confident, engineering-focused, product-minded.
- **Do not insert tool logos**: instead, place **labeled logo placeholders** (empty rounded rectangles) and I’ll add logos later.
- **Include two graphs** (vector style, not screenshots):
  - Graph A: High-level agent ↔ MCP server interaction (simple overview)
  - Graph B: Detailed bipartite mapping (Agents ↔ MCP servers ↔ tools)

---

## Visual design system (match the website)
Match the website’s “cinematic exploration” style exactly.

### Typography
- **Headlines (H1/H2)**: "Playfair Display" (serif), high contrast, slightly wide tracking.
- **Body**: "Inter" (sans), 300–500 weights.
- **Numbers / metrics**: Inter 600.

### Color palette (use these tokens)
Use the same palette as the frontend theme:
- **Midnight (background base)**: HSL(210, 61%, 11%)
- **Midnight-light (surface)**: HSL(210, 45%, 18%)
- **Fog (primary text)**: HSL(60, 14%, 96%)
- **Fog-muted (secondary text)**: HSL(60, 10%, 70%)
- **Gold (primary accent)**: HSL(34, 50%, 66%)
- **Gold-light**: HSL(34, 45%, 75%)
- **Teal (secondary accent)**: HSL(186, 59%, 30%)
- **Teal-light**: HSL(186, 50%, 40%)
- **Sand (warm neutral card)**: HSL(38, 32%, 85%)
- **Borders**: HSL(210, 30%, 25%)

### Background + layout
- Every slide uses a **vertical background gradient**:
  - Top: Midnight
  - Bottom: a slightly darker midnight (like HSL(210, 50%, 8%))
- Add **ambient glow blobs** (very subtle):
  - Top-left: gold at ~5–8% opacity, heavy blur
  - Bottom-right: teal at ~8–12% opacity, heavy blur
- Optional subtle grid overlay at **2% opacity**.

### Components (repeatable UI motifs)
- **Glass card (default “glass-sand”)**:
  - Background: midnight-light with 80–90% opacity
  - Blur: 16–20px
  - Border: 1px, fog at 10–20% opacity
  - Corner radius: 16–20px
  - Shadow: soft, deep (black at ~35–45% alpha)
- **Accent chips**:
  - Teal-tinted glass for tags (like “AI-Powered Planning”).
- **Primary button style**:
  - Gold → gold-light horizontal gradient
  - Text color: midnight
  - Slight glow on hover (in static slides: add mild outer glow).
- Keep **lots of breathing room** (modern spacing). Use a 12-column grid.

### Iconography
- Use simple line icons (plane, map pin, calendar, car) in **gold** or **teal**.

### Transitions
- Minimal: fade/slide up. No flashy transitions.

---

## Story flow (must follow this order)
1. Problem we solve
2. Quick overview graph: agents + MCP servers + sandbox
3. Demo
4. Deep dive: MCP server tools + which agent uses which (graph)
5. APIs used
6. Tools used to develop (with logo placeholders)
7. Pain points + mitigations
8. Q&A

---

## Slide-by-slide plan (include speaker notes)

### Slide 1 — Title
**Title**: OdyssAI — Agentic Travel Planning with MCP
**Subtitle**: Multi-agent workflow • Sandboxed MCP tools • Real travel APIs
**Visual**: Large title on left, on right a glass card with 3 bullets.
- Bullet 1: “Destinations → Flights → Hotels → Itinerary → Transport”
- Bullet 2: “Tools via MCP servers (Docker sandbox)”
- Bullet 3: “FastAPI + modern React UI”
**Footer**: Presenter names + date.

**Speaker notes**:
- One sentence: what OdyssAI does (end-to-end trip planning with agents + tools).

---

### Slide 2 — The problem
**Title**: Travel planning is fragmented and expensive in time
**Layout**: 3-column glass card row.
- Card 1 (gold accent): “Too many tabs” (flights, hotels, weather, POIs)
- Card 2 (teal accent): “Context gets lost” (preferences don’t transfer)
- Card 3 (sand accent): “No end-to-end workflow” (search → decide → book)
**Add**: a small metric-style line: “Our goal: a single workflow from intent → plan.”

**Speaker notes**:
- The user starts with fuzzy intent; turning that into a complete plan is the hard part.

---

### Slide 3 — What we built (solution overview)
**Title**: A multi-agent travel planner that turns preferences into a trip plan
**Left**: A vertical “workflow” timeline (Destination → Flight → Hotel → Itinerary → Transport).
**Right**: One glass card titled “Key idea” with bullets:
- Specialized agents per domain
- Tools exposed via MCP servers (consistent schemas)
- Sandbox execution for safety + reproducibility

**Speaker notes**:
- Emphasize separation of concerns: reasoning in agents; data retrieval in MCP tools.

---

### Slide 4 — System architecture (Graph A)
**Title**: Architecture at a glance
**Subtitle**: Agents orchestrate → MCP tools execute in sandboxed servers

**Main visual (Graph A)**: A clean node-link diagram:
- **Frontend (React)** → **FastAPI backend**
- **FastAPI backend** → **LLM Orchestrator**
- Orchestrator → Agent nodes:
  - Destination Agent
  - Flight Agent
  - Hotel Agent
  - Itinerary Agent
  - Transport Agent
- Agent nodes connect to MCP server nodes (in a “Sandboxed Docker” container group):
  - mcp-flights
  - mcp-hotels
  - mcp-cars
  - mcp-geo-destinations
- Show “Docker sandbox / GuardiAgent” as a translucent container boundary around MCP servers.
- Itinerary Agent has **no MCP connection** (LLM-only) — show dashed line “LLM reasoning only”.

**Design specs for Graph A**:
- Nodes: rounded glass cards.
- Agent nodes: teal-tinted header strip.
- MCP nodes: gold-tinted header strip.
- Lines:
  - Control flow lines: fog/white at 40% opacity
  - Tool invocation lines: gold gradient stroke
  - Optional dashed lines for “optional/conditional”.

**Speaker notes**:
- “MCP servers are separate processes in containers; agents talk to them via stdio JSON-RPC.”

---

### Slide 5 — Demo setup (what you’ll show)
**Title**: Demo
**Layout**: 2 columns.
- Left: checklist inside glass card.
- Right: “Expected outcome” card.

**Demo checklist (left card)**:
- Open OdyssAI UI
- Fill a trip request (dates, vibe, budget, experiences)
- Run the workflow
- Show:
  - Destination selection
  - Flight options
  - Hotel options
  - Itinerary generation
  - Transport options

**Expected outcome (right card)**:
- A coherent trip plan created from one set of preferences
- Visible step-by-step progress (like the UI workflow bar)

**Speaker notes**:
- Keep it fast; the deep dive comes right after.

---

### Slide 6 — Demo time (full-bleed)
**Title (small corner)**: Live demo
**Visual**: Full-bleed demo placeholder area (you will present live).
- Use a subtle frame: thin fog border 10% opacity, rounded corners.
- Add 3 small callouts positioned bottom-left:
  - “Chat sidebar for preference capture”
  - “Agent workflow progress”
  - “Real API-backed results (where available)”

**Speaker notes**:
- Suggest a strong demo narrative: “from vague intent to a full plan in minutes.”

---

### Slide 7 — MCP deep dive (why MCP)
**Title**: Why MCP servers?
**Layout**: 3 stacked glass cards with icons.
- Card 1: “Consistent tool interfaces” (schemas, predictable outputs)
- Card 2: “Sandboxed execution” (Docker + restricted network/env)
- Card 3: “Replaceable backends” (swap APIs without rewriting agents)

**Speaker notes**:
- MCP is the contract layer between reasoning and real-world actions.

---

### Slide 8 — Tooling map (Graph B: agents ↔ MCP servers ↔ tools)
**Title**: Which agent uses which tools

**Main visual (Graph B)**: A bipartite/tri-partite diagram.
- Column 1: Agents
  - Destination Agent
  - Flight Agent
  - Hotel Agent
  - Transport Agent
  - Itinerary Agent
- Column 2: MCP servers
  - mcp-flights
  - mcp-hotels
  - mcp-cars
  - mcp-geo-destinations
- Column 3: Tools (grouped under each server)

**Connections (must be accurate)**
- Destination Agent → mcp-flights → `autocomplete_airport_or_city`
- Destination Agent → mcp-geo-destinations →
  - `get_country_info`
  - `get_best_travel_season`
  - `get_weather_forecast`
  - `get_points_of_interest`
- Flight Agent → mcp-flights →
  - `search_flights`
  - `price_flight_offer`
  - `book_flight`
  - `get_airline_routes`
  - (optionally) `autocomplete_airport_or_city`
- Hotel Agent → mcp-hotels →
  - `search_hotels_in_city`
  - `search_hotels_by_coordinates`
  - `get_hotel_offer_details`
- Transport Agent → mcp-cars →
  - `search_cars_at_airport`
  - `get_car_offer_details`
- Itinerary Agent → (no MCP server) (LLM-only)

**Design specs for Graph B**
- Use grouped containers for each MCP server; tools listed as smaller pill nodes.
- Color coding:
  - Agents: teal
  - MCP servers: gold
  - Tools: sand
  - “No MCP”: fog-muted dashed box
- Keep the diagram readable: max 12–14 connections visible; route lines cleanly.

**Speaker notes**:
- Call out how tool schemas keep agents stable even when APIs change.

---

### Slide 9 — MCP servers (tool list cards)
**Title**: MCP servers & tools
**Layout**: 2x2 grid of glass cards (one per server). Each card contains:
- Server name
- Short purpose
- Tool list (bullets)
- “Used by” chips (agent names)

**Card content**
1) **mcp-flights** (Amadeus)
- Tools: `autocomplete_airport_or_city`, `search_flights`, `price_flight_offer`, `book_flight`, `get_airline_routes`
- Used by: Destination Agent, Flight Agent

2) **mcp-hotels** (Amadeus)
- Tools: `search_hotels_in_city`, `search_hotels_by_coordinates`, `get_hotel_offer_details`
- Used by: Hotel Agent

3) **mcp-cars** (Amadeus)
- Tools: `search_cars_at_airport`, `get_car_offer_details`
- Used by: Transport Agent

4) **mcp-geo-destinations** (RestCountries + OpenWeatherMap + Amadeus POIs)
- Tools: `get_country_info`, `get_best_travel_season`, `get_weather_forecast`, `get_points_of_interest`
- Used by: Destination Agent

**Speaker notes**:
- Mention: servers run via JSON-RPC over stdio inside Docker sandbox.

---

### Slide 10 — APIs we used
**Title**: External APIs
**Layout**: 5 horizontal cards (or 2 rows), each with a logo placeholder + bullets.

For each API card:
- Left: **Logo placeholder** (empty rounded rectangle labeled)
- Right: 2–3 bullets: “What we use it for”

**Cards**
- **Amadeus**
  - Flights (offers search + pricing + booking)
  - Hotels (offers)
  - Cars (offers)
  - POIs (points of interest)
- **OpenWeatherMap**
  - Seasonality / best travel months
  - Date-range temperature range (forecast-like day summaries)
- **RestCountries**
  - Currency, languages, timezone, country metadata
- **Unsplash**
  - Destination imagery in the UI
- **OpenAI**
  - Agent reasoning + structured outputs

**Speaker notes**:
- Emphasize that “tool layer” makes swapping APIs feasible.

---

### Slide 11 — Tools we used to build OdyssAI (logos later)
**Title**: Developer tooling & stack
**Layout**: Grid of logo placeholders (you will fill logos), each with a label underneath.

**Include placeholders for**
- Cursor (IDE)
- Docker
- Docker Compose
- FastAPI
- Uvicorn
- Python
- React
- Vite
- TypeScript
- Tailwind CSS
- shadcn/ui + Radix UI
- PostgreSQL
- SQLAlchemy
- Pydantic
- OpenAI Agents SDK (`openai-agents`)
- MCP (Model Context Protocol)

**Optional small footer text**: “Plus: ESLint, React Query, jsPDF, bcrypt, Alembic”

**Speaker notes**:
- Keep it high-level: these tools enabled speed + reliability.

---

### Slide 12 — Pain points (and how we solved them)
**Title**: Pain points & mitigations

**Pain point #1 (main focus)**: Amadeus API reliability
- Show as a prominent glass card with a warning icon.
- Text:
  - “Amadeus endpoints can be unreliable (timeouts / intermittent errors / rate limits).”
  - “We do have a production key, but reliability is still not sufficient for a real product.”

**Mitigation (what we did)**
- Second card (gold/teal accent): “Caching inside MCP servers”
  - Local airport DB for instant IATA lookups
  - TTL caches for flight searches (e.g., 15 minutes), routes (e.g., 24h)
  - Cache-first behavior reduces calls + smooths transient failures

**What we’d do in production**
- Third card: “Better data provider access”
  - Enterprise-grade APIs / SLAs
  - Redundancy (multi-provider fallback)

**Speaker notes**:
- Be honest: caching helps; real product needs better upstream reliability.

---

### Slide 13 — Q&A
**Title**: Q&A
**Visual**: Minimal. Big title centered. Subtext: “Happy to dive into agents, MCP, caching, or architecture.”

---

## Appendix (optional slides if time)

### Appendix A — Security model (GuardiAgent sandbox)
- Show:
  - Docker sandbox
  - Restricted network domains
  - Restricted env var access
  - No write permissions by default

### Appendix B — Observability
- Mention logs:
  - Tool entry/exit logs
  - API request/response logs
  - Per-agent execution logs

---

## Graph assets notes (for the slide generator)
- Both graphs should be **vector diagrams**, styled like the site:
  - Rounded glass nodes, gold/teal highlights
  - Thin lines, clean arrows
  - Avoid clutter; prioritize readability
- Use the same corner radius language as the UI (16–20px).
- Put diagrams on a glass-sand panel if they need separation from the background.

