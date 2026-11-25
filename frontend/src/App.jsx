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

// Demo wiring: sign-in / register just navigate to /ask.
// Replace with real auth calls once the backend is ready.
export default function App() {
  const navigate = useNavigate();
  const enter = () => navigate("/ask");

  return (
    <Routes>
      <Route path="/" element={<SignIn onSignIn={enter} />} />
      <Route path="/register" element={<Register onRegister={enter} />} />
      <Route element={<AppLayout />}>
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
