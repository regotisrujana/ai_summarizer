import { useState } from "react";
import { summarizeContent } from "./api";

export default function App() {
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [summary, setSummary] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSummary("");
    setCopied(false);

    if (!url.trim() && !text.trim()) {
      setError("Paste article text or enter a URL.");
      return;
    }

    setLoading(true);
    try {
      const data = await summarizeContent({ text, url });
      setSummary(data.summary || "");
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        err.message ||
        "Something went wrong. Try again.";
      setError(typeof message === "string" ? message : JSON.stringify(message));
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async () => {
    if (!summary) return;
    await navigator.clipboard.writeText(summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen px-4 py-8 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-2xl">
        <header className="mb-8 text-center">
          <h1 className="text-3xl font-bold tracking-tight text-slate-900 sm:text-4xl">
            AI Content Summarizer
          </h1>
          <p className="mt-2 text-slate-600">
            Get all important points from any article, text, or YouTube video.
          </p>
        </header>

        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
        >
          <label className="mb-1 block text-sm font-medium text-slate-700">
            Article URL (optional)
          </label>
          <input
            type="url"
            placeholder="https://youtube.com/watch?v=... or article URL"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            className="mb-4 w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
          />

          <label className="mb-1 block text-sm font-medium text-slate-700">
            Or paste text
          </label>
          <textarea
            rows={8}
            placeholder="Paste your article or notes here..."
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="mb-6 w-full resize-y rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-2 focus:ring-indigo-200"
          />

          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 px-4 py-3 text-sm font-semibold text-white shadow-md transition hover:from-indigo-700 hover:to-violet-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {loading ? "Summarizing..." : "Summarize"}
          </button>

          {loading && (
            <div className="mt-4 flex justify-center">
              <div
                className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-200 border-t-indigo-600"
                role="status"
                aria-label="Loading"
              />
            </div>
          )}

          {error && (
            <p className="mt-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700">
              {error}
            </p>
          )}
        </form>

        {summary && (
          <section className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="mb-3 flex items-center justify-between gap-2">
              <h2 className="text-lg font-semibold text-slate-900">
                Key points
              </h2>
              <button
                type="button"
                onClick={handleCopy}
                className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
              >
                {copied ? "Copied!" : "Copy"}
              </button>
            </div>
            <div className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
              {summary}
            </div>
          </section>
        )}

        <p className="mt-6 text-center text-xs text-slate-500">
          Lists all important ideas as bullets. YouTube and article URLs supported.
        </p>
      </div>
    </div>
  );
}
