"use client";
import { useState } from "react";
import { downloadJson, filterRecords, RecordData } from "@/lib/api";
import { useSession } from "./session";
import { useRemote, RemoteMore } from "./remote";
import { Detail, Empty, Field, Form, Loader, Modal, Notice, Table } from "./ui";

export function GovernanceRecords({ framework }: { framework: string }) {
  const records = useRemote(`/governance-records?framework=${framework}`);
  const systems = useRemote("/systems");
  const assessments = useRemote("/assessments");
  const risks = useRemote("/risks");
  const evidence = useRemote("/evidence");
  const { api } = useSession();
  const [editing, setEditing] = useState<RecordData | "new" | null>(null);
  const [detail, setDetail] = useState<unknown>(null);
  const [query, setQuery] = useState("");
  const choices = (values: string[]) =>
    values.map((value) => ({ value, label: value.replaceAll("_", " ") }));
  const kinds =
    framework === "eu_ai_act"
      ? ["classification", "applicability", "obligation", "reassessment"]
      : framework === "iso42001"
        ? [
            "scope",
            "objective",
            "applicability",
            "management_review",
            "internal_audit",
            "risk_treatment",
            "reassessment",
          ]
        : ["scope", "objective", "risk_treatment", "reassessment"];
  const options = (rows: RecordData[]) =>
    rows.map((row) => ({
      value: row.id,
      label: String(row.name || row.title || row.id),
    }));
  const fields: Field[] = [
    { name: "title", label: "Record title", required: true },
    {
      name: "kind",
      label: "Workflow",
      type: "select",
      required: true,
      options: choices(kinds),
    },
    {
      name: "system_id",
      label: "AI system",
      type: "select",
      required: true,
      options: options(systems.rows),
    },
    {
      name: "assessment_id",
      label: "Linked assessment",
      type: "select",
      options: options(
        assessments.rows.filter((row) => row.framework === framework),
      ),
    },
    {
      name: "risk_id",
      label: "Linked risk",
      type: "select",
      options: options(risks.rows),
    },
    {
      name: "status",
      label: "Record status",
      type: "select",
      defaultValue: "draft",
      options: choices(["draft", "in_progress", "approved", "closed"]),
      required: true,
    },
    { name: "owner", label: "Responsible owner" },
    { name: "due_date", label: "Due date", type: "date" },
    { name: "rationale", label: "Assessment rationale", type: "textarea" },
    { name: "decision", label: "Decision or treatment plan", type: "textarea" },
    {
      name: "evidence_ids",
      label: "Supporting evidence",
      type: "multi-select",
      options: options(evidence.rows),
      help: "Use Ctrl or Command to select multiple records.",
    },
    {
      name: "source_url",
      label: "Authoritative source URL",
      help: "HTTPS source for this record; no external content is fetched.",
    },
    { name: "source_version", label: "Source version or date" },
  ];
  return (
    <section className="panel">
      <div className="panel-toolbar">
        <h2>Governance records</h2>
        <input
          aria-label="Search governance records"
          placeholder="Search loaded records"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button className="button primary" onClick={() => setEditing("new")}>
          Add governance record
        </button>
      </div>
      {records.error && <Notice error>{records.error}</Notice>}
      {records.loading ? (
        <Loader />
      ) : !records.rows.length ? (
        <Empty title="No governance records">
          Record scope, obligations, management decisions and treatment plans
          with evidence and ownership.
        </Empty>
      ) : (
        <Table
          rows={filterRecords(records.rows, query)}
          columns={[
            { key: "title", title: "Record" },
            { key: "kind", title: "Workflow" },
            { key: "status", title: "Status", badge: true },
            { key: "owner", title: "Owner" },
            { key: "due_date", title: "Due" },
          ]}
          actions={(row) => (
            <>
              <button className="text-button" onClick={() => setDetail(row)}>
                Traceability
              </button>
              <button className="text-button" onClick={() => setEditing(row)}>
                Edit record
              </button>
              <button
                className="text-button"
                onClick={() => downloadJson(row, `governance-${row.id}.json`)}
              >
                Export
              </button>
            </>
          )}
        />
      )}
      <RemoteMore remote={records} />
      {editing && (
        <Modal
          title={
            editing === "new"
              ? "Add governance record"
              : "Edit governance record"
          }
          close={() => setEditing(null)}
        >
          {[systems, assessments, risks, evidence].map((remote, i) => (
            <div key={i}>
              {remote.error && <Notice error>{remote.error}</Notice>}
              {remote.total > remote.rows.length && (
                <RemoteMore remote={remote} />
              )}
            </div>
          ))}
          <Form
            fields={fields}
            initial={editing === "new" ? {} : editing}
            onCancel={() => setEditing(null)}
            onSubmit={async (values) => {
              await api(
                "/governance-records" +
                  (editing === "new" ? "" : `/${editing.id}`),
                {
                  method: editing === "new" ? "POST" : "PATCH",
                  headers:
                    editing === "new"
                      ? {}
                      : { "If-Match": String(editing.version) },
                  body: JSON.stringify({ ...values, framework }),
                },
              );
              setEditing(null);
              await records.refresh();
            }}
          />
        </Modal>
      )}
      {detail !== null && (
        <Detail
          title="Governance traceability"
          value={detail}
          close={() => setDetail(null)}
        />
      )}
    </section>
  );
}
