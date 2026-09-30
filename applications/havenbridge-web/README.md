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

The table below describes the current frontend structure, including the
mock-service separation added in Phase 4 and the shared service contract added
in Phase 6.

| File | Purpose |
|---|---|
| `src/demoData.ts` | Defines inquiry types, statuses, service categories, and eight initial fictional records |
| `src/services/inquiryService.ts` | Defines the shared `InquiryService` contract and `CreateInquiryInput` type |
| `src/services/mockInquiryService.ts` | Implements the shared service contract using temporary fictional records in browser memory |
| `src/App.tsx` | Implements navigation, screens, filters, forms, loading/error states, and React state; uses the mock service through the shared service boundary |
| `src/App.css` | Styles the workspace and its responsive layout |
| `src/index.css` | Provides application-wide styles |
| `src/main.tsx` | Mounts the React application using the Vite scaffold |

### Data and Privacy Boundaries

Phase 2 originally loaded `DEMO_INQUIRIES` directly into React state. Since
Phase 4, `src/services/mockInquiryService.ts` copies those same initial
records into module-level browser memory; `App.tsx` loads them through the
service and holds a copy in React state for display.

Creating an inquiry or changing a status updates the mock service and the
React display in the running browser session only. A full page refresh
restores the original demo records.

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

Observed results through Phase 4:

- Production build: **PASS** (`tsc -b && vite build`)
- Oxlint: **0 warnings, 0 errors**
- `node_modules` and `dist` are ignored by Git.

`npm run build` compiles the TypeScript application and produces the frontend
build output in `dist/`. `npm run lint` checks the source code for issues
covered by the configured linter. These checks do not replace browser
interaction tests.

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

Search, filtering, pagination, and invalid-form scenarios were subsequently
tested and recorded in Phase 3 below.

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
| One-character requester name | Not separately tested in Phase 3; verified in Phase 5 below | DEFERRED |

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

At the end of Phase 3, the one-character requester-name test and broader
accessibility testing remained outstanding; the name case was subsequently
verified in Phase 5. The frontend remains a local, unauthenticated prototype
using fictional data; it is not ready to expose real inquiry information.

**Frontend Phase 3 observed interaction validation: PASS, with the
outstanding checks noted above.**

## Frontend Phase 4 — Mock Service and Future API Readiness

### Objective and Scope

Separate fictional inquiry operations from the screen code so a future
API client can be introduced without rewriting all four views. This phase
**does not connect to FastAPI** or deploy the frontend.

The existing backend, PostgreSQL database, Kubernetes resources, and Traefik
routing were not changed.

### Implementation and Rationale

**New file:** `applications/havenbridge-web/src/services/mockInquiryService.ts`

The service starts with copies of the eight fictional records defined in
`src/demoData.ts`. It provides these asynchronous operations:

| Operation | Purpose |
|---|---|
| `listMockInquiries()` | Return copies of all fictional inquiries |
| `getMockInquiry(id)` | Retrieve a fictional inquiry by its numeric ID; this operation is available but the screen does not currently call it |
| `createMockInquiry(input)` | Validate demo input and add a fictional inquiry |
| `updateMockInquiryStatus(id, status)` | Change the status of a fictional inquiry |

The service keeps records in JavaScript module memory and returns copies to
callers. Its approximately 200 ms delay simulates an asynchronous operation
for future loading-state tests; it is **not** network latency or an HTTP
request. Refreshing the page initializes the records again from the original
eight fictional entries.

**Updated file:** `applications/havenbridge-web/src/App.tsx`

The React interface now calls the mock service to load records, create an
inquiry, and change an inquiry's status. React state still controls what is
displayed. The file also contains loading and load-error screens, a saving
state, and feedback for creation or status-update errors. The frontend does
not call `fetch()` or communicate with a backend in this phase.

This separation prepares the UI for a later *design and security review* of
real API integration; it does not by itself provide authentication,
authorization, persistence, or production readiness.

### Commands and Validation Evidence

**Host: `syrus` — build and lint**

```bash
cd /home/alabi/projects/havenbridge-ha-service-platform/applications/havenbridge-web
npm run build
npm run lint
```

Observed after replacing `App.tsx` and adding the mock service:

| Check | Observed result | Status |
|---|---|---|
| TypeScript and Vite build | Production build completed successfully | PASS |
| Oxlint | 0 warnings and 0 errors | PASS |
| Initial overview | Eight fictional inquiries loaded | PASS |
| Create fictional inquiry | `HB-0009` appeared; total became 9 and New became 4 | PASS |
| Change `HB-0005` status | `HB-0005` showed Referred; New changed 4 → 3 and Referred changed 2 → 3 while total stayed 9 | PASS |
| Refresh browser | Total returned to 8; `HB-0009` disappeared; `HB-0005` returned to New | PASS |
| Loading and load-error screens | Not independently exercised in Phase 4; subsequently observed in Phase 5 | DEFERRED TO PHASE 5 |
| Service failure handling for create/status updates | Present in code, not independently simulated | NOT YET VERIFIED |

Browser screenshots were reviewed for creation, status change, and the
refresh reset. No automated unit or integration tests were run in this phase.

