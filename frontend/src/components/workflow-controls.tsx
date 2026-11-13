"use client";
import { useState } from "react";
import { downloadJson, RecordData } from "@/lib/api";
import { useSession } from "./session";
import { RemoteMore, useRemote } from "./remote";
import { Detail, Empty, Form, Loader, Modal, Notice, Table } from "./ui";

export function AssessmentActions({
  record,
  refresh,
}: {
  record: RecordData;
  refresh: () => Promise<void>;
}) {
  const { api } = useSession();
  const [history, setHistory] = useState<unknown>(null);
  const [error, setError] = useState("");
  const action = async (fn: () => Promise<void>) => {
    try {
      setError("");
      await fn();
    } catch (e) {
      setError(String(e));
    }
  };
  return (
    <div className="form-actions">
      <button
        className="button secondary"
        onClick={() =>
          void action(async () =>
            setHistory(await api(`/assessments/${record.id}/history`)),
          )
        }
      >
        Assessment history
      </button>
      <button
        className="button secondary"
        onClick={() =>
          void action(async () =>
            downloadJson(
              await api(`/assessments/${record.id}/export`),
              `assessment-${record.id}.json`,
            ),
          )
        }
      >
        Export assessment
      </button>
      <button
        className="button secondary"
        onClick={() =>
          void action(async () => {
            await api(`/assessments/${record.id}`, {
              method: "PATCH",
              headers: { "If-Match": String(record.version) },
              body: JSON.stringify({
                status:
                  record.status === "completed" ? "in_progress" : "completed",
              }),
            });
            await refresh();
          })
        }
      >
        {record.status === "completed"
          ? "Reopen assessment"
          : "Complete assessment"}
      </button>
      {error && <Notice error>{error}</Notice>}
      {history !== null && (
        <Detail
          title="Assessment history"
          value={history}
          close={() => setHistory(null)}
        />
      )}
    </div>
  );
}

export function PolicyHistory({
  policy,
  refresh,
}: {
  policy: RecordData;
  refresh: () => Promise<void>;
}) {
  const { api } = useSession();
  const [open, setOpen] = useState(false);
  return (
    <>
      <button className="text-button" onClick={() => setOpen(true)}>
        Version history
      </button>
      {open && (
        <Modal
          title="Policy versions and rollback"
          close={() => setOpen(false)}
        >
          <PolicyVersions policy={policy} refresh={refresh} />
        </Modal>
      )}
    </>
  );
}
function PolicyVersions({
  policy,
  refresh,
}: {
  policy: RecordData;
  refresh: () => Promise<void>;
}) {
  const remote = useRemote(`/policies/${policy.id}/versions`);
  const { api } = useSession();
  const [selected, setSelected] = useState<RecordData | null>(null);
  const [message, setMessage] = useState("");
  return (
    <>
      <p>
        Current version: {String(policy.version)}. Rollback creates a new
        version and preserves history.
      </p>
      {remote.error && <Notice error>{remote.error}</Notice>}
      {message && <Notice>{message}</Notice>}
      {remote.loading ? (
        <Loader />
      ) : !remote.rows.length ? (
        <Empty title="No previous versions" />
      ) : (
        <Table
          rows={remote.rows}
          columns={[
            { key: "revision", title: "Version" },
            { key: "created_at", title: "Replaced at" },
            { key: "actor_id", title: "Actor" },
          ]}
          actions={(row) => (
            <button className="text-button" onClick={() => setSelected(row)}>
              Review rollback
            </button>
          )}
        />
      )}
      {selected && (
        <>
          <pre className="json-view">
            {JSON.stringify(selected.snapshot, null, 2)}
          </pre>
          <Form
            fields={[]}
            submitLabel={`Restore version ${selected.revision}`}
            onCancel={() => setSelected(null)}
            onSubmit={async () => {
              await api(`/policies/${policy.id}/rollback`, {
                method: "POST",
                headers: { "If-Match": String(policy.version) },
                body: JSON.stringify({ revision: selected.revision }),
              });
              setSelected(null);
              setMessage("Policy restored as a new version.");
              await remote.refresh();
              await refresh();
            }}
          />
        </>
      )}
    </>
  );
}

