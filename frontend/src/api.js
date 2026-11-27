// SearchLab.AI API Client
const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const getAuthToken = () => localStorage.getItem("searchlab_token");
export const setAuthToken = (token) => localStorage.setItem("searchlab_token", token);
export const clearAuthToken = () => localStorage.removeItem("searchlab_token");

export const getUser = () => {
  const u = localStorage.getItem("searchlab_user");
  return u ? JSON.parse(u) : null;
};
export const setUser = (user) => localStorage.setItem("searchlab_user", JSON.stringify(user));
export const clearUser = () => localStorage.removeItem("searchlab_user");

async function request(endpoint, options = {}) {
  const token = getAuthToken();
  const headers = {
    ...options.headers,
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  if (!(options.body instanceof FormData) && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }

  const res = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
  });

  if (res.status === 401) {
    clearAuthToken();
    clearUser();
    if (window.location.pathname !== "/" && window.location.pathname !== "/register") {
      window.location.href = "/";
    }
  }

  if (res.status === 204) return null;

  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const errorMsg = data.message || data.detail?.message || data.detail || "Request failed";
    throw new Error(errorMsg);
  }
  return data;
}

export const api = {
  // Auth
  async register(name, email, password) {
    const data = await request("/auth/register", {
      method: "POST",
      body: JSON.stringify({ name, email, password }),
    });
    if (data.token) {
      setAuthToken(data.token);
      setUser(data.user);
    }
    return data;
  },

  async login(email, password) {
    const data = await request("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    if (data.token) {
      setAuthToken(data.token);
      setUser(data.user);
    }
    return data;
  },

  async getMe() {
    return request("/auth/me");
  },

  async logout() {
    try {
      await request("/auth/logout", { method: "POST" });
    } finally {
      clearAuthToken();
      clearUser();
    }
  },

  // Documents
  async getDocuments() {
    return request("/documents");
  },

  async uploadDocument(file) {
    const formData = new FormData();
    formData.append("file", file);
    return request("/documents", {
      method: "POST",
      body: formData,
    });
  },

  async createTextDocument(name, text) {
    return request("/documents/text", {
      method: "POST",
      body: JSON.stringify({ name, text }),
    });
  },

  async deleteDocument(id) {
    return request(`/documents/${id}`, { method: "DELETE" });
  },

  async getDownloadUrl(id) {
    return request(`/documents/${id}/download`);
  },

  // Query & RAG
  async askStream(question, documentIds = null, onSources, onToken, onDone, onError) {
    const token = getAuthToken();
    try {
      const response = await fetch(`${API_BASE}/ask`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": token ? `Bearer ${token}` : "",
        },
        body: JSON.stringify({
          question,
          document_ids: documentIds && documentIds.length ? documentIds : null,
        }),
      });

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.message || "Query failed");
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop(); // keep partial

        for (const block of lines) {
          if (!block.trim()) continue;
          let event = "message";
          let data = "";

          for (const line of block.split("\n")) {
            if (line.startsWith("event: ")) {
              event = line.replace("event: ", "").trim();
            } else if (line.startsWith("data: ")) {
              data = line.replace("data: ", "").trim();
            }
          }

          if (event === "sources") {
            try { onSources?.(JSON.parse(data)); } catch (e) {}
          } else if (event === "token") {
            try { onToken?.(JSON.parse(data)); } catch (e) { onToken?.(data); }
          } else if (event === "done") {
            try { onDone?.(JSON.parse(data)); } catch (e) { onDone?.({}); }
          }
        }
      }
    } catch (err) {
      onError?.(err);
    }
  },

  // History & Feedback
  async getHistory(query = "") {
    const qParam = query ? `?q=${encodeURIComponent(query)}` : "";
    return request(`/history${qParam}`);
  },

  async clearHistory() {
    return request("/history", { method: "DELETE" });
  },

  async submitFeedback(questionId, helpful) {
    return request("/feedback", {
      method: "POST",
      body: JSON.stringify({ question_id: questionId, helpful }),
    });
  },

  // Admin
  async getUsers() {
    return request("/admin/users");
  },

  async updateUser(id, patch) {
    return request(`/admin/users/${id}`, {
      method: "PATCH",
      body: JSON.stringify(patch),
    });
  },

  async inviteUser(name, email, role = "user") {
    return request("/admin/users/invite", {
      method: "POST",
      body: JSON.stringify({ name, email, role }),
    });
  },

  async runEvaluation() {
    return request("/admin/evaluation/run", { method: "POST" });
  },

  async getCoverageGaps() {
    return request("/admin/gaps");
  },
};
