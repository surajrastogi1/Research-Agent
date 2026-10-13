import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from "react";

type ToastKind = "success" | "error" | "info";
type Toast = {
  id: number;
  kind: ToastKind;
  message: string;
};

type ToastContextType = {
  show: (message: string, kind?: ToastKind) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
};

const ToastContext = createContext<ToastContextType | null>(null);

let nextId = 1;

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const show = useCallback((message: string, kind: ToastKind = "info") => {
    const id = nextId++;
    setToasts((prev) => [...prev, { id, kind, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const success = useCallback((m: string) => show(m, "success"), [show]);
  const error = useCallback((m: string) => show(m, "error"), [show]);
  const info = useCallback((m: string) => show(m, "info"), [show]);

  return (
    <ToastContext.Provider value={{ show, success, error, info }}>
      {children}
      {/* Render toasts in a fixed stack, bottom-right */}
      <div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`pointer-events-auto px-4 py-3 rounded shadow-lg text-sm font-medium text-white min-w-[240px] max-w-[400px] animate-in fade-in slide-in-from-bottom-2 ${
              t.kind === "success"
                ? "bg-green-600"
                : t.kind === "error"
                  ? "bg-red-600"
                  : "bg-gray-800"
            }`}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside ToastProvider");
  return ctx;
}