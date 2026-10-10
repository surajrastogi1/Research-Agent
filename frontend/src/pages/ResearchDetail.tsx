import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import ReactMarkdown from "react-markdown";
import { apiFetch } from "../lib/api";

type Source = {
  id: string;
  title: string | null;
  url: string;
  content: string | null;
  created_at: string;
};

type Research = {
  id: string;
  user_id: string;
  question: string;
  status: "pending" | "processing" | "completed" | "failed";
  report: string | null;
  created_at: string;
  completed_at: string | null;
  sources: Source[];
};

const statusColors: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  processing: "bg-blue-100 text-blue-800",
  completed: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
};

export default function ResearchDetail() {
  const { id } = useParams<{ id: string }>();
  const [item, setItem] = useState<Research | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id) return;

    let cancelled = false;
    let pollTimer: ReturnType<typeof setTimeout> | null = null;

    async function load() {
      try {
        const data = await apiFetch<Research>(`/research/${id}`);
        if (cancelled) return;
        setItem(data);
        setLoading(false);

        // Keep polling while the job is still running
        if (data.status === "pending" || data.status === "processing") {
          pollTimer = setTimeout(load, 3000);
        }
      } catch (err) {
        if (cancelled) return;
        setError(err instanceof Error ? err.message : "Failed to load");
        setLoading(false);
      }
    }

    load();

    return () => {
      cancelled = true;
      if (pollTimer) clearTimeout(pollTimer);
    };
  }, [id]);

  if (loading) {
    return <div className="max-w-4xl mx-auto p-8 text-gray-500">Loading...</div>;
  }

  if (error || !item) {
    return (
      <div className="max-w-4xl mx-auto p-8">
        <Link to="/" className="text-blue-600 hover:underline text-sm">
          ← Back to dashboard
        </Link>
        <div className="mt-4 text-red-600">{error || "Not found"}</div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-8">
      <Link to="/" className="text-blue-600 hover:underline text-sm">
        ← Back to dashboard
      </Link>

      <div className="mt-4 mb-6">
        <div className="flex items-start justify-between gap-4">
          <h1 className="text-2xl font-bold flex-1">{item.question}</h1>
          <span
            className={`text-xs font-medium px-2 py-1 rounded-full whitespace-nowrap ${
              statusColors[item.status] || "bg-gray-100 text-gray-800"
            }`}
          >
            {item.status}
          </span>
        </div>

        <p className="text-sm text-gray-500 mt-2">
          Started {new Date(item.created_at).toLocaleString()}
          {item.completed_at && (
            <> · Completed {new Date(item.completed_at).toLocaleString()}</>
          )}
        </p>
      </div>

      {/* Sources */}
      {item.sources.length > 0 && (
        <div className="mb-8 bg-gray-50 border rounded-lg p-4">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">
            Sources ({item.sources.length})
          </h2>
          <ol className="space-y-1.5 list-decimal list-inside text-sm">
            {item.sources.map((src) => (
              <li key={src.id}>
                <a
                  href={src.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-blue-600 hover:underline"
                >
                  {src.title || src.url}
                </a>
              </li>
            ))}
          </ol>
        </div>
      )}

      {/* Report */}
      {item.report ? (
        <article className="bg-white border rounded-lg p-6 prose prose-slate max-w-none">
          <ReactMarkdown>{item.report}</ReactMarkdown>
        </article>
      ) : (
        <div className="text-center py-16 bg-white rounded-lg border border-dashed">
          <p className="text-gray-500">
            {item.status === "failed"
              ? "This research failed to complete."
              : "Report is still being generated..."}
          </p>
        </div>
      )}
    </div>
  );
}