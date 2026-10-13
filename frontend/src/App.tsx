import { Routes, Route, Navigate } from "react-router-dom";
import { useAuth } from "./context/AuthContext";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import NewResearch from "./pages/NewResearch";
import ResearchDetail from "./pages/ResearchDetail";
import Navbar from "./components/Navbar";

function App() {
  const { token, loading } = useAuth();

  // While we're figuring out if the stored token is valid, show a loader.
  // This prevents flickering between login and dashboard on refresh.
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <p className="text-gray-500">Loading...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {token && <Navbar />}
      <Routes>
        <Route
          path="/login"
          element={token ? <Navigate to="/" replace /> : <Login />}
        />
        <Route
          path="/"
          element={token ? <Dashboard /> : <Navigate to="/login" replace />}
        />
        <Route
          path="/new"
          element={token ? <NewResearch /> : <Navigate to="/login" replace />}
        />
        <Route
          path="/research/:id"
          element={token ? <ResearchDetail /> : <Navigate to="/login" replace />}
        />
      </Routes>
    </div>
  );
}

export default App;