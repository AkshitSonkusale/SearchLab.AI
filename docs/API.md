# SearchLab.AI – API contract (frontend ↔ backend)

This is what the frontend expects from the FastAPI backend. Agree on it before building, so frontend and backend can work in parallel. Anything marked **(proposed)** is a suggestion from the frontend side and can change after discussion.

- Base URL: set in the frontend as `VITE_API_URL` (for example `https://searchlab-api.onrender.com`).
- All requests and responses are JSON unless stated otherwise.
- Authenticated requests send `Authorization: Bearer <token>`.
- Times are ISO 8601 strings in UTC, for example `"2026-11-25T08:30:00Z"`.
- The backend must allow the Vercel frontend URL in its CORS settings.

## Errors

Every error uses the same shape, so the frontend can show `message` directly to the user:

```json
{ "error": "invalid_credentials", "message": "Email or password is incorrect." }
```

| Status | When |
| --- | --- |
| 400 | Invalid input (missing field, bad email, file too large, wrong type) |
| 401 | Missing or expired token |
| 403 | Logged in but not allowed (for example a User calling an Admin endpoint, or a deactivated account) |
| 404 | Item doesn't exist or belongs to someone else |
| 422 | FastAPI validation error |
| 500 | Server error |

---

## 1. Auth

### `POST /auth/register`
```json
// request
{ "name": "Akshit Sonkusale", "email": "akshit@example.com", "password": "at-least-8-chars" }
// 201 response
{ "token": "<jwt>", "user": { "id": "u_123", "name": "Akshit Sonkusale", "email": "akshit@example.com", "role": "user" } }
```
Errors: `email_taken`, `weak_password` (fewer than 8 characters).

### `POST /auth/login`
```json
// request
{ "email": "akshit@example.com", "password": "..." }
// 200 response: same shape as register
```
Errors: `invalid_credentials` (401), `account_deactivated` (403).

### `GET /auth/me`
Returns the current `user` object. The frontend calls this on page load to restore a session.

`role` is `"user"` or `"admin"`.

---

## 2. Documents

### `GET /documents`
```json
[
  {
    "id": "d_1",
    "name": "Intern leave policy.pdf",
    "type": "PDF",
    "size_bytes": 2400000,
    "uploaded_at": "2026-11-20T10:00:00Z",
    "status": "ready",
    "passages": 3,
    "error": null
  }
]
```
`status` is one of `"processing"`, `"ready"`, `"failed"`. When `failed`, `error` holds a user-readable reason, for example `"No readable text found. Upload a text-based PDF, not a scan."`.

### `POST /documents` (multipart/form-data)
Field `file`. Accept PDF, DOCX and TXT only, 10 MB maximum. Return `202` with the new document in `"processing"` status, then process it in the background. The frontend polls `GET /documents` (every 2–3 s) until the status changes.

Errors: `unsupported_type`, `file_too_large`.

### `POST /documents/text` (proposed)
"Paste text as a document".
```json
{ "name": "Meeting notes", "text": "..." }
```

### `DELETE /documents/{id}`
`204`. Must also delete the document's chunks and embeddings, so it stops appearing in answers.

---

## 3. Ask (the RAG pipeline)

### `POST /ask` → Server-Sent Events stream
```json
// request
{ "question": "How many days in advance should I request leave?", "document_ids": null }
```
`document_ids: null` means search all of the user's documents. A list restricts the search ("Search in" filter).

The response is `text/event-stream` with these events, in order:

```text
event: sources
data: {"sources":[{"n":1,"document_id":"d_2","document":"Employee handbook.txt","passage":"All leave requests must be submitted ... five working days ...","passage_index":4,"passage_count":5,"relevance":0.52,"evidence":"All leave requests must be submitted ... five working days in advance ..."}]}

event: token
data: {"text":"All leave requests must be "}

event: token
data: {"text":"submitted at least five working days in advance [1]."}

event: done
data: {"question_id":"q_789","found":true,"conflicts":[{"a":1,"b":2}],"search":{"terms":["day","advance","request","leave"],"passages_searched":11,"documents_searched":3,"best_score":0.52,"threshold":0.2}}
```

- `relevance` is the similarity score from 0 to 1. `evidence` is the exact sentence in the passage that supports the answer; the frontend highlights it.
- Citations in the answer text use `[n]`, matching `sources[].n`.
- **Not found:** if nothing passes the relevance threshold, send no `token` events, and send `done` with `"found": false` and the closest passages in `sources`. The frontend shows "This isn't in your documents". The LLM must not be called in this case.
- `conflicts` (proposed): pairs of source numbers that give different answers to the same question. The frontend shows a "Sources disagree" box. A simple first version: two passages from different documents that share most of their words but contain different numbers.
- `search`: shown in the "How I searched" panel.
- The frontend's "Stop generating" button closes the stream.

A non-streaming fallback, `POST /ask?stream=false`, returning `{ answer, sources, found, conflicts, search, question_id }`, is useful for testing.

---

## 4. History and feedback

### `GET /history?q=<optional search text>`
```json
[ { "question_id": "q_789", "question": "How many days in advance should I request leave?", "asked_at": "2026-11-25T08:30:00Z", "found": true, "source_count": 2 } ]
```
Only the current user's questions, newest first.

### `GET /history/{question_id}`
Returns the stored answer, `{ answer, sources, found, conflicts, search }`, so the frontend can reopen a past question without asking again.

### `DELETE /history`
Clears the current user's history. `204`.

### `POST /feedback`
```json
{ "question_id": "q_789", "helpful": true }
```
`204`. Sending it again for the same question replaces the earlier rating.

---

## 5. Admin (role `admin` only; otherwise `403`)

### `POST /admin/evaluation/run`
Runs the fixed test set. Can take a while, so return `202 { "run_id": "r_3" }` and let the frontend poll:

### `GET /admin/evaluation/runs/{run_id}`
```json
{
  "status": "done",
  "metrics": { "retrieval_top5": 0.84, "answer_correct_doc": 0.80, "not_found_accuracy": 0.92, "avg_seconds": 2.9 },
  "feedback": { "helpful": 46, "not_helpful": 7 },
  "results": [ { "question": "trainee absence rules", "expected": "Intern leave policy.txt", "top_source": "Intern leave policy.txt", "pass": true } ]
}
```
`expected` is `null` for questions that should get "not found".

### `GET /admin/evaluation/runs`
Past runs: `[{ "run_id", "finished_at", "retrieval_top5", "passed", "total" }]`.

### `GET /admin/gaps` (proposed)
```json
{
  "unanswered": [ { "example_question": "What is the CEO salary", "topic_terms": ["ceo", "salary"], "count": 12, "last_asked_at": "..." } ],
  "conflicts": [ { "documents": ["Employee handbook.txt", "Intern leave policy.txt"], "a": "...five working days...", "b": "...three working days...", "count": 3, "last_seen_at": "...", "example_question": "..." } ]
}
```
Unanswered questions are the `found: false` questions from all users, grouped by their key terms. Conflicts are the ones recorded by `/ask`.

### Users
| Method and path | Body | Result |
| --- | --- | --- |
| `GET /admin/users` | | `[{ id, name, email, role, active, last_active_at }]` |
| `POST /admin/users/invite` | `{ name, email, role }` | `201`, the new user. Error `already_exists`. |
| `PATCH /admin/users/{id}` | `{ role?, active? }` | `200`, the updated user. Error `cannot_change_self` if an admin changes their own role or access. |

---

## 6. Health

### `GET /health`
`200 { "status": "ok" }`. Used by the uptime ping that keeps the free Render instance awake, and by the frontend to show a "waking up the server" message on the first request.
