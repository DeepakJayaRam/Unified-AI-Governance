"use client";
export default function ErrorPage({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="main-content">
      <section className="panel padded">
        <h1>The workspace could not be displayed</h1>
        <p>
          Retry the page. If this continues, contact your administrator with the
          time of the error.
        </p>
        <button className="button primary" onClick={reset}>
          Retry page
        </button>
      </section>
    </main>
  );
}
