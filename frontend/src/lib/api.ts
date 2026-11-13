export const API_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8100/api/v1";
export type RecordData = Record<string, unknown> & { id: string };
export type PageInfo = { total: number; limit: number; offset: number };
export function pageInfo(data: unknown): PageInfo | undefined {
  return data && typeof data === "object"
    ? (data as { __page?: PageInfo }).__page
    : undefined;
}
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}
export function errorMessage(value: unknown): string {
  if (typeof value === "string") return value;
  if (Array.isArray(value))
    return value
      .map((v) =>
        typeof v === "object" && v && "msg" in v ? String(v.msg) : String(v),
      )
      .join("; ");
  if (value && typeof value === "object") return JSON.stringify(value);
  return "The request could not be completed.";
}
export function makeApi(token: string, tenant: string, expired?: () => void) {
  return async function api<T = unknown>(
    path: string,
    options: RequestInit = {},
  ): Promise<T> {
    const headers = new Headers(options.headers);
    if (token) headers.set("Authorization", `Bearer ${token}`);
    if (tenant) headers.set("X-Tenant-ID", tenant);
    if (options.body && !(options.body instanceof FormData))
      headers.set("Content-Type", "application/json");
    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      headers,
      cache: "no-store",
      credentials: "omit",
    });
    if (!response.ok) {
      const data = await response
        .json()
        .catch(() => ({ detail: response.statusText }));
      if (response.status === 401 && token) expired?.();
      throw new ApiError(
        response.status,
        errorMessage(data.detail ?? data.message ?? data),
      );
    }
    if (response.status === 204) return undefined as T;
    const payload = await response.json();
    if (Array.isArray(payload) && response.headers.has("X-Total-Count")) {
      Object.defineProperty(payload, "__page", {
        value: {
          total: Number(response.headers.get("X-Total-Count")),
          limit: Number(response.headers.get("X-Page-Limit")),
          offset: Number(response.headers.get("X-Page-Offset")),
        },
      });
    }
    return payload as T;
  };
}
export function label(value: unknown): string {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value).replace(/_/g, " ");
}
export function listOf(value: unknown): RecordData[] {
  if (Array.isArray(value)) return value as RecordData[];
  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;
    for (const key of ["items", "results", "integrations", "data"])
      if (Array.isArray(record[key])) return record[key] as RecordData[];
  }
  return [];
}
export function filterRecords(
  records: RecordData[],
  query: string,
): RecordData[] {
  const needle = query.trim().toLowerCase();
  return needle
    ? records.filter((record) =>
        Object.values(record).some(
          (value) =>
            typeof value === "string" && value.toLowerCase().includes(needle),
        ),
      )
    : records;
}
export function downloadJson(value: unknown, filename: string) {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(value, null, 2)], { type: "application/json" }),
  );
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}
