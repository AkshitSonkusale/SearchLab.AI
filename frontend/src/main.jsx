import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, MemoryRouter } from "react-router-dom";

// VITE_ROUTER=memory is used for the hosted demo page (no real URLs there).
const Router = import.meta.env.VITE_ROUTER === "memory" ? MemoryRouter : BrowserRouter;
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <Router>
      <App />
    </Router>
  </React.StrictMode>
);
