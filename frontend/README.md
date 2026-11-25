# SearchLab.AI frontend

React + Vite + Tailwind frontend for SearchLab.AI (Team 17). Matches the demo screens.

## Run it

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # production build in dist/ (deploy to Vercel)
```

## Pages (routes)

| Route | Page |
| --- | --- |
| `/` | Sign in (interactive grid background) |
| `/register` | Create account |
| `/ask` | Ask a question, pick documents to search |
| `/answer?q=...` | Answer with cited sources; streams in; shows "not in your documents" when nothing matches |
| `/documents` | Upload (drag and drop or file picker) and manage documents |
| `/history` | Past questions, searchable, clearable |
| `/evaluation` | Admin: accuracy against the test set |
| `/users` | Admin: roles and access |

## Structure

- `src/components/` – `AppLayout` (sidebar + page header), `AuthShell` (sign-in layout), `GridBackground`, `Logo`, `SourceNote`, `Icons`
- `src/pages/` – one file per route
- `src/data/sample.js` – sample data. **Replace with API calls** to the FastAPI backend; each page has a comment naming the endpoint it needs
- `src/index.css` – shared styles: `.btn`, `.btn2`, `.inp`, `.sheet`, table classes
- `tailwind.config.js` – brand colours (`paper`, `ink`, `graphite`, `rule`, `brand`, `highlight`) and fonts

## Demo behaviour (until the backend is connected)

- Sign in / Create account go straight to `/ask`.
- Questions mentioning "leave" or "intern" get the sample answer; anything else shows the not-found state.
- Uploads, deletes, role changes and feedback update local state only.
