"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import { listOf, pageInfo } from "@/lib/api";
import { useSession } from "./session";

export function useRemote(path: string, poll = false) {
  const { api } = useSession();
  const [data, setData] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [total, setTotal] = useState(0);
  const [more, setMore] = useState(false);
  const sequence = useRef(0);
  const refresh = useCallback(async () => {
    const request = ++sequence.current;
    try {
      const result = await api(path);
      if (request !== sequence.current) return;
      setData(result);
      setTotal(pageInfo(result)?.total ?? listOf(result).length);
      setError("");
    } catch (e) {
      if (request === sequence.current)
        setError(e instanceof Error ? e.message : "Unable to load data");
    } finally {
      if (request === sequence.current) setLoading(false);
    }
  }, [api, path]);
  useEffect(() => {
    setLoading(true);
    setData(null);
    void refresh();
    const timer = poll ? setInterval(() => void refresh(), 5000) : undefined;
    return () => {
      ++sequence.current;
      clearInterval(timer);
    };
  }, [refresh, poll]);
  const loadMore = async () => {
    const request = ++sequence.current;
    setMore(true);
    try {
      const next = await api(
        `${path}${path.includes("?") ? "&" : "?"}limit=100&offset=${listOf(data).length}`,
      );
      if (request !== sequence.current) return;
      setData([...listOf(data), ...listOf(next)]);
      setTotal(pageInfo(next)?.total ?? total);
      setError("");
    } catch (e) {
      if (request === sequence.current) setError(String(e));
    } finally {
      setMore(false);
    }
  };
  return {
    data,
    loading,
    error,
    refresh,
    rows: listOf(data),
    total,
    more,
    loadMore,
  };
}

export function RemoteMore({
  remote,
}: {
  remote: ReturnType<typeof useRemote>;
}) {
  if (remote.loading || !remote.total) return null;
  return (
    <div className="panel-footnote">
      Showing {remote.rows.length} of {remote.total} records. Search filters the
      loaded records.
      {remote.rows.length < remote.total && (
        <button
          className="button secondary small"
          disabled={remote.more}
          onClick={() => void remote.loadMore()}
        >
          {remote.more ? "Loading…" : "Load more records"}
        </button>
      )}
    </div>
  );
}