**Result: PASS for the observed build, lint, creation, status-update, and
refresh-reset checks.** Loading/error behavior was subsequently exercised in
Phase 5.

### Remaining Boundaries

The mock service is local demonstration code. Its validation and simulated
asynchronous behavior are not substitutes for server-side validation,
authentication, authorization, audit logging, secure storage, or live API
integration. Continue using fictional names and `example.org` addresses.

## Frontend Phase 5 — Loading, Error, and Accessibility Validation

### Objective and Scope

Exercise the frontend's browser-based input checks, keyboard navigation, and
loading/load-error displays without connecting to FastAPI or PostgreSQL.
The service, backend, Kubernetes resources, and Traefik routing were not
changed. All test records were fictional.

### Browser Interaction Checks

| Check | Evidence and observed result | Status |
|---|---|---|
| One-character requester name | A name of `A` triggered the browser's minimum-two-character message and prevented submission | PASS |
| Keyboard navigation | User confirmed Tab could reach navigation, all four form fields, Cancel, and Create demo inquiry, with visible keyboard focus; a focused inquiry row was also visible in a screenshot | PASS for the reported keyboard path |
| Loading display | A controlled mock-service delay showed “Loading fictional inquiries…” and identified the operation as a local demonstration | PASS for display appearing |
| Load-error display | A controlled mock-service failure showed “Unable to load the demo” and “Intentional mock loading error for Phase 5 validation.” | PASS for display appearing |

The screenshots establish that the loading and error messages rendered. They
do **not** independently establish the precise loading duration or a successful
eight-record transition after the delay. Keyboard activation with Enter, a
screen-reader review, automated accessibility testing, and full WCAG
conformance were not verified.

### Controlled Loading and Failure Test

**Host: `syrus` — temporary local test only**

A temporary test version of
`applications/havenbridge-web/src/services/mockInquiryService.ts` accepted
`hbMockTest` query-string switches solely to make these states observable.
The test file was **not committed**. The locally committed mock service has no
Phase 5 query-string test switches.

The temporary service was installed only after backing up the original to
`/tmp/havenbridge-mockInquiryService-before-phase5.ts`. The temporary build
(`npm run build`) passed, and `npm run lint` reported zero warnings and zero
errors. Vite must be running for a browser to access its local URL; a prior
`ERR_CONNECTION_REFUSED` screenshot occurred when the development server was
not running and was **not** an application load-error test.

The browser test URLs were:

```text
http://127.0.0.1:5173/?hbMockTest=loading
http://127.0.0.1:5173/?hbMockTest=error
```

The loading URL displayed the loading message. The error URL displayed the
intentional mock failure message. The error URL is deliberately configured to
fail again on refresh while the temporary test file is installed; remove the
test switch to return to normal behavior.

**Host: `syrus` — restore the original service and validate**

```bash
cd /home/alabi/projects/havenbridge-ha-service-platform/applications/havenbridge-web

# Restore the original service; do not commit the temporary test implementation.
cp /tmp/havenbridge-mockInquiryService-before-phase5.ts \
  src/services/mockInquiryService.ts

npm run build
npm run lint
git status --short
```

The restored production build passed, Oxlint reported **0 warnings and 0
errors**, and `git status --short` produced no output. This confirms the
original mock service was restored with no uncommitted changes at the end of
the browser tests.

### Result and Remaining Coverage

**PASS for the observed one-character name rejection, reported keyboard
navigation path, controlled loading display, controlled load-error display,
and restoration of the original service.** These are targeted checks, not a
complete accessibility audit or end-to-end test suite. The handling of failures
during inquiry creation and status updates has not been separately simulated.

## Frontend Phase 6 — API Integration Design and Shared Service Boundary

### Objective and Scope

Review the existing FastAPI inquiry contract and Kubernetes routing before
connecting the frontend to live data. Introduce a shared frontend service
contract so React can later switch from fictional browser data to a real API
implementation without rewriting the screens.

This phase does **not** connect the frontend to FastAPI, expose real inquiry
records, change PostgreSQL, deploy the frontend, or modify Traefik.

### Existing FastAPI Contract

The backend inspection confirmed these routes:

| Operation | Endpoint | Behavior |
|---|---|---|
| Create inquiry | `POST /api/v1/inquiries` | Validates and stores a new inquiry |
| List inquiries | `GET /api/v1/inquiries` | Uses `limit` and `offset`; newest first |
| Get one inquiry | `GET /api/v1/inquiries/{inquiry_id}` | Returns one inquiry or `404` |
| Change status | `PATCH /api/v1/inquiries/{inquiry_id}/status` | Updates status and writes status history |

The list endpoint currently defaults to 50 records, supports a maximum of 100,
and uses offset-based pagination.

The backend response fields are:

```text
id
requester_name
requester_email
service_category
message
status
created_at
updated_at
```

The supported statuses are:

```text
new
reviewing
referred
closed
```

These fields and status values are compatible with the frontend `Inquiry`
TypeScript interface.

### Create-Request Compatibility

The frontend `CreateInquiryInput` contains:

