"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useSession } from "./session";
import { Icon, Notice } from "./ui";
import {
  AuditPage,
  BomPage,
  DashboardPage,
  DiscoveryPage,
  EvidencePage,
  ExecutionsPage,
  FrameworkPage,
  GuardrailsPage,
  IntegrationsPage,
  OrganisationPage,
  ReportsPage,
  ResourcePage,
  RuntimePage,
  SettingsPage,
} from "./pages";

const groups = [
  {
    title: "Workspace",
    items: [
      { id: "dashboard", title: "Overview", icon: "grid" },
      { id: "inventory", title: "AI systems", icon: "box" },
      { id: "discovery", title: "Discovery scans", icon: "scan" },
      { id: "bom", title: "AI-BOM / SBOM", icon: "file" },
    ],
  },
  {
    title: "Governance",
    items: [
      { id: "eu-ai-act", title: "EU AI Act", icon: "layers", layer: "02" },
      { id: "iso42001", title: "ISO / IEC 42001", icon: "layers", layer: "03" },
      { id: "nist-ai-rmf", title: "NIST AI RMF", icon: "layers", layer: "04" },
      { id: "risks", title: "Risk register", icon: "risk" },
      { id: "findings", title: "Findings", icon: "scan" },
      { id: "actions", title: "Corrective actions", icon: "check" },
    ],
  },
  {
    title: "Evidence & security",
    items: [
      { id: "evidence", title: "Evidence library", icon: "file" },
      { id: "oscal", title: "OSCAL & attestations", icon: "lock" },
      { id: "runtime", title: "Runtime monitoring", icon: "pulse" },
      { id: "guardrails", title: "LLM guardrails", icon: "shield" },
    ],
  },
  {
    title: "Operations",
    items: [
      { id: "integrations", title: "Integration catalogue", icon: "plug" },
      {
        id: "integration-config",
        title: "Integration settings",
        icon: "settings",
      },
      { id: "executions", title: "Execution history", icon: "clock" },
      { id: "reports", title: "Reports & exports", icon: "file" },
      { id: "audit", title: "Audit trail", icon: "clock" },
      { id: "organisation", title: "Organisation & access", icon: "users" },
      { id: "settings", title: "Settings", icon: "settings" },
    ],
  },
];
function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <div className={`brand ${compact ? "compact" : ""}`}>
      <span className="brand-mark">
        <Icon name="shield" size={25} />
      </span>
      <div>
        <strong>
          UNIFIED<span>AI GOVERNANCE & SECURITY</span>
        </strong>
      </div>
    </div>
  );
}
function Login() {
  const { login } = useSession();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return (
    <main className="login-page">
      <section className="login-story">
        <Brand />
        <div className="login-story-content">
          <p className="eyebrow">Clarity. Control. Accountability.</p>
          <h1>
            Confidence in every
            <br />
            AI decision.
          </h1>
          <p>
            One workspace for the systems you build,
            <br />
            the risks you manage and the evidence
            <br />
            that connects them.
          </p>
          <div className="governance-visual" aria-hidden="true">
            <div className="visual-orbit orbit-1" />
            <div className="visual-orbit orbit-2" />
            <div className="visual-center">
              <Icon name="shield" size={48} />
            </div>
            {["Discover", "Assess", "Protect", "Evidence"].map((t, i) => (
              <span className={`visual-node node-${i}`} key={t}>
                {t}
              </span>
            ))}
          </div>
        </div>
        <div className="login-story-foot">
          <span>Seven governance layers</span>
          <span>One accountable platform</span>
        </div>
      </section>
      <section className="login-form-area">
        <div className="login-form-wrap">
          <span className="outline-tag">Your secure workspace</span>
          <h2>Welcome back</h2>
          <p>Sign in to your governance workspace.</p>
          <form
            onSubmit={async (event) => {
              event.preventDefault();
              setBusy(true);
              setError("");
              try {
                await login(email, password);
                setPassword("");
              } catch (e) {
                setError(e instanceof Error ? e.message : "Sign-in failed");
              } finally {
                setBusy(false);
              }
            }}
          >
            <label className="field">
              <span>Email address</span>
              <input
                type="email"
                autoComplete="username"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@organisation.com"
              />
            </label>
            <label className="field">
              <span>Password</span>
              <input
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
              />
            </label>
            {error && <Notice error>{error}</Notice>}
            <button
              className="button primary login-submit"
              type="submit"
              disabled={busy}
            >
              {busy ? "Signing in…" : "Sign in to workspace"}
              <Icon name="arrow" size={18} />
            </button>
          </form>
          <div className="login-help">
            <Icon name="lock" size={17} />
            <p>
              Accounts are provisioned by your administrator. Contact them if
              you need access or a password reset.
            </p>
          </div>
        </div>
        <footer>
          Unified AI Governance & Security
          <span>Independent governance engine</span>
        </footer>
      </section>
    </main>
  );
}
export function GovernanceApp() {
  const { data, tenant, setTenant, logout } = useSession();
  const pathname = usePathname();
  const route = pathname.split("/").filter(Boolean)[0] || "dashboard";
  const [menu, setMenu] = useState(false);
  const [logoutError, setLogoutError] = useState("");
  if (!data) return <Login />;
  const current = groups.flatMap((g) => g.items).find((i) => i.id === route);
  const membership = data.memberships.find((m) => m.tenant_id === tenant);
  let page: React.ReactNode;
  switch (route) {
    case "dashboard":
    case "login":
      page = <DashboardPage />;
      break;
    case "inventory":
    case "risks":
    case "findings":
    case "actions":
      page = <ResourcePage key={route} kind={route} />;
      break;
    case "discovery":
      page = <DiscoveryPage />;
      break;
    case "bom":
      page = <BomPage />;
      break;
    case "eu-ai-act":
    case "iso42001":
    case "nist-ai-rmf":
      page = <FrameworkPage key={route} kind={route} />;
      break;
    case "evidence":
    case "oscal":
      page = <EvidencePage key={route} oscal={route === "oscal"} />;
      break;
    case "integrations":
    case "integration-config":
      page = (
        <IntegrationsPage configuration={route === "integration-config"} />
      );
      break;
    case "executions":
      page = <ExecutionsPage />;
      break;
    case "guardrails":
      page = <GuardrailsPage />;
      break;
    case "runtime":
      page = <RuntimePage />;
      break;
    case "audit":
      page = <AuditPage />;
      break;
    case "reports":
      page = <ReportsPage />;
      break;
    case "organisation":
      page = <OrganisationPage />;
      break;
    case "settings":
      page = <SettingsPage />;
      break;
    default:
      page = (
        <section className="panel padded">
          <h1>Page not found</h1>
          <p>The requested workspace page does not exist.</p>
          <Link className="button primary" href="/dashboard">
            Return to overview
          </Link>
        </section>
      );
  }
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      {menu && (
        <button
          className="sidebar-overlay"
          aria-label="Close navigation"
          onClick={() => setMenu(false)}
        />
      )}
      <aside className={`sidebar ${menu ? "is-open" : ""}`}>
        <Link
          href="/dashboard"
          className="brand-link"
          aria-label="Unified governance overview"
        >
          <Brand compact />
        </Link>
        <div className="workspace-label">
          <span className="workspace-dot" />
          GOVERNANCE WORKSPACE
        </div>
        <nav aria-label="Main navigation">
          {groups.map((group) => (
            <div className="nav-group" key={group.title}>
              <h2>{group.title}</h2>
              {group.items.map((item) => (
                <Link
                  key={item.id}
                  href={`/${item.id}`}
                  className={`nav-item ${route === item.id ? "active" : ""}`}
                  aria-label={item.title}
                  aria-current={route === item.id ? "page" : undefined}
                  onClick={() => setMenu(false)}
                >
                  <Icon name={item.icon} size={18} />
                  <span>{item.title}</span>
                  {"layer" in item && <small>{item.layer}</small>}
                </Link>
              ))}
            </div>
          ))}
        </nav>
        <div className="sidebar-footer">
          <div className="avatar">
            {(data.user.name || data.user.email).slice(0, 1).toUpperCase()}
          </div>
          <div>
            <strong>{data.user.name || data.user.email}</strong>
            <small>{membership?.role?.replace(/_/g, " ") || "Member"}</small>
          </div>
          <button
            className="icon-button"
            aria-label="Sign out"
            title="Sign out"
            onClick={() => {
              void logout().catch((e) => setLogoutError(String(e)));
            }}
          >
            <Icon name="arrow" size={18} />
          </button>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="topbar-left">
            <button
              className="icon-button mobile-menu"
              aria-label="Open navigation"
              onClick={() => setMenu(true)}
            >
              <Icon name="menu" />
            </button>
            <span className="breadcrumb">
              Workspace <span>/</span>{" "}
              <strong>{current?.title || "Overview"}</strong>
            </span>
          </div>
          <div className="topbar-right">
            <span className="tenant-label">
              <Icon name="users" size={16} />
            </span>
            <select
              aria-label="Select workspace"
              className="tenant-select"
              value={tenant}
              onChange={(e) => setTenant(e.target.value)}
            >
              {data.memberships.map((m) => (
                <option key={m.tenant_id} value={m.tenant_id}>
                  {m.tenant_name}
                </option>
              ))}
            </select>
            <span className="tenant-boundary">Tenant isolated</span>
          </div>
        </header>
        <main id="main-content" className="main-content" key={tenant}>
          {logoutError && <Notice error>{logoutError}</Notice>}
          {page}
          <footer className="page-footer">
            <span>Unified AI Governance & Security</span>
            <span>Traceable decisions. Accountable systems.</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
