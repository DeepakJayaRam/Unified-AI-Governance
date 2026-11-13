"use client";
import Link from "next/link";
import { useState } from "react";
import { useRemote, RemoteMore } from "./remote";
import { GovernanceRecords } from "./governance-records";
import {
  PolicyHistory,
  ReviewQueue,
  AccountSecurity,
  MembershipActions,
  AssessmentActions,
} from "./workflow-controls";
import {
  API_URL,
  downloadJson,
  filterRecords,
  label,
  listOf,
  RecordData,
} from "@/lib/api";
import { useSession } from "./session";
import {
  Badge,
  Detail,
  Empty,
  Field,
  Form,
  Icon,
  Loader,
  Modal,
  Notice,
  Table,
} from "./ui";

export function PageHeader({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow?: string;
  title: string;
  description: string;
  children?: React.ReactNode;
}) {
  return (
    <header className="page-heading">
      <div>
        {eyebrow && <p className="eyebrow">{eyebrow}</p>}
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      <div className="heading-actions">{children}</div>
    </header>
  );
}
function Search({
  value,
  onChange,
  placeholder = "Search records…",
}: {
  value: string;
  onChange: (s: string) => void;
  placeholder?: string;
}) {
  return (
    <div className="search-box">
      <Icon name="search" size={17} />
      <input
        aria-label={placeholder}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
const statuses = (values: string[]) =>
  values.map((value) => ({ value, label: value.replace(/_/g, " ") }));
const riskFields: Field[] = [
  { name: "title", label: "Title", required: true },
  { name: "description", label: "Description", type: "textarea" },
  {
    name: "severity",
    label: "Severity",
    type: "select",
    options: statuses(["low", "medium", "high", "critical"]),
    defaultValue: "medium",
    required: true,
  },
  {
    name: "status",
    label: "Status",
    type: "select",
    options: statuses(["open", "in_progress", "resolved", "accepted"]),
    defaultValue: "open",
    required: true,
  },
  { name: "owner", label: "Owner" },
  { name: "due_date", label: "Due date", type: "date" },
];
export const resourceDefinitions: Record<
  string,
  {
    title: string;
    description: string;
    path: string;
    singular: string;
    fields: Field[];
    columns: { key: string; title: string; badge?: boolean }[];
    system?: boolean;
    editable?: boolean;
  }
> = {
  inventory: {
    title: "AI system inventory",
    description:
      "Know the systems you operate, who owns them and the risk they carry.",
    path: "/systems",
    singular: "AI system",
    fields: [
      { name: "name", label: "System name", required: true },
      { name: "description", label: "Description", type: "textarea" },
      { name: "owner", label: "System owner" },
      {
        name: "risk_level",
        label: "Risk level",
        type: "select",
        options: statuses([
          "unassessed",
          "minimal",
          "limited",
          "high",
          "unacceptable",
        ]),
        defaultValue: "unassessed",
        required: true,
      },
    ],
    columns: [
      { key: "name", title: "System" },
      { key: "owner", title: "Owner" },
      { key: "risk_level", title: "Risk level", badge: true },
      { key: "created_at", title: "Registered" },
    ],
    editable: true,
  },
  risks: {
    title: "Risk register",
    description:
      "Assess risks, assign responsibility and follow treatment through to completion.",
    path: "/risks",
    singular: "risk",
    fields: riskFields,
    columns: [
      { key: "title", title: "Risk" },
      { key: "severity", title: "Severity", badge: true },
      { key: "status", title: "Status", badge: true },
      { key: "owner", title: "Owner" },
      { key: "due_date", title: "Due" },
    ],
    system: true,
    editable: true,
  },
  findings: {
    title: "Findings",
    description:
      "Review scan findings and assessment gaps in one tenant-scoped register.",
    path: "/findings",
    singular: "finding",
    fields: riskFields,
    columns: [
      { key: "title", title: "Finding" },
      { key: "severity", title: "Severity", badge: true },
      { key: "status", title: "Status", badge: true },
      { key: "owner", title: "Owner" },
    ],
    system: true,
    editable: true,
  },
  actions: {
    title: "Corrective actions",
    description: "Turn governance gaps into assigned, time-bound improvements.",
    path: "/actions",
    singular: "corrective action",
    fields: riskFields,
    columns: [
      { key: "title", title: "Action" },
      { key: "status", title: "Status", badge: true },
      { key: "owner", title: "Owner" },
      { key: "due_date", title: "Due" },
    ],
    system: true,
    editable: true,
  },
};
export function ResourcePage({ kind }: { kind: string }) {
  const def = resourceDefinitions[kind];
  const remote = useRemote(def.path);
  const systems = useRemote("/systems");
  const { api } = useSession();
  const [query, setQuery] = useState("");
  const [editing, setEditing] = useState<RecordData | "new" | null>(null);
  const [detail, setDetail] = useState<unknown>(null);
  const fields = def.system
    ? [
        {
          name: "system_id",
          label: "AI system",
          type: "select" as const,
          options: systems.rows.map((s) => ({
            value: s.id,
            label: String(s.name),
          })),
        },
        ...def.fields,
      ]
    : def.fields;
  return (
    <>
      <PageHeader
        eyebrow="Governance operations"
        title={def.title}
        description={def.description}
      >
        <button className="button primary" onClick={() => setEditing("new")}>
          <Icon name="plus" size={17} />
          Add {def.singular}
        </button>
      </PageHeader>
      {remote.error && <Notice error>{remote.error}</Notice>}
      <section className="panel">
        <div className="panel-toolbar">
          <div className="section-label">
            All records <span className="count">{remote.rows.length}</span>
          </div>
          <Search value={query} onChange={setQuery} />
        </div>
        {remote.loading ? (
          <Loader />
        ) : !remote.rows.length ? (
          <Empty
            title={`No ${kind === "inventory" ? "AI systems" : def.title.toLowerCase()} yet`}
          />
        ) : (
          <Table
            rows={filterRecords(remote.rows, query)}
            columns={def.columns}
            actions={(row) => (
              <>
                <button className="text-button" onClick={() => setDetail(row)}>
                  Details
                </button>
                {def.editable && (
                  <button
                    className="text-button"
                    onClick={() => setEditing(row)}
                  >
                    Edit
                  </button>
                )}
              </>
            )}
          />
        )}
        <RemoteMore remote={remote} />
      </section>
      {editing && (
        <Modal
          title={`${editing === "new" ? "Add" : "Edit"} ${def.singular}`}
          close={() => setEditing(null)}
        >
          <Form
            fields={fields}
            initial={editing === "new" ? {} : editing}
            onCancel={() => setEditing(null)}
            onSubmit={async (values) => {
              await api(
                def.path + (editing === "new" ? "" : `/${editing.id}`),
                {
                  method: editing === "new" ? "POST" : "PATCH",
                  headers:
                    editing === "new"
                      ? {}
                      : { "If-Match": String(editing.version) },
                  body: JSON.stringify(values),
                },
              );
              setEditing(null);
              await remote.refresh();
            }}
          />
        </Modal>
      )}
      {detail !== null && (
        <Detail value={detail} close={() => setDetail(null)} />
      )}
    </>
  );
}
export function DashboardPage() {
  const remote = useRemote("/dashboard");
  const executions = useRemote("/executions");
  const risks = useRemote("/risks");
  const stats = (remote.data || {}) as Record<string, unknown>;
  const metric = (...keys: string[]) => {
    for (const key of keys)
      if (typeof stats[key] === "number") return stats[key] as number;
    const counts = stats.counts as Record<string, number> | undefined;
    for (const key of keys)
      if (counts && typeof counts[key] === "number") return counts[key];
    return "—";
  };
  return (
    <>
      <PageHeader
        eyebrow="Your governance workspace"
        title="Governance overview"
        description="A clear view of your AI systems, evidence and security activity."
      >
        <Link className="button secondary" href="/reports">
          <Icon name="download" size={17} />
          Export report
        </Link>
        <Link className="button primary" href="/inventory">
          <Icon name="plus" size={17} />
          Register AI system
        </Link>
      </PageHeader>
      {remote.error && <Notice error>{remote.error}</Notice>}
      <div className="metrics-grid">
        {[
          {
            label: "AI systems",
            value: metric("systems", "ai_systems", "system_count"),
            icon: "box",
            link: "/inventory",
            detail: "Registered in this workspace",
          },
          {
            label: "Open risks",
            value:
              risks.loading || risks.error
                ? "?"
                : risks.rows.filter(
                    (r) =>
                      !["resolved", "accepted", "closed"].includes(
                        String(r.status),
                      ),
                  ).length,
            icon: "risk",
            link: "/risks",
            detail: "Requiring review or treatment",
          },
          {
            label: "Evidence records",
            value: metric("evidence", "evidence_count"),
            icon: "file",
            link: "/evidence",
            detail: "Stored with integrity hashes",
          },
          {
            label: "Executions",
            value: metric("executions", "execution_count"),
            icon: "pulse",
            link: "/executions",
            detail: "Recorded integration runs",
          },
        ].map((m) => (
          <Link className="metric" href={m.link} key={m.label}>
            <div className="metric-top">
              <span>{m.label}</span>
              <Icon name={m.icon} />
            </div>
            <strong>{remote.loading ? "…" : m.value}</strong>
            <p>{m.detail}</p>
          </Link>
        ))}
      </div>
      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel-title">
            <h2>Recent executions</h2>
            <Link href="/executions">
              View all <Icon name="arrow" size={15} />
            </Link>
          </div>
          {executions.loading ? (
            <Loader />
          ) : executions.error ? (
            <Notice error>{executions.error}</Notice>
          ) : !executions.rows.length ? (
            <Empty title="Your execution history starts here">
              Configure a supported integration and submit a discovery scan to
              see its results.
            </Empty>
          ) : (
            <Table
              rows={executions.rows.slice(0, 5)}
              columns={[
                { key: "integration_id", title: "Integration" },
                { key: "status", title: "Status", badge: true },
                { key: "created_at", title: "Submitted" },
              ]}
            />
          )}
        </section>
        <section className="panel pathway">
          <p className="eyebrow">A connected workflow</p>
          <h2>Build your governance record</h2>
          <p>
            Connect operational evidence to the systems and decisions it
            supports.
          </p>
          {[
            {
              n: "01",
              title: "Register a system",
              text: "Establish scope and ownership",
              href: "/inventory",
            },
            {
              n: "02",
              title: "Assess and discover",
              text: "Understand risks and controls",
              href: "/discovery",
            },
            {
              n: "03",
              title: "Collect the evidence",
              text: "Preserve provenance and integrity",
              href: "/evidence",
            },
          ].map((item) => (
            <Link key={item.n} href={item.href} className="pathway-step">
              <span>{item.n}</span>
              <div>
                <strong>{item.title}</strong>
                <small>{item.text}</small>
              </div>
              <Icon name="arrow" size={17} />
            </Link>
          ))}
        </section>
      </div>
      <section className="panel">
        <div className="panel-title">
          <h2>Risks requiring attention</h2>
          <Link href="/risks">
            Open risk register <Icon name="arrow" size={15} />
          </Link>
        </div>
        {risks.error ? (
          <Notice error>{risks.error}</Notice>
        ) : risks.loading ? (
          <Loader />
        ) : risks.rows.filter(
            (r) =>
              !["resolved", "accepted", "closed"].includes(String(r.status)),
          ).length ? (
          <Table
            rows={risks.rows
              .filter(
                (r) =>
                  !["resolved", "accepted", "closed"].includes(
                    String(r.status),
                  ),
              )
              .slice(0, 5)}
            columns={[
              { key: "title", title: "Risk" },
              { key: "severity", title: "Severity", badge: true },
              { key: "status", title: "Status", badge: true },
              { key: "owner", title: "Owner" },
            ]}
          />
        ) : (
          <Empty title="No open risks recorded">
            Your risk register is clear of open records. This is a record count,
            not a compliance determination.
          </Empty>
        )}
      </section>
    </>
  );
}
export function DiscoveryPage() {
  const systems = useRemote("/systems");
  const catalog = useRemote("/integrations");
  const { api } = useSession();
  const [result, setResult] = useState<unknown>(null);
  const discovery = catalog.rows.filter(
    (r) => Number(r.layer) === 1 || /cdxgen|aibom|opencomplai/.test(r.id),
  );
  return (
    <>
      <PageHeader
        eyebrow="Layer 01 · Discovery"
        title="Discover your AI footprint"
        description="Queue supported discovery tools and preserve the complete execution record."
      />
      <div className="two-column">
        <section className="panel padded">
          <h2>New discovery scan</h2>
          {systems.error && <Notice error>{systems.error}</Notice>}
          {catalog.error && <Notice error>{catalog.error}</Notice>}
          <Form
            submitLabel="Queue scan"
            fields={[
              {
                name: "system_id",
                label: "AI system",
                type: "select",
                required: true,
                options: systems.rows.map((s) => ({
                  value: s.id,
                  label: String(s.name),
                })),
              },
              {
                name: "integration_id",
                label: "Discovery integration",
                type: "select",
                required: true,
                options: discovery
                  .filter((s) => s.executable)
                  .map((s) => ({
                    value: s.id,
                    label: `${s.name || s.id} · ${s.status || s.classification}`,
                  })),
              },
              {
                name: "input",
                label: "Execution input (JSON)",
                type: "json",
                defaultValue: {
                  package_json: {
                    name: "my-ai-system",
                    version: "1.0.0",
                    dependencies: {},
                  },
                  package_lock: {
                    name: "my-ai-system",
                    version: "1.0.0",
                    lockfileVersion: 3,
                    requires: true,
                    packages: {
                      "": {
                        name: "my-ai-system",
                        version: "1.0.0",
                        dependencies: {},
                      },
                    },
                  },
                },
                help: "Replace this template with your package.json and npm v3 package-lock JSON. Remove scripts and unsupported fields. This adapter accepts manifest data, never host filesystem paths.",
              },
            ]}
            onSubmit={async (values) => {
              setResult(
                await api("/executions", {
                  method: "POST",
                  body: JSON.stringify(values),
                }),
              );
            }}
          />
          {result !== null && (
            <>
              <Notice>
                Scan submitted. Follow its status in execution history.
              </Notice>
              <pre className="json-view">{JSON.stringify(result, null, 2)}</pre>
              <Link className="button secondary" href="/executions">
                View execution history
                <Icon name="arrow" size={16} />
              </Link>
            </>
          )}
        </section>
        <aside className="panel padded muted-panel">
          <span className="feature-icon">
            <Icon name="scan" size={26} />
          </span>
          <h2>Discovery with provenance</h2>
          <p>
            Jobs run through configured adapters with explicit timeouts and
            controlled inputs. Availability depends on the worker environment.
          </p>
          <div className="info-steps">
            <p>
              <strong>1. Configure</strong>
              <span>Inspect an integration’s requirements and health.</span>
            </p>
            <p>
              <strong>2. Execute</strong>
              <span>Queue a scan for a registered AI system.</span>
            </p>
            <p>
              <strong>3. Review</strong>
              <span>Inspect raw output, normalized results and findings.</span>
            </p>
          </div>
          <Link href="/integrations" className="text-link">
            Browse discovery integrations <Icon name="arrow" size={16} />
          </Link>
        </aside>
      </div>
    </>
  );
}
export function BomPage() {
  const remote = useRemote("/bom");
  const systems = useRemote("/systems");
  const { api } = useSession();
  const [open, setOpen] = useState(false);
  const [detail, setDetail] = useState<unknown>(null);
  const [query, setQuery] = useState("");
  return (
    <>
      <PageHeader
        eyebrow="Layer 01 · Inventory artifacts"
        title="AI-BOM & SBOM library"
        description="Import supported CycloneDX documents and inspect the inventory behind each AI system."
      >
        <button className="button primary" onClick={() => setOpen(true)}>
          <Icon name="plus" size={17} />
          Import BOM
        </button>
      </PageHeader>
      {remote.error && <Notice error>{remote.error}</Notice>}
      <section className="panel">
        <div className="panel-toolbar">
          <span className="section-label">
            Inventory documents{" "}
            <span className="count">{remote.rows.length}</span>
          </span>
          <Search value={query} onChange={setQuery} />
        </div>
        {remote.loading ? (
          <Loader />
        ) : remote.rows.length ? (
          <Table
            rows={filterRecords(remote.rows, query)}
            columns={[
              { key: "id", title: "Document" },
              { key: "system_id", title: "AI system" },
              { key: "component_count", title: "Components" },
              { key: "created_at", title: "Imported" },
            ]}
            actions={(row) => (
              <button className="text-button" onClick={() => setDetail(row)}>
                Inspect
              </button>
            )}
          />
        ) : (
          <Empty title="No inventory documents">
            Import a CycloneDX document or run a configured discovery adapter.
          </Empty>
        )}
        <RemoteMore remote={remote} />
      </section>
      {open && (
        <Modal title="Import inventory document" close={() => setOpen(false)}>
          <Form
            fields={[
              {
                name: "system_id",
                label: "AI system",
                type: "select",
                required: true,
                options: systems.rows.map((s) => ({
                  value: s.id,
                  label: String(s.name),
                })),
              },
              {
                name: "document",
                label: "CycloneDX JSON document",
                type: "json",
                required: true,
                defaultValue: {
                  bomFormat: "CycloneDX",
                  specVersion: "1.6",
                  version: 1,
                  components: [],
                },
              },
            ]}
            submitLabel="Import document"
            onCancel={() => setOpen(false)}
            onSubmit={async (values) => {
              await api("/bom", {
                method: "POST",
                body: JSON.stringify(values),
              });
              setOpen(false);
              await remote.refresh();
            }}
          />
        </Modal>
      )}
      {detail !== null && (
        <Detail
          value={detail}
          title="Inventory document"
          close={() => setDetail(null)}
        />
      )}
    </>
  );
}
const frameworkInfo: Record<
  string,
  { key: string; title: string; eyebrow: string; description: string }
> = {
  "eu-ai-act": {
    key: "eu_ai_act",
    title: "EU AI Act workspace",
    eyebrow: "Layer 02 · Regulatory governance",
    description:
      "Organize risk classification, control assessments and regulatory evidence.",
  },
  iso42001: {
    key: "iso42001",
    title: "ISO/IEC 42001 workspace",
    eyebrow: "Layer 03 · AI management system",
    description:
      "Assess your management practices, track gaps and record applicability decisions.",
  },
  "nist-ai-rmf": {
    key: "nist_ai_rmf",
    title: "NIST AI RMF workspace",
    eyebrow: "Layer 04 · Risk management",
    description:
      "Connect Govern, Map, Measure and Manage activities to evidence and accountable owners.",
  },
};
export function FrameworkPage({ kind }: { kind: string }) {
  const info = frameworkInfo[kind];
  const remote = useRemote("/assessments");
  const systems = useRemote("/systems");
  const evidence = useRemote("/evidence");
  const { api } = useSession();
  const [creating, setCreating] = useState(false);
  const [detail, setDetail] = useState<RecordData | null>(null);
  const [control, setControl] = useState<RecordData | null>(null);
  const [error, setError] = useState("");
  const rows = remote.rows.filter((r) => r.framework === info.key);
  const openAssessment = async (row: RecordData) => {
    try {
      setDetail(await api<RecordData>(`/assessments/${row.id}`));
      setError("");
    } catch (e) {
      setError(String(e));
    }
  };
  return (
    <>
      <PageHeader
        eyebrow={info.eyebrow}
        title={info.title}
        description={info.description}
      >
        <button className="button primary" onClick={() => setCreating(true)}>
          <Icon name="plus" size={17} />
          New assessment
        </button>
      </PageHeader>
      <div className="context-note">
        <Icon name="file" size={18} />
        <p>
          {kind === "eu-ai-act"
            ? "Assessment support is not legal advice or a guarantee of compliance. Review applicable obligations against authoritative legal sources."
            : kind === "iso42001"
              ? "This workspace supports management workflows. It does not reproduce the ISO standard or issue certification."
              : "Assessments organize NIST AI RMF activities. Mappings are implementation guidance and require contextual review."}
        </p>
      </div>
      {(error || remote.error) && (
        <Notice error>{error || remote.error}</Notice>
      )}
      <section className="panel">
        <div className="panel-title">
          <h2>Assessments</h2>
          <span className="count">{rows.length}</span>
        </div>
        {remote.loading ? (
          <Loader />
        ) : rows.length ? (
          <Table
            rows={rows}
            columns={[
              { key: "name", title: "Assessment" },
              { key: "system_id", title: "AI system" },
              { key: "status", title: "Status", badge: true },
              { key: "created_at", title: "Created" },
            ]}
            actions={(row) => (
              <button
                className="text-button"
                onClick={() => void openAssessment(row)}
              >
                Open assessment
              </button>
            )}
          />
        ) : (
          <Empty title="No assessments started">
            Choose an AI system and create an assessment to evaluate controls
            and attach evidence.
          </Empty>
        )}
        <RemoteMore remote={remote} />
      </section>
      <GovernanceRecords framework={info.key} />
      {creating && (
        <Modal title="Create assessment" close={() => setCreating(false)}>
          <Form
            fields={[
              { name: "name", label: "Assessment name", required: true },
              {
                name: "system_id",
                label: "AI system",
                type: "select",
                required: true,
                options: systems.rows.map((s) => ({
                  value: s.id,
                  label: String(s.name),
                })),
              },
            ]}
            onCancel={() => setCreating(false)}
            onSubmit={async (values) => {
              const created = await api<RecordData>("/assessments", {
                method: "POST",
                body: JSON.stringify({ ...values, framework: info.key }),
              });
              setCreating(false);
              await remote.refresh();
              await openAssessment(created);
            }}
          />
        </Modal>
      )}
      {detail && (
        <Modal
          title={String(detail.name || "Assessment")}
          close={() => setDetail(null)}
        >
          <p className="modal-intro">
            Review each control, record supporting evidence and assign follow-up
            work.
          </p>
          <AssessmentActions
            record={detail}
            refresh={async () => {
              const latest = await api<RecordData>(`/assessments/${detail.id}`);
              setDetail((current) =>
                current?.id === latest.id ? latest : current,
              );
              await remote.refresh();
            }}
          />
          <div className="control-list">
            {listOf(detail.controls).map((c) => (
              <div className="control-row" key={c.id}>
                <div>
                  <span className="control-id">{c.id}</span>
                  <h3>{String(c.title || c.name || c.id)}</h3>
                  <p>
                    {String(
                      c.description ||
                        c.notes ||
                        "No assessment notes recorded.",
                    )}
                  </p>
                </div>
                <Badge value={c.status || "not_started"} />
                <button
                  className="button secondary small"
                  onClick={() => setControl(c)}
                >
                  Evaluate
                </button>
              </div>
            ))}
          </div>
          {!listOf(detail.controls).length && (
            <Empty title="No controls returned">
              The selected framework has no loaded controls. Check framework
              configuration.
            </Empty>
          )}
        </Modal>
      )}
      {control && detail && (
        <Modal title={`Evaluate ${control.id}`} close={() => setControl(null)}>
          <Form
            initial={{
              ...control,
              evidence_ids: JSON.stringify(control.evidence_ids || []),
            }}
            fields={[
              {
                name: "status",
                label: "Control status",
                type: "select",
                required: true,
                options: statuses([
                  "not_started",
                  "in_progress",
                  "implemented",
                  "gap",
                  "not_applicable",
                ]),
              },
              {
                name: "notes",
                label: "Assessment and applicability notes",
                type: "textarea",
              },
              { name: "owner", label: "Owner" },
              { name: "due_date", label: "Due date", type: "date" },
              {
                name: "evidence_ids",
                label: "Evidence IDs (JSON array)",
                type: "json",
                help: evidence.rows.length
                  ? evidence.rows.map((e) => `${e.title}: ${e.id}`).join(" · ")
                  : "No evidence records yet. Create evidence in the library, then attach its ID.",
              },
            ]}
            onCancel={() => setControl(null)}
            onSubmit={async (values) => {
              await api(
                `/assessments/${detail.id}/controls/${encodeURIComponent(control.id)}`,
                { method: "PUT", body: JSON.stringify(values) },
              );
              setControl(null);
              await openAssessment(detail);
              await remote.refresh();
            }}
          />
        </Modal>
      )}
    </>
  );
}
export function EvidencePage({ oscal = false }: { oscal?: boolean }) {
  const remote = useRemote("/evidence");
  const systems = useRemote("/systems");
  const { api, data, tenant } = useSession();
  const [creating, setCreating] = useState(false);
  const [detail, setDetail] = useState<unknown>(null);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const action = async (row: RecordData, type: string) => {
    setError("");
    try {
      if (type === "download") {
        const response = await fetch(`${API_URL}/evidence/${row.id}/download`, {
          headers: {
            Authorization: `Bearer ${data?.access_token}`,
            "X-Tenant-ID": tenant,
          },
          credentials: "omit",
          cache: "no-store",
        });
        if (!response.ok)
          throw new Error(`Download failed (${response.status})`);
        const url = URL.createObjectURL(await response.blob());
        const link = document.createElement("a");
        link.href = url;
        link.download = `evidence-${row.id}.txt`;
        link.click();
        URL.revokeObjectURL(url);
      } else {
        setDetail(
          await api(`/evidence/${row.id}/${type}`, {
            method: type === "attest" ? "POST" : "GET",
          }),
        );
        await remote.refresh();
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Evidence action failed");
    }
  };
  return (
    <>
      <PageHeader
        eyebrow="Layer 05 · Evidence & provenance"
        title={oscal ? "OSCAL & attestations" : "Evidence library"}
        description={
          oscal
            ? "Generate attestations, verify evidence integrity and inspect structured compliance artifacts."
            : "Keep the artifacts behind your governance decisions traceable and accessible."
        }
      >
        <button className="button primary" onClick={() => setCreating(true)}>
          <Icon name="plus" size={17} />
          Add evidence
        </button>
      </PageHeader>
      {oscal && (
        <div className="context-note">
          <Icon name="lock" size={18} />
          <p>
            Attestations record provenance and artifact hashes. A statement
            alone is not a digital signature. External signing requires a
            configured signer; inspect the returned verification status.
          </p>
        </div>
      )}
      {(remote.error || error) && (
        <Notice error>{error || remote.error}</Notice>
      )}
      <section className="panel">
        <div className="panel-toolbar">
          <span className="section-label">
            Evidence records <span className="count">{remote.rows.length}</span>
          </span>
          <Search value={query} onChange={setQuery} />
        </div>
        {remote.loading ? (
          <Loader />
        ) : remote.rows.length ? (
          <Table
            rows={filterRecords(remote.rows, query)}
            columns={[
              { key: "title", title: "Evidence" },
              { key: "media_type", title: "Format" },
              { key: "sha256", title: "SHA-256" },
              { key: "created_at", title: "Collected" },
            ]}
            actions={(row) => (
              <>
                <button className="text-button" onClick={() => setDetail(row)}>
                  Details
                </button>
                <button
                  className="text-button"
                  onClick={() => void action(row, "download")}
                >
                  Download
                </button>
                <button
                  className="text-button"
                  onClick={() => void action(row, "verify")}
                >
                  Verify
                </button>
                <button
                  className="text-button"
                  onClick={() => void action(row, "attest")}
                >
                  Attest
                </button>
              </>
            )}
          />
        ) : (
          <Empty title="No evidence collected">
            Add an artifact to record its provenance and integrity hash.
          </Empty>
        )}
        <RemoteMore remote={remote} />
      </section>
      {creating && (
        <Modal title="Add evidence" close={() => setCreating(false)}>
          <Form
            fields={[
              { name: "title", label: "Evidence title", required: true },
              { name: "description", label: "Description", type: "textarea" },
              {
                name: "system_id",
                label: "AI system",
                type: "select",
                options: systems.rows.map((s) => ({
                  value: s.id,
                  label: String(s.name),
                })),
              },
              {
                name: "media_type",
                label: "Media type",
                type: "select",
                defaultValue: "text/plain",
                required: true,
                options: statuses(["text/plain", "application/json"]),
              },
              {
                name: "content",
                label: "Artifact content",
                type: "textarea",
                required: true,
                help: "Paste text or JSON. JSON is validated when application/json is selected. Artifacts remain isolated to this workspace.",
              },
            ]}
            onCancel={() => setCreating(false)}
            onSubmit={async (values) => {
              await api("/evidence", {
                method: "POST",
                body: JSON.stringify(values),
              });
              setCreating(false);
              await remote.refresh();
            }}
          />
        </Modal>
      )}
      {detail !== null && (
        <Detail
          value={detail}
          title="Evidence record"
          close={() => setDetail(null)}
        />
      )}
    </>
  );
}
function IntegrationRunModal({
  integration,
  close,
  completed,
}: {
  integration: RecordData;
  close: () => void;
  completed: (value: unknown) => void;
}) {
  const systems = useRemote("/systems");
  const { api } = useSession();
  return (
    <Modal title={`Run ${integration.name || integration.id}`} close={close}>
      <p className="modal-intro">
        Submit the adapter's documented input. Execution runs in the background
        and preserves status, raw output and provenance.
      </p>
      <Form
        submitLabel="Queue execution"
        fields={[
          {
            name: "system_id",
            label: "AI system",
            type: "select",
            options: systems.rows.map((s) => ({
              value: s.id,
              label: String(s.name),
            })),
          },
          {
            name: "input",
            label: "Execution input (JSON)",
            type: "json",
            defaultValue: {},
            help: "Use the verified adapter input format from the integration record and deployment documentation. Secrets and arbitrary host paths are not accepted.",
          },
        ]}
        onCancel={close}
        onSubmit={async (values) => {
          const result = await api("/executions", {
            method: "POST",
            body: JSON.stringify({ ...values, integration_id: integration.id }),
          });
          close();
          completed(result);
        }}
      />
    </Modal>
  );
}
export function IntegrationsPage({
  configuration = false,
}: {
  configuration?: boolean;
}) {
  const remote = useRemote("/integrations");
  const { api } = useSession();
  const [query, setQuery] = useState("");
  const [layer, setLayer] = useState("");
  const [editing, setEditing] = useState<RecordData | null>(null);
  const [detail, setDetail] = useState<unknown>(null);
  const [error, setError] = useState("");
  const [checking, setChecking] = useState("");
  const [running, setRunning] = useState<RecordData | null>(null);
  const rows = filterRecords(remote.rows, query).filter(
    (r) => !layer || String(r.layer) === layer,
  );
  const restricted = (row: RecordData) =>
    !row.executable ||
    ["REFERENCE_RESOURCE", "BLOCKED_BY_LICENCE", "DEFERRED"].includes(
      String(row.classification),
    );
  return (
    <>
      <PageHeader
        eyebrow="Seven layers · One catalogue"
        title={
          configuration ? "Integration configuration" : "Integration catalogue"
        }
        description="Verified upstream capabilities, deployment requirements and tenant-specific connection status."
      >
        <button
          className="button secondary"
          onClick={() => void remote.refresh()}
        >
          <Icon name="refresh" size={16} />
          Refresh status
        </button>
      </PageHeader>
      {(remote.error || error) && (
        <Notice error>{error || remote.error}</Notice>
      )}
      <div className="catalog-toolbar">
        <Search
          value={query}
          onChange={setQuery}
          placeholder="Search integrations…"
        />
        <select
          aria-label="Filter by layer"
          value={layer}
          onChange={(e) => setLayer(e.target.value)}
        >
          <option value="">All seven layers</option>
          {[1, 2, 3, 4, 5, 6, 7].map((n) => (
            <option value={n} key={n}>
              Layer {n}
            </option>
          ))}
        </select>
        <span className="muted">{rows.length} entries</span>
      </div>
      {remote.loading ? (
        <Loader />
      ) : rows.length ? (
        <div className="integration-grid">
          {rows.map((row) => (
            <article className="integration-card" key={row.id}>
              <div className="integration-card-top">
                <span className="integration-symbol">
                  <Icon
                    name={
                      Number(row.layer) === 7
                        ? "shield"
                        : Number(row.layer) === 5
                          ? "file"
                          : "plug"
                    }
                    size={25}
                  />
                </span>
                <span className="layer-tag">LAYER {String(row.layer)}</span>
              </div>
              <h2>{String(row.name || row.project_name || row.id)}</h2>
              <p className="integration-description">
                {String(
                  row.description ||
                    row.capabilities ||
                    "Review the verified integration record for capabilities and requirements.",
                )}
              </p>
              <div className="integration-meta">
                <Badge
                  value={
                    row.status || row.integration_status || "Not configured"
                  }
                />
                <span>{label(row.classification)}</span>
              </div>
              <div className="integration-card-footer">
                <button className="text-button" onClick={() => setDetail(row)}>
                  View verification <Icon name="arrow" size={14} />
                </button>
                {!restricted(row) && (
                  <div className="inline-fields">
                    <button
                      className="button secondary small"
                      onClick={() => setEditing(row)}
                    >
                      Configure
                    </button>
                    {Boolean(
                      (row.configuration as Record<string, unknown> | null)
                        ?.enabled,
                    ) && (
                      <button
                        className="button primary small"
                        onClick={() => setRunning(row)}
                      >
                        Run
                      </button>
                    )}
                  </div>
                )}
              </div>
              {!restricted(row) && configuration && (
                <button
                  className="text-button health-button"
                  disabled={checking === row.id}
                  onClick={async () => {
                    setChecking(row.id);
                    setError("");
                    try {
                      setDetail(
                        await api(`/integrations/${row.id}/health`, {
                          method: "POST",
                        }),
                      );
                      await remote.refresh();
                    } catch (e) {
                      setError(
                        e instanceof Error ? e.message : "Health check failed",
                      );
                    } finally {
                      setChecking("");
                    }
                  }}
                >
                  {checking === row.id ? "Checking…" : "Check connection"}
                </button>
              )}
            </article>
          ))}
        </div>
      ) : (
        <Empty title="No integrations match">
          Try another search term or layer filter.
        </Empty>
      )}
      {editing && (
        <Modal
          title={`Configure ${editing.name || editing.id}`}
          close={() => setEditing(null)}
        >
          <p className="modal-intro">
            Configuration is scoped to the selected tenant. Credentials and
            signing keys must be supplied through the documented server secret
            mechanism.
          </p>
          <Form
            fields={[
              {
                name: "enabled",
                label: "Enable integration",
                type: "checkbox",
                defaultValue: true,
              },
              {
                name: "config",
                label: "Adapter configuration (JSON)",
                type: "json",
                defaultValue:
                  (editing.configuration as Record<string, unknown> | null)
                    ?.config || {},
                help: "Use only fields supported by the adapter. Read the verification record and deployment documentation before enabling.",
              },
            ]}
            initial={{
              enabled:
                (editing.configuration as Record<string, unknown> | null)
                  ?.enabled ?? true,
              config:
                (editing.configuration as Record<string, unknown> | null)
                  ?.config || {},
            }}
            onCancel={() => setEditing(null)}
            submitLabel="Save configuration"
            onSubmit={async (values) => {
              await api(`/integrations/${editing.id}/config`, {
                method: "PUT",
                body: JSON.stringify(values),
              });
              setEditing(null);
              await remote.refresh();
            }}
          />
        </Modal>
      )}
      {running && (
        <IntegrationRunModal
          integration={running}
          close={() => setRunning(null)}
          completed={setDetail}
        />
      )}{" "}
      {detail !== null && (
        <Detail
          value={detail}
          title="Integration verification & status"
          close={() => setDetail(null)}
        />
      )}
    </>
  );
}
export function ExecutionsPage() {
  const remote = useRemote("/executions", true);
  const { api } = useSession();
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("");
  const [detail, setDetail] = useState<unknown>(null);
  const [error, setError] = useState("");
  const rows = filterRecords(remote.rows, query).filter(
    (r) => !status || r.status === status,
  );
  return (
    <>
      <PageHeader
        eyebrow="Integration operations"
        title="Execution history"
        description="Track queued work, inspect normalized results and preserve raw output and provenance."
      >
        <Link className="button primary" href="/discovery">
          <Icon name="plus" size={16} />
          New scan
        </Link>
      </PageHeader>
      {(remote.error || error) && (
        <Notice error>{error || remote.error}</Notice>
      )}
      <section className="panel">
        <div className="panel-toolbar">
          <div className="section-label">
            Executions <span className="count">{remote.rows.length}</span>
            <span className="live-label">
              <span className="dot" />
              Refreshes every 5s
            </span>
          </div>
          <div className="inline-fields">
            <select
              aria-label="Filter by execution status"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
            >
              <option value="">All statuses</option>
              {["queued", "running", "succeeded", "failed", "cancelled"].map(
                (s) => (
                  <option key={s}>{s}</option>
                ),
              )}
            </select>
            <Search value={query} onChange={setQuery} />
          </div>
        </div>
        {remote.loading ? (
          <Loader />
        ) : remote.rows.length ? (
          <Table
            rows={rows}
            columns={[
              { key: "integration_id", title: "Integration" },
              { key: "status", title: "Status", badge: true },
              { key: "created_at", title: "Submitted" },
              { key: "duration_ms", title: "Duration (ms)" },
            ]}
            actions={(row) => (
              <>
                <button
                  className="text-button"
                  onClick={async () => {
                    try {
                      setDetail(await api(`/executions/${row.id}`));
                    } catch (e) {
                      setError(String(e));
                    }
                  }}
                >
                  View results
                </button>
                {["queued", "running"].includes(String(row.status)) && (
                  <button
                    className="text-button danger-text"
                    onClick={async () => {
                      try {
                        await api(`/executions/${row.id}/cancel`, {
                          method: "POST",
                        });
                        await remote.refresh();
                      } catch (e) {
                        setError(String(e));
                      }
                    }}
                  >
                    Cancel
                  </button>
                )}
                {["failed", "cancelled"].includes(String(row.status)) && (
                  <button
                    className="text-button"
                    onClick={async () => {
                      try {
                        await api(`/executions/${row.id}/retry`, {
                          method: "POST",
                        });
                        await remote.refresh();
                      } catch (e) {
                        setError(String(e));
                      }
                    }}
                  >
                    Retry execution
                  </button>
                )}
              </>
            )}
          />
        ) : (
          <Empty title="No executions recorded">
            Submit a discovery job or run a configured adapter to start an
            execution history.
          </Empty>
        )}
        <RemoteMore remote={remote} />
      </section>
      {detail !== null && (
        <Detail
          value={detail}
          title="Execution results & provenance"
          close={() => setDetail(null)}
        />
      )}
    </>
  );
}
export function GuardrailsPage() {
  const policies = useRemote("/policies");
  const systems = useRemote("/systems");
  const { api } = useSession();
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<RecordData | null>(null);
  const [result, setResult] = useState<Record<string, unknown> | null>(null);
  return (
    <>
      <PageHeader
        eyebrow="Layer 07 · LLM guardrails"
        title="Guardrail policies & testing"
        description="Evaluate configured controls and measure the decision path using your own test input."
      >
        <button className="button primary" onClick={() => setCreating(true)}>
          <Icon name="plus" size={17} />
          Create policy
        </button>
      </PageHeader>
      {policies.error && <Notice error>{policies.error}</Notice>}
      <div className="two-column">
        <section className="panel padded">
          <div className="section-heading">
            <h2>Test a request</h2>
            <span className="outline-tag">Synchronous path</span>
          </div>
          <Form
            submitLabel="Evaluate request"
            fields={[
              {
                name: "policy_id",
                label: "Policy",
                type: "select",
                required: true,
                options: policies.rows.map((p) => ({
                  value: p.id,
                  label: String(p.name),
                })),
              },
              {
                name: "text",
                label: "Test input",
                type: "textarea",
                required: true,
                placeholder: "Enter a test message to evaluate…",
                help: "Use synthetic data when testing. Request content is not stored in the audit log.",
              },
              {
                name: "system_id",
                label: "AI system for OPA classification",
                type: "select",
                options: systems.rows.map((s) => ({
                  value: s.id,
                  label: String(s.name),
                })),
              },
              {
                name: "direction",
                label: "Request direction",
                type: "select",
                defaultValue: "input",
                required: true,
                options: statuses(["input", "output"]),
              },
            ]}
            onSubmit={async (values) =>
              setResult(
                await api<Record<string, unknown>>("/guardrails/evaluate", {
                  method: "POST",
                  body: JSON.stringify(values),
                }),
              )
            }
          />
          {result && (
            <div className="guardrail-result">
              <div className="result-heading">
                <Badge value={result.decision} />
                <span>
                  {typeof result.latency_ms === "number"
                    ? `${result.latency_ms.toFixed(2)} ms`
                    : label(result.latency_ms)}
                </span>
              </div>
              {typeof result.sanitized_text === "string" && (
                <>
                  <h3>Processed output</h3>
                  <div className="processed-text">{result.sanitized_text}</div>
                </>
              )}
              <h3>Check results</h3>
              <pre className="json-view">
                {JSON.stringify(result.checks || result, null, 2)}
              </pre>
            </div>
          )}
        </section>
        <section className="panel">
          <div className="panel-title">
            <h2>Workspace policies</h2>
            <span className="count">{policies.rows.length}</span>
          </div>
          {policies.loading ? (
            <Loader />
          ) : policies.rows.length ? (
            <div className="policy-list">
              {policies.rows.map((p) => (
                <div className="policy-card" key={p.id}>
                  <div>
                    <h3>{String(p.name)}</h3>
                    <Badge value={p.enabled ? "Active" : "Disabled"} />
                  </div>
                  <pre>{JSON.stringify(p.config, null, 2)}</pre>
                  <button className="text-button" onClick={() => setEditing(p)}>
                    Edit policy
                  </button>
                  <PolicyHistory policy={p} refresh={policies.refresh} />
                </div>
              ))}
            </div>
          ) : (
            <Empty title="No policies configured">
              Create a policy with explicit PII handling and error behavior
              before testing requests.
            </Empty>
          )}
          <div className="panel-footnote">
            Latency is measured per request. A single observation does not
            establish p50, p95 or p99 performance or a sub-50ms guarantee.
          </div>
        </section>
      </div>
      {(creating || editing) && (
        <Modal
          title={editing ? "Edit policy" : "Create guardrail policy"}
          close={() => {
            setCreating(false);
            setEditing(null);
          }}
        >
          <Form
            initial={
              editing
                ? {
                    name: editing.name,
                    enabled: editing.enabled,
                    config: editing.config,
                  }
                : {}
            }
            fields={[
              { name: "name", label: "Policy name", required: true },
              {
                name: "enabled",
                label: "Enabled",
                type: "checkbox",
                defaultValue: true,
              },
              {
                name: "config",
                label: "Policy configuration (JSON)",
                type: "json",
                defaultValue: {
                  pii_action: "sanitize",
                  blocked_terms: [],
                  error_action: "block",
                  checks: ["native"],
                },
                help: "checks: native, presidio and/or opa. External controls require administrator-enabled integrations. pii_action: sanitize, block, review or allow. error_action: block or review. Native patterns do not provide comprehensive PII or prompt-injection protection.",
              },
            ]}
            onCancel={() => {
              setCreating(false);
              setEditing(null);
            }}
            onSubmit={async (values) => {
              await api(editing ? `/policies/${editing.id}` : "/policies", {
                method: editing ? "PATCH" : "POST",
                headers: editing ? { "If-Match": String(editing.version) } : {},
                body: JSON.stringify(values),
              });
              setCreating(false);
              setEditing(null);
              await policies.refresh();
            }}
          />
        </Modal>
      )}
    </>
  );
}
export function RuntimePage() {
  const remote = useRemote("/runtime/events", true);
  const [detail, setDetail] = useState<unknown>(null);
  const [query, setQuery] = useState("");
  return (
    <>
      <PageHeader
        eyebrow="Layer 06 · Continuous governance"
        title="Runtime monitoring"
        description="Inspect recorded policy decisions, check outcomes and measured request latency."
      >
        <Link className="button primary" href="/guardrails">
          Test guardrail policy
          <Icon name="arrow" size={16} />
        </Link>
      </PageHeader>
      {remote.error && <Notice error>{remote.error}</Notice>}
      <section className="panel">
        <div className="panel-toolbar">
          <span className="section-label">
            Policy decisions <span className="count">{remote.rows.length}</span>
          </span>
          <Search value={query} onChange={setQuery} />
        </div>
        {remote.loading ? (
          <Loader />
        ) : remote.rows.length ? (
          <Table
            rows={filterRecords(remote.rows, query)}
            columns={[
              { key: "policy_id", title: "Policy" },
              { key: "decision", title: "Decision", badge: true },
              { key: "latency_ms", title: "Latency (ms)" },
              { key: "created_at", title: "Observed" },
            ]}
            actions={(row) => (
              <button className="text-button" onClick={() => setDetail(row)}>
                Inspect
              </button>
            )}
          />
        ) : (
          <Empty title="No runtime decisions recorded">
            Evaluate a request against a configured policy. Decisions and
            timings will appear here.
          </Empty>
        )}
        <RemoteMore remote={remote} />
      </section>
      <ReviewQueue />
      <div className="context-note">
        <Icon name="pulse" size={18} />
        <p>
          These are application policy decisions. Proxy-wide monitoring requires
          a separately configured Envoy and OPA deployment.
        </p>
      </div>
      {detail !== null && (
        <Detail
          value={detail}
          title="Runtime decision"
          close={() => setDetail(null)}
        />
      )}
    </>
  );
}
export function AuditPage() {
  const remote = useRemote("/audit");
  const [query, setQuery] = useState("");
  const [detail, setDetail] = useState<unknown>(null);
  return (
    <>
      <PageHeader
        eyebrow="Accountability"
        title="Audit trail"
        description="Review the recorded history of workspace changes and security-relevant actions."
      >
        <button
          className="button secondary"
          onClick={() => downloadJson(remote.data, "audit-export.json")}
          disabled={!remote.data}
        >
          <Icon name="download" size={17} />
          Export visible records
        </button>
      </PageHeader>
      {remote.error && <Notice error>{remote.error}</Notice>}
      <section className="panel">
        <div className="panel-toolbar">
          <span className="section-label">
            Audit events <span className="count">{remote.rows.length}</span>
          </span>
          <Search value={query} onChange={setQuery} />
        </div>
        {remote.loading ? (
          <Loader />
        ) : remote.rows.length ? (
          <Table
            rows={filterRecords(remote.rows, query)}
            columns={[
              { key: "action", title: "Action" },
              { key: "actor_id", title: "Actor" },
              { key: "resource_id", title: "Resource" },
              { key: "created_at", title: "Timestamp" },
            ]}
            actions={(row) => (
              <button className="text-button" onClick={() => setDetail(row)}>
                Details
              </button>
            )}
          />
        ) : (
          <Empty title="No audit events returned" />
        )}
        <RemoteMore remote={remote} />
      </section>
      {detail !== null && (
        <Detail
          value={detail}
          title="Audit event"
          close={() => setDetail(null)}
        />
      )}
    </>
  );
}
export function ReportsPage() {
  const remote = useRemote("/reports");
  const { api } = useSession();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState<unknown>(null);
  const generate = async () => {
    setBusy(true);
    setError("");
    try {
      const report = await api("/reports/export?format=json");
      downloadJson(
        report,
        `governance-report-${new Date().toISOString().slice(0, 10)}.json`,
      );
      setResult(report);
      await remote.refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Export failed");
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <PageHeader
        eyebrow="Reporting & exports"
        title="Governance reports"
        description="Export a tenant-scoped snapshot of the records supporting your governance program."
      />
      {(error || remote.error) && (
        <Notice error>{error || remote.error}</Notice>
      )}
      <div className="two-column">
        <section className="panel padded report-card">
          <div className="feature-icon">
            <Icon name="file" size={30} />
          </div>
          <span className="outline-tag">JSON export</span>
          <h2>Workspace governance report</h2>
          <p>
            Collect AI inventory, assessments, risks, findings and evidence
            metadata in a structured export for review and downstream
            integration.
          </p>
          <button
            className="button primary"
            disabled={busy}
            onClick={() => void generate()}
          >
            <Icon name="download" size={17} />
            {busy ? "Generating…" : "Generate & download"}
          </button>
        </section>
        <section className="panel padded">
          <h2>Scope and interpretation</h2>
          <p>
            Reports reflect stored records in the selected workspace at export
            time. They do not establish regulatory compliance or certification.
          </p>
          <p>
            Artifact contents and integration secrets are excluded from the
            governance summary. Use the evidence library to retrieve permitted
            artifacts.
          </p>
          <Link href="/audit" className="text-link">
            Review the audit history
            <Icon name="arrow" size={16} />
          </Link>
        </section>
      </div>
      {result !== null && (
        <section className="panel padded">
          <h2>Generated report preview</h2>
          <pre className="json-view">{JSON.stringify(result, null, 2)}</pre>
        </section>
      )}
      {remote.rows.length > 0 && (
        <section className="panel">
          <div className="panel-title">
            <h2>Report records</h2>
          </div>
          <Table
            rows={remote.rows}
            columns={[
              { key: "name", title: "Report" },
              { key: "created_at", title: "Generated" },
            ]}
          />
        </section>
      )}
    </>
  );
}
export function OrganisationPage() {
  const remote = useRemote("/memberships");
  const { api, data, refreshIdentity } = useSession();
  const [creating, setCreating] = useState(false);
  const [newTenant, setNewTenant] = useState(false);
  const [message, setMessage] = useState("");
  return (
    <>
      <PageHeader
        eyebrow="Workspace administration"
        title="Organisation & access"
        description="Manage membership and role-based access to this isolated workspace."
      >
        <button className="button secondary" onClick={() => setNewTenant(true)}>
          Create organisation
        </button>
        <button className="button primary" onClick={() => setCreating(true)}>
          <Icon name="plus" size={17} />
          Add member
        </button>
      </PageHeader>
      {remote.error && <Notice error>{remote.error}</Notice>}
      {message && <Notice>{message}</Notice>}
      <section className="panel">
        <div className="panel-title">
          <h2>Workspace members</h2>
          <span className="count">{remote.rows.length}</span>
        </div>
        {remote.loading ? (
          <Loader />
        ) : remote.rows.length ? (
          <Table
            rows={remote.rows}
            columns={[
              { key: "email", title: "Email" },
              { key: "name", title: "Name" },
              { key: "role", title: "Role", badge: true },
            ]}
            actions={(row) => (
              <MembershipActions member={row} refresh={remote.refresh} />
            )}
          />
        ) : (
          <Empty title="No memberships returned" />
        )}
      </section>
      <section className="panel padded">
        <h2>Your available workspaces</h2>
        <p>
          Use the workspace selector in the header to switch between your
          organisation memberships.
        </p>
        <div className="workspace-chips">
          {data?.memberships.map((m) => (
            <div key={m.tenant_id}>
              <Icon name="users" size={18} />
              <strong>{m.tenant_name}</strong>
              <Badge value={m.role} />
            </div>
          ))}
        </div>
      </section>
      {creating && (
        <Modal title="Add workspace member" close={() => setCreating(false)}>
          <Form
            fields={[
              { name: "email", label: "Email", type: "email", required: true },
              { name: "name", label: "Full name", required: true },
              {
                name: "password",
                label: "Initial password",
                type: "password",
                required: true,
                help: "Provide a strong unique password through a secure channel.",
              },
              {
                name: "role",
                label: "Role",
                type: "select",
                required: true,
                defaultValue: "viewer",
                options: statuses([
                  "organisation_admin",
                  "governance_manager",
                  "security_engineer",
                  "contributor",
                  "auditor",
                  "viewer",
                ]),
              },
            ]}
            onCancel={() => setCreating(false)}
            onSubmit={async (values) => {
              await api("/memberships", {
                method: "POST",
                body: JSON.stringify(values),
              });
              setCreating(false);
              await remote.refresh();
            }}
          />
        </Modal>
      )}
      {newTenant && (
        <Modal title="Create organisation" close={() => setNewTenant(false)}>
          <p className="modal-intro">
            Organisation creation requires the platform administrator role.
          </p>
          <Form
            fields={[
              { name: "name", label: "Organisation name", required: true },
            ]}
            onCancel={() => setNewTenant(false)}
            onSubmit={async (values) => {
              await api("/tenants", {
                method: "POST",
                body: JSON.stringify(values),
              });
              setNewTenant(false);
              await refreshIdentity();
              setMessage(
                "Organisation created. It is now available in the workspace selector.",
              );
            }}
          />
        </Modal>
      )}
    </>
  );
}
export function SettingsPage() {
  const remote = useRemote("/settings");
  const { api, data } = useSession();
  const [saved, setSaved] = useState(false);
  return (
    <>
      <PageHeader
        eyebrow="Administration"
        title="Workspace settings"
        description="Review application configuration and update tenant-scoped preferences."
      />
      {remote.error && <Notice error>{remote.error}</Notice>}
      {saved && <Notice>Workspace settings saved.</Notice>}
      <AccountSecurity />
      <div className="two-column">
        <section className="panel padded">
          <h2>Workspace configuration</h2>
          {remote.loading ? (
            <Loader />
          ) : (
            <Form
              key={JSON.stringify(remote.data)}
              submitLabel="Save settings"
              initial={(remote.data || {}) as Record<string, unknown>}
              fields={[
                { name: "name", label: "Workspace display name" },
                {
                  name: "retention_days",
                  label: "Retention days",
                  type: "number",
                  defaultValue: 365,
                  help: "Allowed range: 30?3650 days. Retention metadata requires an operational retention procedure.",
                },
                {
                  name: "notification_email",
                  label: "Notification contact email",
                  type: "email",
                  help: "Contact metadata; outbound notification delivery requires a separately configured service.",
                },
              ]}
              onSubmit={async (values) => {
                await api("/settings", {
                  method: "PATCH",
                  body: JSON.stringify(values),
                });
                setSaved(true);
                await remote.refresh();
              }}
            />
          )}
        </section>
        <section className="panel padded">
          <h2>Connection information</h2>
          <dl className="key-values">
            <dt>Signed in as</dt>
            <dd>{data?.user.email}</dd>
            <dt>API endpoint</dt>
            <dd className="mono">{API_URL}</dd>
            <dt>API version</dt>
            <dd>v1</dd>
            <dt>Session storage</dt>
            <dd>Browser memory · cleared on page reload</dd>
          </dl>
          <p className="muted">
            The application is an independently deployed governance engine. API
            integration with Guardrail Sovereign is a future, separately
            authorized phase.
          </p>
        </section>
      </div>
    </>
  );
}
