import { useState } from "react";
import { askRagChatbot, evaluateRag, summarizeContent } from "./api";

const tabs = [
  { id: "summarizer", label: "Summarizer" },
  { id: "chat", label: "RAG Chat" },
  { id: "evaluation", label: "Evaluation" },
];

function formatPercent(value) {
  return `${Math.round((value || 0) * 100)}%`;
}

export default function App() {
  const [activeTab, setActiveTab] = useState("chat");
  const [text, setText] = useState("");
  const [url, setUrl] = useState("");
  const [summary, setSummary] = useState("");
  const [question, setQuestion] = useState("");
  const [chatResult, setChatResult] = useState(null);
  const [evaluation, setEvaluation] = useState(null);
  const [loading, setLoading] = useState("");
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);

  const handleSummarize = async (event) => {
    event.preventDefault();
    setError("");
    setSummary("");
    setCopied(false);

    if (!url.trim() && !text.trim()) {
      setError("Paste article text or enter a URL.");
      return;
    }

    setLoading("summary");
    try {
      const data = await summarizeContent({ text, url });
      setSummary(data.summary || "");
    } catch (err) {
      showError(err);
    } finally {
      setLoading("");
    }
  };

  const handleChat = async (event) => {
    event.preventDefault();
    setError("");
    setChatResult(null);

    if (!question.trim()) {
      setError("Ask a question about AI summarization or RAG.");
      return;
    }

    setLoading("chat");
    try {
      const data = await askRagChatbot({ question, topK: 3 });
      setChatResult(data);
    } catch (err) {
      showError(err);
    } finally {
      setLoading("");
    }
  };

  const handleEvaluate = async () => {
    setError("");
    setLoading("evaluation");
    try {
      const data = await evaluateRag();
      setEvaluation(data);
    } catch (err) {
      showError(err);
    } finally {
      setLoading("");
    }
  };

  const handleCopy = async () => {
    if (!summary) return;
    await navigator.clipboard.writeText(summary);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const showError = (err) => {
    const message =
      err.response?.data?.detail ||
      err.message ||
      "Something went wrong. Try again.";
    setError(typeof message === "string" ? message : JSON.stringify(message));
  };

  return (
    <div className="min-h-screen bg-slate-50 px-4 py-8 text-slate-900 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-5xl">
        <header className="mb-6">
          <p className="text-sm font-semibold uppercase tracking-wide text-teal-700">
            AI Summarizer Project
          </p>
          <h1 className="mt-2 text-3xl font-bold sm:text-4xl">
            Domain-Specific RAG Chatbot
          </h1>
          <p className="mt-2 max-w-3xl text-slate-600">
            Chat with a 50-document AI summarization knowledge base, inspect
            citations, and run retrieval plus answer quality evaluation.
          </p>
        </header>

        <nav className="mb-6 flex gap-2 rounded-lg border border-slate-200 bg-white p-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              onClick={() => {
                setActiveTab(tab.id);
                setError("");
              }}
              className={`flex-1 rounded-md px-3 py-2 text-sm font-semibold transition ${
                activeTab === tab.id
                  ? "bg-slate-900 text-white"
                  : "text-slate-600 hover:bg-slate-100"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        {error && (
          <p className="mb-4 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        )}

        {activeTab === "summarizer" && (
          <section className="grid gap-6 lg:grid-cols-[1fr_0.9fr]">
            <form
              onSubmit={handleSummarize}
              className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
            >
              <label className="mb-1 block text-sm font-medium text-slate-700">
                Article URL
              </label>
              <input
                type="url"
                placeholder="https://youtube.com/watch?v=... or article URL"
                value={url}
                onChange={(event) => setUrl(event.target.value)}
                className="mb-4 w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-100"
              />

              <label className="mb-1 block text-sm font-medium text-slate-700">
                Or paste text
              </label>
              <textarea
                rows={9}
                placeholder="Paste your article or notes here..."
                value={text}
                onChange={(event) => setText(event.target.value)}
                className="mb-5 w-full resize-y rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-100"
              />

              <button
                type="submit"
                disabled={loading === "summary"}
                className="w-full rounded-md bg-teal-700 px-4 py-3 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading === "summary" ? "Summarizing..." : "Summarize"}
              </button>
            </form>

            <ResultPanel
              title="Key points"
              action={
                summary && (
                  <button
                    type="button"
                    onClick={handleCopy}
                    className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-50"
                  >
                    {copied ? "Copied" : "Copy"}
                  </button>
                )
              }
            >
              {summary ? (
                <div className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
                  {summary}
                </div>
              ) : (
                <EmptyState text="Your summary will appear here." />
              )}
            </ResultPanel>
          </section>
        )}

        {activeTab === "chat" && (
          <section className="grid gap-6 lg:grid-cols-[0.85fr_1.15fr]">
            <form
              onSubmit={handleChat}
              className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm"
            >
              <label className="mb-1 block text-sm font-medium text-slate-700">
                Ask the RAG chatbot
              </label>
              <textarea
                rows={7}
                placeholder="Example: How can retrieval accuracy be evaluated?"
                value={question}
                onChange={(event) => setQuestion(event.target.value)}
                className="mb-5 w-full resize-y rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-teal-600 focus:outline-none focus:ring-2 focus:ring-teal-100"
              />
              <button
                type="submit"
                disabled={loading === "chat"}
                className="w-full rounded-md bg-teal-700 px-4 py-3 text-sm font-semibold text-white transition hover:bg-teal-800 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {loading === "chat" ? "Retrieving..." : "Ask"}
              </button>
            </form>

            <ResultPanel title="Answer with sources">
              {chatResult ? (
                <div className="space-y-5">
                  <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-700">
                    {chatResult.answer}
                  </p>
                  <div>
                    <h3 className="mb-2 text-sm font-semibold text-slate-900">
                      Retrieved sources
                    </h3>
                    <div className="space-y-3">
                      {chatResult.sources.map((source) => (
                        <article
                          key={source.id}
                          className="rounded-md border border-slate-200 bg-slate-50 p-3"
                        >
                          <div className="flex items-start justify-between gap-3">
                            <div>
                              <p className="text-sm font-semibold text-slate-900">
                                {source.id} - {source.title}
                              </p>
                              <p className="text-xs uppercase tracking-wide text-slate-500">
                                {source.category}
                              </p>
                            </div>
                            <span className="rounded bg-white px-2 py-1 text-xs font-medium text-slate-600">
                              {source.score}
                            </span>
                          </div>
                          <p className="mt-2 text-sm leading-relaxed text-slate-600">
                            {source.text}
                          </p>
                        </article>
                      ))}
                    </div>
                  </div>
                </div>
              ) : (
                <EmptyState text="Ask a question to retrieve evidence from the 50-document corpus." />
              )}
            </ResultPanel>
          </section>
        )}

        {activeTab === "evaluation" && (
          <section className="space-y-5">
            <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="text-lg font-semibold">RAG evaluation</h2>
                  <p className="mt-1 text-sm text-slate-600">
                    Runs a fixed question set against retrieval and reference
                    answers to produce repeatable project metrics.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={handleEvaluate}
                  disabled={loading === "evaluation"}
                  className="rounded-md bg-slate-900 px-4 py-2 text-sm font-semibold text-white transition hover:bg-slate-700 disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {loading === "evaluation" ? "Running..." : "Run evaluation"}
                </button>
              </div>
            </div>

            {evaluation ? (
              <>
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
                  <Metric label="Documents" value={evaluation.document_count} />
                  <Metric label="Questions" value={evaluation.question_count} />
                  <Metric
                    label="Top-1"
                    value={formatPercent(evaluation.top1_accuracy)}
                  />
                  <Metric
                    label="Top-3"
                    value={formatPercent(evaluation.topk_accuracy)}
                  />
                  <Metric
                    label="Answer F1"
                    value={formatPercent(evaluation.answer_quality_f1)}
                  />
                </div>

                <div className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
                  <table className="w-full border-collapse text-left text-sm">
                    <thead className="bg-slate-100 text-xs uppercase tracking-wide text-slate-600">
                      <tr>
                        <th className="px-3 py-3">Question</th>
                        <th className="px-3 py-3">Expected</th>
                        <th className="px-3 py-3">Retrieved</th>
                        <th className="px-3 py-3">F1</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-200">
                      {evaluation.results.map((result) => (
                        <tr key={result.question}>
                          <td className="px-3 py-3 text-slate-700">
                            {result.question}
                          </td>
                          <td className="px-3 py-3 text-slate-600">
                            {result.expected_doc_ids.join(", ")}
                          </td>
                          <td className="px-3 py-3 text-slate-600">
                            {result.retrieved_doc_ids.join(", ")}
                          </td>
                          <td className="px-3 py-3 font-semibold text-slate-900">
                            {formatPercent(result.answer_f1)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            ) : (
              <EmptyState text="Run the evaluator to show retrieval accuracy and answer quality." />
            )}
          </section>
        )}
      </div>
    </div>
  );
}

function ResultPanel({ title, action, children }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="mb-3 flex items-center justify-between gap-2">
        <h2 className="text-lg font-semibold text-slate-900">{title}</h2>
        {action}
      </div>
      {children}
    </section>
  );
}

function EmptyState({ text }) {
  return (
    <div className="rounded-md border border-dashed border-slate-300 bg-slate-50 px-4 py-8 text-center text-sm text-slate-500">
      {text}
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
        {label}
      </p>
      <p className="mt-2 text-2xl font-bold text-slate-900">{value}</p>
    </div>
  );
}
