import { afterEach, describe, expect, it, vi } from "vitest";
import {
  ApiError,
  errorMessage,
  filterRecords,
  listOf,
  makeApi,
} from "../../src/lib/api";
afterEach(() => vi.unstubAllGlobals());
describe("tenant-scoped API requests", () => {
  it("sends tenant and bearer headers without browser cookies", async () => {
    const fetcher = vi
      .fn()
      .mockResolvedValue(
        new Response(JSON.stringify({ id: "record-1" }), { status: 200 }),
      );
    vi.stubGlobal("fetch", fetcher);
    const result = await makeApi("test-session-token", "tenant-a")("/systems", {
      method: "POST",
      body: JSON.stringify({ name: "System A" }),
    });
    expect(result).toEqual({ id: "record-1" });
    const options = fetcher.mock.calls[0][1];
    expect(options.headers.get("Authorization")).toBe(
      "Bearer test-session-token",
    );
    expect(options.headers.get("X-Tenant-ID")).toBe("tenant-a");
    expect(options.headers.get("Content-Type")).toBe("application/json");
    expect(options.credentials).toBe("omit");
    expect(options.cache).toBe("no-store");
  });
  it("clears authenticated state on expiry and reports a normalized error", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Session expired" }), {
          status: 401,
        }),
      ),
    );
    const expired = vi.fn();
    await expect(
      makeApi("expired-token", "tenant-a", expired)("/systems"),
    ).rejects.toEqual(new ApiError(401, "Session expired"));
    expect(expired).toHaveBeenCalledOnce();
  });
  it("does not clear session for an authorization denial", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Insufficient permission" }), {
          status: 403,
        }),
      ),
    );
    const expired = vi.fn();
    await expect(
      makeApi("session", "tenant-a", expired)("/settings"),
    ).rejects.toMatchObject({ status: 403 });
    expect(expired).not.toHaveBeenCalled();
  });
  it("supports logout with an empty response", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 204 })),
    );
    await expect(
      makeApi("session", "tenant-a")("/auth/logout", { method: "POST" }),
    ).resolves.toBeUndefined();
  });
});
describe("record handling", () => {
  it("extracts known collection envelopes and rejects noncollections", () => {
    expect(listOf({ items: [{ id: "1" }] })).toEqual([{ id: "1" }]);
    expect(listOf({ message: "unavailable" })).toEqual([]);
  });
  it("filters case-insensitively across fields", () => {
    expect(
      filterRecords(
        [
          { id: "1", name: "Vision Model", owner: "Research" },
          { id: "2", name: "Support" },
        ],
        " RESEARCH ",
      ).map((r) => r.id),
    ).toEqual(["1"]);
  });
  it("reports validation details without rendering markup", () => {
    expect(errorMessage([{ loc: ["body"], msg: "Invalid input" }])).toBe(
      "Invalid input",
    );
    expect(errorMessage("<script>alert(1)</script>")).toBe(
      "<script>alert(1)</script>",
    );
  });
});
