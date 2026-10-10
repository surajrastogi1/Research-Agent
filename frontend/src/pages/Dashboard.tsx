import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
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

export default function Dashboard() {
  const [items, setItems] = useState<Research[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function load() {
      try {
        const data = await apiFetch<Research[]>("/research/");
        setItems(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) {
    return <div className="max-w-5xl mx-auto p-8 text-gray-500">Loading...</div>;
  }

  if (error) {
    return <div className="max-w-5xl mx-auto p-8 text-red-600">{error}</div>;
  }

  return (
    <div className="max-w-5xl mx-auto p-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Your Research</h1>
        <Link
          to="/new"
          className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
        >
          + New Research
        </Link>
      </div>

      {items.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-lg border border-dashed">
          <p className="text-gray-500 mb-4">No research yet.</p>
          <Link
            to="/new"
            className="text-blue-600 hover:underline font-medium"
          >
            Start your first one →
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {items.map((item) => (
            <Link
              key={item.id}
              to={`/research/${item.id}`}
              className="block bg-white border rounded-lg p-4 hover:border-blue-400 transition"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{item.question}</p>
                  <p className="text-sm text-gray-500 mt-1">
                    {new Date(item.created_at).toLocaleString()}
                    {item.sources.length > 0 && (
                      <> · {item.sources.length} sources</>
                    )}
                  </p>
                </div>
                <span
                  className={`text-xs font-medium px-2 py-1 rounded-full whitespace-nowrap ${
                    statusColors[item.status] || "bg-gray-100 text-gray-800"
                  }`}
                >
                  {item.status}
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}