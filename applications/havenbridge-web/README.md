
# HavenBridge Web — Local Frontend Prototype

## Purpose

HavenBridge Web is the first frontend prototype for the HavenBridge service
platform. It demonstrates a staff-oriented service-inquiry workspace using
fictional records.

This phase develops and validates the user interface independently of the
backend. It does not connect to the live FastAPI application, read from
PostgreSQL, or change Kubernetes and Traefik configuration.

**Current status: local prototype; not deployed or authenticated.**

## Frontend Phase 1 — Development Foundation

The frontend was created under:

`applications/havenbridge-web/`

The development workstation is `syrus`.

The project uses React, TypeScript, and Vite. Node.js is managed using nvm.

Validated development-tool versions:

- Node.js: `v24.21.0`
- npm: `11.19.0`
- Vite: `8.3.0`

The Vite React + TypeScript scaffold was created with:

```bash
npm create vite@latest havenbridge-web -- --template react-ts
```

Dependencies were installed with `npm install`. The generated project
successfully passed its initial production build.

## Frontend Phase 2 — Synthetic Inquiry Workspace

The prototype provides four main views:

| View | Purpose |
|---|---|
| Overview | Show total inquiries, status counts, and recent records |
| Inquiry list | Browse, search, filter, and page through fictional records |
| Inquiry details | Read an inquiry and change its displayed status |
| New inquiry | Validate a form and add a fictional inquiry to the current session |

The supported statuses match the existing backend contract:

`new`, `reviewing`, `referred`, and `closed`.

### Main Files

| File | Purpose |
|---|---|
| `src/demoData.ts` | Defines the inquiry types, statuses, service categories, and eight initial fictional records |
| `src/App.tsx` | Implements navigation, screens, filters, forms, and temporary React state |
| `src/App.css` | Styles the workspace and its responsive layout |
| `src/index.css` | Provides application-wide styles |
| `src/main.tsx` | Mounts the React application using the Vite scaffold |

### Data and Privacy Boundaries

The prototype initializes its records from `DEMO_INQUIRIES` in
`src/demoData.ts`.

Creating an inquiry or changing a status updates React state in the running
browser session only. A page refresh restores the original demo records.

The interface does not:

- send requests to the HavenBridge API;
- read from or write to PostgreSQL;
- create a real inquiry-status audit record;
- authenticate staff; or
- provide a secure production inquiry-management service.

Use fictional names and `example.org` email addresses for testing. Do not
enter real personal or healthcare information.

## Run Locally

**Host: `syrus`**

From the repository root:

```bash
cd applications/havenbridge-web
npm install
npm run dev -- --host 127.0.0.1
```

Open the local URL printed by Vite, normally:

`http://127.0.0.1:5173/`

Binding to `127.0.0.1` keeps the development server listening on the local
workstation rather than intentionally exposing it on the LAN.

Stop the server with `Ctrl+C`.

### Validate the Build and Linter

**Host: `syrus`**

```bash
cd /home/alabi/projects/havenbridge-ha-service-platform/applications/havenbridge-web

npm run build
npm run lint
```

Observed results:

- Production build: **PASS**
- Oxlint: **0 warnings, 0 errors**
- `node_modules` and `dist` are ignored by Git.

`npm run build` compiles the TypeScript application and produces the frontend
build output in `dist/`. `npm run lint` checks the source code for issues
covered by the configured linter.

## Interactive Validation Evidence

The following behavior was observed during Frontend Phase 2:

| Check | Observed result |
|---|---|
| Inquiry list renders | Eight initial fictional records displayed |
| Create a demo inquiry | `HB-0009` appeared; list showed nine records |
| Change an inquiry status | Grace Sample displayed `Reviewing` |
| Refresh the browser | List returned to eight records |
| Refresh removes temporary inquiry | `HB-0009` disappeared |
| Refresh restores status | Grace Sample returned to `New` |

**Result: PASS for the observed create, status-change, and refresh-reset
scenarios.**

Search, filtering, pagination, and invalid-form scenarios are implemented
but require separate recorded interaction checks before being marked PASS
in this validation history.

## Frontend Phase 3 — Interaction and Usability Validation

### Objective

Validate the local HavenBridge inquiry workspace through browser interactions
before connecting it to the live FastAPI backend.

All tests used the local Vite development server on `syrus`:

`http://127.0.0.1:5173/`

The prototype continued to use fictional, in-memory records. No PostgreSQL,
Kubernetes, Traefik, or backend changes were made during this phase.

### Inquiry List Validation

| Test | Observed result | Status |
|---|---|---|
| Search for `grace` | Only Grace Sample appeared | PASS |
| Filter by Respite Care | Grace Sample and Amara Sample appeared | PASS |
| Filter by New | Four matching records appeared after a demo inquiry was created | PASS |
| Pagination, page 1 | Six of eight initial inquiries appeared | PASS |
| Pagination, page 2 | Remaining two inquiries appeared | PASS |
| Pagination controls | Previous and Next were disabled at the appropriate ends | PASS |

Search and filtering operate on records already loaded into the local
prototype. These tests do not establish database-wide search or filtering.

### Inquiry Creation and Temporary State

Creating a demo inquiry displayed confirmation and added `HB-0009` to the
workspace. The total inquiry count increased from eight to nine, and the New
count increased from three to four.

An earlier status-change test displayed Grace Sample as Reviewing. Refreshing
the browser restored the original eight records, removed `HB-0009`, and
returned Grace Sample to New.

**Result: PASS — demo creation and status changes affect browser memory only.**

The prototype does not send these changes to FastAPI or PostgreSQL and does
not create a database status-history record.

### Form Validation

| Test | Observed result | Status |
|---|---|---|
| Required field left empty | Browser displayed a required-field message and blocked submission | PASS |
| Email entered as `not-an-email` | Browser reported a missing `@` and blocked submission | PASS |
| Seven-character message | Browser required at least 10 characters and blocked submission | PASS |
| One-character requester name | Not separately tested | PENDING |

These checks validate the browser form behavior exercised during testing.
They do not replace server-side validation when a live API connection is
introduced.

### Narrow-Screen Layout

Chrome DevTools Device Mode was used to inspect the frontend at a responsive
viewport width of **343 px**.

The overview cards stacked vertically. The inquiry-list controls adapted to
the narrow layout. On the New inquiry screen, all four form fields and both
action buttons were visible within the viewport width, without visible
horizontal overflow.

**Result: PASS for the inspected 343 px layout.**

This was a browser viewport inspection, not a test on a physical mobile device.

### Validation Summary

The observed search, category filtering, status filtering, pagination,
demo creation, refresh reset, required-field validation, email-format
validation, minimum-message-length validation, and narrow-screen layout
checks passed.

A one-character requester-name test and broader accessibility testing remain
outstanding. The frontend remains a local, unauthenticated prototype using
fictional data; it is not ready to expose real inquiry information.

**Frontend Phase 3 observed interaction validation: PASS, with the
outstanding checks noted above.**


## Next Steps

1. Complete and record the remaining frontend interaction checks.
2. Review the first-release screen design and accessibility.
3. Design and validate staff authentication and API authorization before
   connecting a deployed management interface to inquiry data.
4. Connect the frontend to the existing FastAPI contract in a later phase.
5. Review the Traefik routing plan before deploying the frontend.

The existing FastAPI backend, PostgreSQL database, and Kubernetes routing
remain unchanged during this prototype phase.
