import { useState, useEffect } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";
import AppLayout from "./components/AppLayout";
import SignIn from "./pages/SignIn";
import Register from "./pages/Register";
import Ask from "./pages/Ask";
import Answer from "./pages/Answer";
import Documents from "./pages/Documents";
import History from "./pages/History";
import Evaluation from "./pages/Evaluation";
import Users from "./pages/Users";
import { api, getAuthToken, getUser } from "./api";

function ProtectedRoute({ children }) {
  const token = getAuthToken();
  if (!token) {
    return <Navigate to="/" replace />;
  }
  return children;
}

export default function App() {
  const navigate = useNavigate();
  const [error, setError] = useState("");

  const handleSignIn = async ({ email, password }) => {
    try {
      setError("");
      await api.login(email, password);
      navigate("/ask");
    } catch (err) {
      setError(err.message || "Invalid credentials");
    }
  };

  const handleRegister = async ({ name, email, password }) => {
    try {
      setError("");
      await api.register(name, email, password);
      navigate("/ask");
    } catch (err) {
      setError(err.message || "Registration failed");
    }
  };

  return (
    <Routes>
      <Route path="/" element={<SignIn onSignIn={handleSignIn} error={error} />} />
      <Route path="/register" element={<Register onRegister={handleRegister} error={error} />} />
      <Route element={<ProtectedRoute><AppLayout /></ProtectedRoute>}>
        <Route path="/ask" element={<Ask />} />
        <Route path="/answer" element={<Answer />} />
        <Route path="/documents" element={<Documents />} />
        <Route path="/history" element={<History />} />
        <Route path="/evaluation" element={<Evaluation />} />
        <Route path="/users" element={<Users />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
