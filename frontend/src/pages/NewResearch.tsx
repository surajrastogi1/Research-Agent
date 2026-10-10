import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { getToken } from "../lib/api";

type Source = { title: string; url: string; content: string };

const API_URL = import.meta.env.VITE_API_URL as string;

export default function NewResearch() {
  const navigate = useNavigate();
  const [question, setQuestion] = useState("");
  const [running, setRunning] = useState(false);
  const [stage, setStage] = useState<string>("");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [sources, setSources] = useState<Source[]>([]);
  const [report, setReport] = useState("");
  const [researchId, setResearchId] = useState<string | null>(null);
  const [error, setError] = useState("");

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!question.trim() || running) return;

    // Reset state
    setRunning(true);
    setStage("starting");
    setSearchQuery("");
    setSources([]);
    setReport("");
    setResearchId(null);
    setError("");

    try {
      const res = await fetch(`${API_URL}/research/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${getToken()}`,
        },
        body: JSON.stringify({ question }),
      });

      if (!res.ok || !res.body) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || "Request failed");
      }

      // Read the SSE stream manually
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });

        // SSE frames are separated by \n\n
        const frames = buffer.split("\n\n");
        buffer = frames.pop() || ""; // keep incomplete frame for next round

        for (const frame of frames) {
          if (!frame.trim()) continue;

          // Parse "event: X\ndata: {...}"
          let eventName = "message";
          let dataStr = "";
          for (const line of frame.split("\n")) {
            if (line.startsWith("event: ")) eventName = line.slice(7).trim();
            else if (line.startsWith("data: ")) dataStr += line.slice(6);
          }

          if (!dataStr) continue;
          const data = JSON.parse(dataStr);
          handleEvent(eventName, data);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setRunning(false);
    }
  }

  function handleEvent(name: string, data: any) {
    switch (name) {
      case "research_id":
        setResearchId(data.id);
        break;
      case "status":
        setStage(data.stage);
        if (data.query) setSearchQuery(data.query);
        break;
      case "sources":
        setSources(data);
        break;
      case "token":
        setReport((prev) => prev + data.text);
        break;
      case "done":
        // report + sources already streamed; nothing extra to do
        setStage("done");
        break;
      case "error":
        setError(data.message);
        break;
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-8">
      <h1 className="text-2xl font-bold mb-6">New Research</h1>

      <form onSubmit={handleSubmit} className="mb-6">
        <textarea
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question..."
          rows={3}
          disabled={running}
          className="w-full p-3 border rounded focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50"
        />
        <div className="mt-3 flex items-center justify-between">
          <div className="text-sm text-gray-500">
            {stage && <StatusLine stage={stage} />}
          </div>
          <button
            type="submit"
            disabled={running || !question.trim()}
            className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {running ? "Running..." : "Research"}
          </button>
        </div>
      </form>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 p-3 rounded mb-6">
          {error}
        </div>
      )}

      {searchQuery && (
        <div className="mb-4 text-sm text-gray-600">
          Search query: <span className="font-mono">{searchQuery}</span>
        </div>
      )}

      {sources.length > 0 && (
        <div className="mb-6">
          <h2 className="text-sm font-semibold text-gray-700 mb-2">
            Sources ({sources.length})
          </h2>
          <ul className="space-y-1">
            {sources.map((src, i) => (
              <li key={i} className="text-sm">
                <span className="text-gray-400 mr-2">[{i + 1}]</span>
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
          </ul>
        </div>
      )}

      {report && (
        <div className="bg-white border rounded-lg p-6">
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-sm font-semibold text-gray-700">Report</h2>
            {researchId && stage === "done" && (
              <button
                onClick={() => navigate(`/research/${researchId}`)}
                className="text-xs text-blue-600 hover:underline"
              >
                View saved →
              </button>
            )}
          </div>
          <pre className="whitespace-pre-wrap font-sans text-gray-800 leading-relaxed">
            {report}
            {running && <span className="animate-pulse">▍</span>}
          </pre>
        </div>
      )}
    </div>
  );
}

function StatusLine({ stage }: { stage: string }) {
  const label: Record<string, string> = {
    starting: "Starting...",
    generating_query: "Generating search query...",
    searching: "Searching the web...",
    synthesizing: "Writing report...",
    done: "Done",
  };
  return (
    <span>
      {label[stage] || stage}
      {stage !== "done" && <span className="animate-pulse">...</span>}
    </span>
  );
}