```text
requester_name
requester_email
service_category
message
```

These are the same four fields accepted by the FastAPI create schema.

The backend remains the authoritative validator. It currently enforces:

- requester name: 2–120 characters;
- email: Pydantic `EmailStr` validation;
- service category: 2–80 characters;
- message: 10–2000 characters; and
- rejection of unexpected request fields.

The mock frontend performs similar checks for demonstration purposes, but its
service-category rule is stricter because it only accepts values from
`DEMO_CATEGORIES`. The backend currently accepts any category string that
meets its length constraint. This difference is documented for a later
integration decision rather than changed in this phase.

### Authentication Finding

The inspected inquiry routes use `Depends(get_db)` to obtain a SQLAlchemy
database session.

The application inspection did not identify an implemented OAuth, JWT,
bearer-token, API-key, or equivalent staff-authentication mechanism protecting
the inquiry routes.

Therefore, the staff-facing frontend must **not** expose live inquiry listing,
detail, or status-update operations until authentication and authorization are
designed and validated.

No authentication mechanism was added during Phase 6.

### Current Traefik Routing Finding

The existing HTTPS route uses:

```text
hostname: havenbridge.lab
PathPrefix: /
backend: havenbridge-api Service :80
```

This means the current hostname sends all matching paths to FastAPI.

The proposed future routing model is:

```text
https://havenbridge.lab/
        |
        +-- /           -> havenbridge-web
        |
        +-- /api/...    -> havenbridge-api
```

This would allow the deployed frontend to use relative requests such as:

```text
/api/v1/inquiries
```

The proposed routing is a design only. No HTTPRoute, Gateway, Traefik,
Service, or NetworkPolicy resource was changed in Phase 6.

### Shared Frontend Service Contract

**New file:**

`applications/havenbridge-web/src/services/inquiryService.ts`

Purpose: define a common contract for inquiry data operations.

The contract contains:

```text
listInquiries()
getInquiry(id)
createInquiry(input)
updateInquiryStatus(id, status)
```

It also defines the shared `CreateInquiryInput` type.

The architecture is now:

```text
App.tsx
   |
   v
InquiryService contract
   |
   +-- mockInquiryService   <- current
   |
   +-- apiInquiryService    <- future
```

### Mock Service Update

**Updated file:**

`applications/havenbridge-web/src/services/mockInquiryService.ts`

The mock service now implements the shared `InquiryService` contract and
exports a `mockInquiryService` object.

Its behavior remains unchanged:

- eight fictional records are loaded initially;
- created inquiries remain temporary;
- status changes remain temporary;
- browser refresh restores the original records;
- no FastAPI request is made;
- no PostgreSQL write occurs; and
- no real status-history record is created.

### React Integration Update

**Updated file:**

`applications/havenbridge-web/src/App.tsx`

React now calls the shared service object instead of importing individual
mock-specific operation functions.

Before:

```text
listMockInquiries()
createMockInquiry()
updateMockInquiryStatus()
```

After:

```text
mockInquiryService.listInquiries()
mockInquiryService.createInquiry()
mockInquiryService.updateInquiryStatus()
```

The application is still explicitly using fictional data.

### Build, Lint, and Browser Regression Validation

**Host: `syrus`**

```bash
cd /home/alabi/projects/havenbridge-ha-service-platform/applications/havenbridge-web

npm run build
npm run lint
```

Observed results:

| Check | Observed result | Status |
|---|---|---|
| TypeScript and Vite build | Production build completed successfully | PASS |
| Oxlint | 0 warnings and 0 errors | PASS |
| Initial dataset | Original eight fictional inquiries loaded | PASS |
| Create inquiry | `HB-0009` appeared; total increased to 9 | PASS |
| Change status | `HB-0009` changed to Referred | PASS |
| Refresh reset | Total returned to 8 and `HB-0009` disappeared | PASS |

The regression check confirms that introducing the shared service boundary did
not change the previously validated mock-data behavior.

### Phase 6 Result

**PASS for API-contract review, frontend/backend compatibility review,
authentication and routing findings, shared-service implementation, build and
lint validation, and browser regression testing.**

The frontend remains a local, unauthenticated prototype using fictional data.
A real `apiInquiryService` should not be activated for staff inquiry data until
authentication, authorization, and routing changes are implemented and
validated.


## Next Steps

1. Design and validate staff authentication and API authorization before
   exposing real inquiry listing, detail, or status-update operations.
2. Decide the final Traefik path-routing design for `havenbridge.lab`.
3. Design the future `apiInquiryService`, including HTTP error handling and
   server-side pagination, while keeping the mock implementation active.
4. Perform broader accessibility testing, including screen-reader behavior
   and focus management.
5. Simulate failures during inquiry creation and status updates.
6. Resolve the service-category validation difference between the frontend
   fixed category list and the backend's current length-only rule.
7. Near project completion, compile the alphabetical HavenBridge glossary and
   host-labeled command reference into a searchable PDF without secrets.

The frontend remains a local, unauthenticated prototype using fictional data.
The existing FastAPI backend, PostgreSQL database, and Kubernetes routing were
not changed during Frontend Phase 6.
