import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import NewResearch from "./pages/NewResearch";
import ResearchDetail from "./pages/ResearchDetail";
import Navbar from "./components/Navbar";

function App() {
  const location = useLocation();
  const token = localStorage.getItem("token");
  const isLoginPage = location.pathname === "/login";

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Only show navbar when logged in AND not on login page */}
      {token && !isLoginPage && <Navbar />}

      <Routes>
        {/* If already logged in, /login redirects to dashboard */}
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