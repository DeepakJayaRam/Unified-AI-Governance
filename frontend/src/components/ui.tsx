"use client";
import { useEffect, useId, useRef, useState } from "react";
import { label, RecordData } from "@/lib/api";

export function Icon({ name, size = 20 }: { name: string; size?: number }) {
  const paths: Record<string, React.ReactNode> = {
    grid: (
      <>
        <rect x="3" y="3" width="7" height="7" rx="1.5" />
        <rect x="14" y="3" width="7" height="7" rx="1.5" />
        <rect x="3" y="14" width="7" height="7" rx="1.5" />
        <rect x="14" y="14" width="7" height="7" rx="1.5" />
      </>
    ),
    shield: (
      <>
        <path d="M12 3 21 7v5c0 5-9 9-9 9s-9-4-9-9V7l9-4Z" />
        <path d="m8 12 3 3 5-6" />
      </>
    ),
    box: (
      <>
        <path d="m12 3 9 5v9l-9 5-9-5V8l9-5Z M3 8l9 5 9-5 M12 13v9 M7.5 5.5l9 5" />
      </>
    ),
    scan: (
      <>
        <path d="M8 3H3v5 M16 3h5v5 M21 16v5h-5 M8 21H3v-5 M3 12h18" />
        <rect x="7" y="7" width="10" height="10" rx="2" />
      </>
    ),
    file: (
      <>
        <path d="M14 3H5v18h14V8l-5-5Z M14 3v5h5 M8 12h8 M8 16h6" />
      </>
    ),
    layers: (
      <>
        <path d="m12 3 10 5-10 5L2 8l10-5Z M2 12l10 5 10-5 M2 16l10 5 10-5" />
      </>
    ),
    risk: (
      <>
        <path d="m12 3 10 18H2L12 3Z M12 9v5 M12 17v.5" />
      </>
    ),
    lock: (
      <>
        <rect x="4" y="10" width="16" height="11" rx="2" />
        <path d="M8 10V7a4 4 0 0 1 8 0v3 M12 14v3" />
      </>
    ),
    pulse: (
      <>
        <path d="M2 12h5l3-8 4 16 3-8h5" />
      </>
    ),
    plug: (
      <>
        <path d="M8 3v5 M16 3v5 M5 8h14 M7 8v4a5 5 0 0 0 10 0V8 M12 17v4" />
      </>
    ),
    clock: (
      <>
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 2" />
      </>
    ),
    users: (
      <>
        <circle cx="9" cy="8" r="3" />
        <path d="M3 21v-3a6 6 0 0 1 12 0v3 M16 4a4 4 0 0 1 0 8 M18 15a5 5 0 0 1 3 5" />
      </>
    ),
    settings: (
      <>
        <path d="m9 3-1 3-3 1v4l-2 2 2 3 3 1 1 4h5l2-3 4-1v-4l2-2-2-3-3-1-1-4H9Z" />
        <circle cx="12" cy="12" r="3" />
      </>
    ),
    check: <path d="m5 12 4 4L19 6" />,
    arrow: <path d="M4 12h16 m-6-6 6 6-6 6" />,
    search: (
      <>
        <circle cx="10" cy="10" r="6" />
        <path d="m15 15 6 6" />
      </>
    ),
    plus: <path d="M12 5v14 M5 12h14" />,
    close: <path d="m6 6 12 12 M18 6 6 18" />,
    download: (
      <>
        <path d="M12 3v12 m-5-5 5 5 5-5 M4 16v5h16v-5" />
      </>
    ),
    menu: <path d="M3 6h18 M3 12h18 M3 18h18" />,
    refresh: (
      <>
        <path d="M20 7v5h-5 M4 17v-5h5 M6 6a8 8 0 0 1 13 2 M18 18A8 8 0 0 1 5 16" />
      </>
    ),
  };
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {paths[name] || paths.file}
    </svg>
  );
}
export function Badge({ value }: { value: unknown }) {
  const text = label(value);
  const tone =
    /connected|completed|succeeded|allow|low|implemented|verified|active/i.test(
      text,
    )
      ? "good"
      : /failed|block|critical|high|restricted|error/i.test(text)
        ? "danger"
        : /pending|queued|review|medium|planned|progress/i.test(text)
          ? "warn"
          : "neutral";
  return (
    <span className={`badge ${tone}`}>
      <span className="dot" />
      {text}
    </span>
  );
}
export function Notice({
  children,
  error = false,
}: {
  children: React.ReactNode;
  error?: boolean;
}) {
  return (
    <div
      role={error ? "alert" : "status"}
      className={`notice ${error ? "error" : ""}`}
    >
      {children}
    </div>
  );
}
export function Empty({
  title = "No records yet",
  children,
}: {
  title?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="empty">
      <div className="empty-icon">
        <Icon name="layers" size={27} />
      </div>
      <h3>{title}</h3>
      <p>
        {children ||
          "Create your first record to start building a traceable governance history."}
      </p>
    </div>
  );
}
export function Loader() {
  return (
    <div className="loading" role="status">
      <span className="spinner" />
      Loading workspace data…
    </div>
  );
}
export function Table({
  rows,
  columns,
  actions,
}: {
  rows: RecordData[];
  columns: { key: string; title: string; badge?: boolean }[];
  actions?: (row: RecordData) => React.ReactNode;
}) {
  return (
    <div className="table-scroll">
      <table>
        <thead>
          <tr>
            {columns.map((c) => (
              <th key={c.key}>{c.title}</th>
            ))}
            {actions && (
              <th>
                <span className="sr-only">Actions</span>
              </th>
            )}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={row.id || i}>
              {columns.map((c, n) => (
                <td key={c.key} className={n === 0 ? "primary-cell" : ""}>
                  {c.badge ? (
                    <Badge value={row[c.key]} />
                  ) : /created_at|due_date|timestamp/.test(c.key) &&
                    row[c.key] ? (
                    <time>
                      {new Date(String(row[c.key])).toLocaleString(undefined, {
                        dateStyle: "medium",
                        ...(c.key === "due_date"
                          ? {}
                          : { timeStyle: "short" as const }),
                      })}
                    </time>
                  ) : (
                    label(row[c.key])
                  )}
                </td>
              ))}
              {actions && <td className="row-actions">{actions(row)}</td>}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
export type Field = {
  name: string;
  label: string;
  type?:
    | "text"
    | "password"
    | "email"
    | "textarea"
    | "select"
    | "json"
    | "date"
    | "checkbox"
    | "number";
  required?: boolean;
  options?: { value: string; label: string }[];
  placeholder?: string;
  help?: string;
  defaultValue?: unknown;
};
export function Modal({
  title,
  children,
  close,
}: {
  title: string;
  children: React.ReactNode;
  close: () => void;
}) {
  const id = useId();
  const dialog = useRef<HTMLElement>(null);
  const closeRef = useRef(close);
  closeRef.current = close;
  useEffect(() => {
    const previousFocus = document.activeElement as HTMLElement | null;
    const firstInput = dialog.current?.querySelector<HTMLElement>(
      "input, select, textarea, button",
    );
    firstInput?.focus();
    const handler = (event: KeyboardEvent) => {
      const dialogs = document.querySelectorAll('[role="dialog"]');
      if (dialogs[dialogs.length - 1] !== dialog.current) return;
      if (event.key === "Escape") {
        event.preventDefault();
        closeRef.current();
      }
      if (event.key === "Tab") {
        const focusable = Array.from(
          dialog.current?.querySelectorAll<HTMLElement>(
            'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex="0"]',
          ) || [],
        );
        const first = focusable[0],
          last = focusable[focusable.length - 1];
        if (event.shiftKey && document.activeElement === first) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    };
    document.addEventListener("keydown", handler);
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", handler);
      document.body.style.overflow = prev;
      if (previousFocus?.isConnected) previousFocus.focus();
    };
  }, []);
  return (
    <div
      className="modal-backdrop"
      onClick={(event) => {
        if (event.target === event.currentTarget) close();
      }}
    >
      <section
        ref={dialog}
        role="dialog"
        aria-modal="true"
        aria-labelledby={id}
        className="modal"
      >
        <div className="modal-heading">
          <h2 id={id}>{title}</h2>
          <button
            className="icon-button"
            onClick={close}
            aria-label="Close dialog"
          >
            <Icon name="close" />
          </button>
        </div>
        {children}
      </section>
    </div>
  );
}
export function Form({
  fields,
  onSubmit,
  initial = {},
  submitLabel = "Save record",
  onCancel,
}: {
  fields: Field[];
  initial?: Record<string, unknown>;
  onSubmit: (values: Record<string, unknown>) => Promise<void>;
  submitLabel?: string;
  onCancel?: () => void;
}) {
  const [values, setValues] = useState<Record<string, unknown>>(() =>
    Object.fromEntries(
      fields.map((f) => [
        f.name,
        initial[f.name] ??
          f.defaultValue ??
          (f.type === "checkbox" ? false : ""),
      ]),
    ),
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  return (
    <form
      className="record-form"
      onSubmit={async (event) => {
        event.preventDefault();
        setBusy(true);
        setError("");
        try {
          const payload = { ...values };
          fields.forEach((f) => {
            if (f.type === "json")
              payload[f.name] =
                typeof values[f.name] === "string"
                  ? JSON.parse(String(values[f.name] || "{}"))
                  : values[f.name];
            if (f.type === "number") payload[f.name] = Number(values[f.name]);
            if (
              ["system_id", "finding_id", "due_date"].includes(f.name) &&
              !payload[f.name]
            )
              payload[f.name] = null;
          });
          await onSubmit(payload);
        } catch (e) {
          setError(e instanceof Error ? e.message : "Unable to save record");
        } finally {
          setBusy(false);
        }
      }}
    >
      {fields.map((field) => (
        <label
          className={`field ${field.type === "checkbox" ? "checkbox-field" : ""}`}
          key={field.name}
        >
          <span>
            {field.label}
            {field.required && <span className="required"> *</span>}
          </span>
          {field.type === "textarea" || field.type === "json" ? (
            <textarea
              aria-label={field.label}
              required={field.required}
              rows={field.type === "json" ? 7 : 3}
              className={field.type === "json" ? "code-input" : ""}
              value={
                typeof values[field.name] === "object"
                  ? JSON.stringify(values[field.name], null, 2)
                  : String(values[field.name] ?? "")
              }
              placeholder={field.placeholder}
              onChange={(e) =>
                setValues({ ...values, [field.name]: e.target.value })
              }
            />
          ) : field.type === "select" ? (
            <select
              aria-label={field.label}
              required={field.required}
              value={String(values[field.name] ?? "")}
              onChange={(e) =>
                setValues({ ...values, [field.name]: e.target.value })
              }
            >
              <option value="">Select {field.label.toLowerCase()}</option>
              {field.options?.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          ) : field.type === "checkbox" ? (
            <input
              aria-label={field.label}
              type="checkbox"
              checked={Boolean(values[field.name])}
              onChange={(e) =>
                setValues({ ...values, [field.name]: e.target.checked })
              }
            />
          ) : (
            <input
              aria-label={field.label}
              type={field.type || "text"}
              required={field.required}
              value={String(values[field.name] ?? "")}
              placeholder={field.placeholder}
              autoComplete={field.type === "password" ? "new-password" : "off"}
              onChange={(e) =>
                setValues({ ...values, [field.name]: e.target.value })
              }
            />
          )}{" "}
          {field.help && <small>{field.help}</small>}
        </label>
      ))}
      {error && <Notice error>{error}</Notice>}
      <div className="form-actions">
        {onCancel && (
          <button type="button" className="button secondary" onClick={onCancel}>
            Cancel
          </button>
        )}
        <button disabled={busy} className="button primary" type="submit">
          {busy ? "Saving…" : submitLabel}
        </button>
      </div>
    </form>
  );
}
export function Detail({
  value,
  title = "Record details",
  close,
}: {
  value: unknown;
  title?: string;
  close: () => void;
}) {
  return (
    <Modal title={title} close={close}>
      <pre className="json-view">{JSON.stringify(value, null, 2)}</pre>
    </Modal>
  );
}
