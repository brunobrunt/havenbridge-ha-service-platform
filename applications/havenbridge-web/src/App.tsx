import { useMemo, useState, type FormEvent } from "react";
import {
  DEMO_CATEGORIES,
  DEMO_INQUIRIES,
  INQUIRY_STATUSES,
  STATUS_LABELS,
  type Inquiry,
  type InquiryStatus,
} from "./demoData";
import "./App.css";

type Page = "overview" | "inquiries" | "new";

const PAGE_SIZE = 6;

function formatDate(value: string): string {
  return new Date(value).toLocaleDateString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

function inquiryNumber(id: number): string {
  return `HB-${String(id).padStart(4, "0")}`;
}

function App() {
  const [inquiries, setInquiries] = useState<Inquiry[]>(DEMO_INQUIRIES);
  const [page, setPage] = useState<Page>("overview");
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [statusDraft, setStatusDraft] = useState<InquiryStatus>("new");
  const [statusFilter, setStatusFilter] = useState<InquiryStatus | "all">("all");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [pageNumber, setPageNumber] = useState(1);
  const [notice, setNotice] = useState("");

  const selectedInquiry = inquiries.find((item) => item.id === selectedId);

  const filteredInquiries = useMemo(() => {
    return inquiries
      .filter((item) => statusFilter === "all" || item.status === statusFilter)
      .filter(
        (item) =>
          categoryFilter === "all" ||
          item.service_category === categoryFilter,
      )
      .filter((item) => {
        const term = search.trim().toLowerCase();

        return (
          term === "" ||
          inquiryNumber(item.id).toLowerCase().includes(term) ||
          item.requester_name.toLowerCase().includes(term) ||
          item.service_category.toLowerCase().includes(term)
        );
      })
      .sort(
        (a, b) =>
          new Date(b.created_at).getTime() -
          new Date(a.created_at).getTime(),
      );
  }, [inquiries, statusFilter, categoryFilter, search]);

  const totalPages = Math.max(
    1,
    Math.ceil(filteredInquiries.length / PAGE_SIZE),
  );

  const visibleInquiries = filteredInquiries.slice(
    (pageNumber - 1) * PAGE_SIZE,
    pageNumber * PAGE_SIZE,
  );

  function showOverview() {
    setPage("overview");
    setSelectedId(null);
    setNotice("");
  }

  function showInquiries(filter: InquiryStatus | "all" = "all") {
    setPage("inquiries");
    setSelectedId(null);
    setStatusFilter(filter);
    setCategoryFilter("all");
    setSearch("");
    setPageNumber(1);
    setNotice("");
  }

  function openInquiry(inquiry: Inquiry) {
    setSelectedId(inquiry.id);
    setStatusDraft(inquiry.status);
    setPage("inquiries");
    setNotice("");
  }

  function updateStatus() {
    if (!selectedInquiry || statusDraft === selectedInquiry.status) return;

    const now = new Date().toISOString();

    setInquiries((current) =>
      current.map((item) =>
        item.id === selectedInquiry.id
          ? { ...item, status: statusDraft, updated_at: now }
          : item,
      ),
    );

    setNotice("Demo status updated in this browser session only.");
  }

  function createInquiry(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const data = new FormData(event.currentTarget);
    const requester_name = String(data.get("requester_name") ?? "").trim();
    const requester_email = String(data.get("requester_email") ?? "").trim();
    const service_category = String(data.get("service_category") ?? "");
    const message = String(data.get("message") ?? "").trim();

    if (
      requester_name.length < 2 ||
      requester_name.length > 120 ||
      !requester_email.includes("@") ||
      !DEMO_CATEGORIES.includes(service_category) ||
      message.length < 10 ||
      message.length > 2000
    ) {
      setNotice("Please check the form fields and try again.");
      return;
    }

    const id = Math.max(0, ...inquiries.map((item) => item.id)) + 1;
    const now = new Date().toISOString();

    const inquiry: Inquiry = {
      id,
      requester_name,
      requester_email,
      service_category,
      message,
      status: "new",
      created_at: now,
      updated_at: now,
    };

    setInquiries((current) => [inquiry, ...current]);
    setSelectedId(id);
    setStatusDraft("new");
    setPage("inquiries");
    setNotice("Fictional inquiry created in this browser session only.");
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">H</div>
          <div>
            <strong>HavenBridge</strong>
            <span>Service workspace</span>
          </div>
        </div>

        <nav aria-label="Main navigation">
          <button
            className={page === "overview" ? "nav-active" : ""}
            onClick={showOverview}
          >
            Overview
          </button>
          <button
            className={page === "inquiries" ? "nav-active" : ""}
            onClick={() => showInquiries()}
          >
            Inquiries
          </button>
          <button
            className={page === "new" ? "nav-active" : ""}
            onClick={() => {
              setSelectedId(null);
              setPage("new");
              setNotice("");
            }}
          >
            New inquiry
          </button>
        </nav>

        <div className="sidebar-note">
          <strong>Prototype mode</strong>
          <p>No live API or database connection.</p>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <span className="eyebrow">HAVENBRIDGE / DEMO</span>
            <h1>
              {page === "overview"
                ? "Workspace overview"
                : page === "new"
                  ? "New inquiry"
                  : selectedInquiry
                    ? "Inquiry details"
                    : "Service inquiries"}
            </h1>
            <p className="muted">
              Fictional records for frontend development and validation.
            </p>
          </div>
          <span className="demo-badge">SYNTHETIC DATA</span>
        </header>

        <div className="privacy-banner">
          <strong>Private local prototype.</strong> Do not enter real personal
          information. Changes are temporary and disappear when you refresh
          the page.
        </div>

        {notice && (
          <div className="notice" role="status">
            {notice}
          </div>
        )}

        {page === "overview" && (
          <>
            <section className="stats-grid" aria-label="Inquiry counts">
              <button className="stat-card" onClick={() => showInquiries()}>
                <span>Total inquiries</span>
                <strong>{inquiries.length}</strong>
                <small>View all inquiries →</small>
              </button>

              {INQUIRY_STATUSES.map((status) => (
                <button
                  className="stat-card"
                  key={status}
                  onClick={() => showInquiries(status)}
                >
                  <span>{STATUS_LABELS[status]}</span>
                  <strong>
                    {inquiries.filter((item) => item.status === status).length}
                  </strong>
                  <small>View matching inquiries →</small>
                </button>
              ))}
            </section>

            <section className="panel">
              <div className="section-heading">
                <div>
                  <h2>Recent inquiries</h2>
                  <p className="muted">Select a fictional record to explore it.</p>
                </div>
                <button className="secondary-button" onClick={() => showInquiries()}>
                  View all
                </button>
              </div>

              <div className="inquiry-list">
                {[...inquiries]
                  .sort(
                    (a, b) =>
                      new Date(b.created_at).getTime() -
                      new Date(a.created_at).getTime(),
                  )
                  .slice(0, 5)
                  .map((item) => (
                    <button
                      className="inquiry-row"
                      key={item.id}
                      onClick={() => openInquiry(item)}
                    >
                      <span>
                        <strong>{inquiryNumber(item.id)}</strong>
                        <small>{item.requester_name}</small>
                      </span>
                      <span>{item.service_category}</span>
                      <span className={`status status-${item.status}`}>
                        {STATUS_LABELS[item.status]}
                      </span>
                    </button>
                  ))}
              </div>
            </section>
          </>
        )}

        {page === "inquiries" && !selectedInquiry && (
          <section className="panel">
            <div className="section-heading">
              <div>
                <h2>Inquiry list</h2>
                <p className="muted">
                  Showing {filteredInquiries.length} fictional records.
                </p>
              </div>
              <button className="primary-button" onClick={() => setPage("new")}>
                + New inquiry
              </button>
            </div>

            <div className="filters">
              <label>
                Search
                <input
                  value={search}
                  placeholder="ID, requester or category"
                  onChange={(event) => {
                    setSearch(event.target.value);
                    setPageNumber(1);
                  }}
                />
              </label>

              <label>
                Status
                <select
                  value={statusFilter}
                  onChange={(event) => {
                    setStatusFilter(
                      event.target.value as InquiryStatus | "all",
                    );
                    setPageNumber(1);
                  }}
                >
                  <option value="all">All statuses</option>
                  {INQUIRY_STATUSES.map((status) => (
                    <option key={status} value={status}>
                      {STATUS_LABELS[status]}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Category
                <select
                  value={categoryFilter}
                  onChange={(event) => {
                    setCategoryFilter(event.target.value);
                    setPageNumber(1);
                  }}
                >
                  <option value="all">All categories</option>
                  {DEMO_CATEGORIES.map((category) => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {visibleInquiries.length === 0 ? (
              <div className="empty-state">
                No inquiries match these filters.
              </div>
            ) : (
              <div className="inquiry-list">
                {visibleInquiries.map((item) => (
                  <button
                    className="inquiry-row"
                    key={item.id}
                    onClick={() => openInquiry(item)}
                  >
                    <span>
                      <strong>{inquiryNumber(item.id)}</strong>
                      <small>{item.requester_name}</small>
                    </span>
                    <span>{item.service_category}</span>
                    <span className={`status status-${item.status}`}>
                      {STATUS_LABELS[item.status]}
                    </span>
                  </button>
                ))}
              </div>
            )}

            <div className="pagination">
              <button
                className="secondary-button"
                disabled={pageNumber === 1}
                onClick={() => setPageNumber((current) => current - 1)}
              >
                Previous
              </button>
              <span>
                Page {pageNumber} of {totalPages}
              </span>
              <button
                className="secondary-button"
                disabled={pageNumber >= totalPages}
                onClick={() => setPageNumber((current) => current + 1)}
              >
                Next
              </button>
            </div>
          </section>
        )}

        {page === "inquiries" && selectedInquiry && (
          <section className="panel detail-panel">
            <button className="text-button" onClick={() => showInquiries(statusFilter)}>
              ← Back to inquiries
            </button>

            <div className="section-heading">
              <div>
                <span className="eyebrow">
                  {inquiryNumber(selectedInquiry.id)}
                </span>
                <h2>{selectedInquiry.service_category}</h2>
              </div>
              <span className={`status status-${selectedInquiry.status}`}>
                {STATUS_LABELS[selectedInquiry.status]}
              </span>
            </div>

            <div className="detail-grid">
              <div>
                <span className="field-label">Requester</span>
                <strong>{selectedInquiry.requester_name}</strong>
              </div>
              <div>
                <span className="field-label">Demo email</span>
                <strong>{selectedInquiry.requester_email}</strong>
              </div>
              <div>
                <span className="field-label">Created</span>
                <strong>{formatDate(selectedInquiry.created_at)}</strong>
              </div>
              <div>
                <span className="field-label">Updated</span>
                <strong>{formatDate(selectedInquiry.updated_at)}</strong>
              </div>
            </div>

            <div className="message-box">
              <h3>Inquiry message</h3>
              <p>{selectedInquiry.message}</p>
            </div>

            <div className="status-editor">
              <label>
                Update status
                <select
                  value={statusDraft}
                  onChange={(event) =>
                    setStatusDraft(event.target.value as InquiryStatus)
                  }
                >
                  {INQUIRY_STATUSES.map((status) => (
                    <option key={status} value={status}>
                      {STATUS_LABELS[status]}
                    </option>
                  ))}
                </select>
              </label>
              <button
                className="primary-button"
                disabled={statusDraft === selectedInquiry.status}
                onClick={updateStatus}
              >
                Save demo status
              </button>
            </div>

            <p className="muted">
              This prototype does not write to PostgreSQL or create a real
              status-history record.
            </p>
          </section>
        )}

        {page === "new" && (
          <section className="panel form-panel">
            <h2>Create a fictional inquiry</h2>
            <p className="muted">
              Use invented names and example.org email addresses only.
            </p>

            <form onSubmit={createInquiry} className="inquiry-form">
              <label>
                Requester name
                <input
                  name="requester_name"
                  minLength={2}
                  maxLength={120}
                  placeholder="Taylor Demo"
                  required
                />
              </label>

              <label>
                Demo email
                <input
                  name="requester_email"
                  type="email"
                  placeholder="taylor.demo@example.org"
                  required
                />
              </label>

              <label>
                Service category
                <select name="service_category" defaultValue="" required>
                  <option value="" disabled>
                    Choose a category
                  </option>
                  {DEMO_CATEGORIES.map((category) => (
                    <option key={category} value={category}>
                      {category}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Inquiry message
                <textarea
                  name="message"
                  minLength={10}
                  maxLength={2000}
                  rows={5}
                  placeholder="Describe a fictional service inquiry..."
                  required
                />
              </label>

              <div className="form-actions">
                <button
                  type="button"
                  className="secondary-button"
                  onClick={showOverview}
                >
                  Cancel
                </button>
                <button type="submit" className="primary-button">
                  Create demo inquiry
                </button>
              </div>
            </form>
          </section>
        )}
      </main>
    </div>
  );
}

export default App;
