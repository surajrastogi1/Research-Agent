import { Link, useNavigate } from "react-router-dom";
import { clearToken } from "../lib/api";

export default function Navbar() {
  const navigate = useNavigate();

  function handleLogout() {
    clearToken();
    navigate("/login");
  }

  return (
    <nav className="bg-white border-b">
      <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link to="/" className="text-lg font-semibold">
          Research Agent
        </Link>
        <div className="flex items-center gap-4">
          <Link
            to="/new"
            className="text-sm font-medium text-blue-600 hover:text-blue-800"
          >
            + New Research
          </Link>
          <button
            onClick={handleLogout}
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            Logout
          </button>
        </div>
      </div>
    </nav>
  );
}