export function ReviewQueue() {
  const remote = useRemote("/runtime/reviews");
  const { api } = useSession();
  const [selected, setSelected] = useState<RecordData | null>(null);
  return (
    <section className="panel">
      <div className="panel-title">
        <h2>Human review queue</h2>
        <button className="text-button" onClick={() => void remote.refresh()}>
          Refresh reviews
        </button>
      </div>
      {remote.error && <Notice error>{remote.error}</Notice>}
      {remote.loading ? (
        <Loader />
      ) : !remote.rows.length ? (
        <Empty title="No reviews requested" />
      ) : (
        <Table
          rows={remote.rows}
          columns={[
            { key: "event_id", title: "Decision event" },
            { key: "status", title: "Status", badge: true },
            { key: "resolution", title: "Resolution" },
            { key: "created_at", title: "Requested" },
          ]}
          actions={(row) =>
            row.status === "pending" ? (
              <button className="text-button" onClick={() => setSelected(row)}>
                Resolve review
              </button>
            ) : null
          }
        />
      )}
      <RemoteMore remote={remote} />
      {selected && (
        <Modal title="Resolve runtime review" close={() => setSelected(null)}>
          <p>
            This records a human decision. It does not automatically replay or
            release the original request. Prompts are not retained.
          </p>
          <Form
            fields={[
              {
                name: "resolution",
                label: "Decision",
                type: "select",
                required: true,
                options: [
                  { value: "block", label: "Block" },
                  { value: "allow", label: "Allow" },
                ],
              },
              {
                name: "notes",
                label: "Review rationale",
                type: "textarea",
                required: true,
                help: "Do not enter prompts, secrets or personal data.",
              },
              { name: "owner", label: "Responsible owner" },
            ]}
            onCancel={() => setSelected(null)}
            onSubmit={async (values) => {
              await api(`/runtime/reviews/${selected.id}`, {
                method: "PATCH",
                body: JSON.stringify(values),
              });
              setSelected(null);
              await remote.refresh();
            }}
          />
        </Modal>
      )}
    </section>
  );
}

export function AccountSecurity() {
  const { api, logout } = useSession();
  return (
    <section className="panel padded">
      <h2>Change your password</h2>
      <p>
        A successful change revokes all your sessions. Sign in again with the
        new password.
      </p>
      <Form
        submitLabel="Change password"
        fields={[
          {
            name: "current_password",
            label: "Current password",
            type: "password",
            required: true,
          },
          {
            name: "new_password",
            label: "New password",
            type: "password",
            required: true,
            help: "Use at least 12 characters.",
          },
        ]}
        onSubmit={async (values) => {
          await api("/auth/password", {
            method: "POST",
            body: JSON.stringify(values),
          });
          await logout();
        }}
      />
    </section>
  );
}

export function MembershipActions({
  member,
  refresh,
}: {
  member: RecordData;
  refresh: () => Promise<void>;
}) {
  const { api, refreshIdentity } = useSession();
  const [mode, setMode] = useState<"role" | "remove" | null>(null);
  const roles = [
    "organisation_admin",
    "governance_manager",
    "security_engineer",
    "contributor",
    "auditor",
    "viewer",
  ];
  return (
    <>
      <button className="text-button" onClick={() => setMode("role")}>
        Change role
      </button>
      <button
        className="text-button danger-text"
        onClick={() => setMode("remove")}
      >
        Remove access
      </button>
      {mode && (
        <Modal
          title={
            mode === "role" ? "Change member role" : "Remove workspace access"
          }
          close={() => setMode(null)}
        >
          <p>
            {String(member.email)}. At least one organisation administrator must
            remain.
          </p>
          <Form
            initial={{ role: member.role }}
            fields={
              mode === "role"
                ? [
                    {
                      name: "role",
                      label: "New role",
                      type: "select",
                      required: true,
                      options: roles.map((value) => ({
                        value,
                        label: value.replaceAll("_", " "),
                      })),
                    },
                  ]
                : []
            }
            submitLabel={
              mode === "role" ? "Update role" : "Remove workspace membership"
            }
            onCancel={() => setMode(null)}
            onSubmit={async (values) => {
              await api(`/memberships/${member.id}`, {
                method: mode === "role" ? "PATCH" : "DELETE",
                ...(mode === "role" ? { body: JSON.stringify(values) } : {}),
              });
              setMode(null);
              await refresh();
              await refreshIdentity();
            }}
          />
        </Modal>
      )}
    </>
  );
}
