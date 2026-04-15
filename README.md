# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

## PostgreSQL Backend

The app now uses PostgreSQL for auth and blog content instead of the old JSON file store.

- Users, blog posts, comments, ratings, and comment likes are backed by PostgreSQL tables.
- The backend seeds demo blog posts and sample interaction rows on first run so the feed is not empty.
- Frontend auth still stores only the current session user in localStorage.

### Run With Docker Compose

From the project root:

```bash
docker compose up --build
```

This starts:

- PostgreSQL on `localhost:5432`
- FastAPI backend on `http://localhost:5000`
- Frontend preview server on `http://localhost:4173`

### Run Backend Locally

Set `DATABASE_URL` to a PostgreSQL instance, then run the backend from the `backend` folder:

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Environment variables:

- `DATABASE_URL` - PostgreSQL connection string
- `HOST` - backend bind host, defaults to `127.0.0.1`
- `PORT` - backend port, defaults to `5000`
- `SEED_DEMO_DATA` - set to `false` to skip seeding demo content

### Run Frontend Locally

In a separate terminal from project root:

```bash
npm install
npm run dev
```

The Vite dev server still proxies `/api` requests to the backend on `127.0.0.1:5000`.

### Notes

- Passwords are hashed server-side before storing them in PostgreSQL.
- Existing JSON data is not migrated.
- No 2FA or social login is implemented.
