# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.

## Authentication Backend

This project uses a simple FastAPI backend for registration and login:

- Register endpoint saves new accounts to a persistent JSON file at `data/accounts.json`.
- Login endpoint reads `data/accounts.json` and validates credentials against saved accounts.
- Frontend keeps only the current session user in localStorage.

### Run Backend

From project root:

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
python app.py
```

The backend runs on `http://127.0.0.1:5000`.

### Run Frontend

In a separate terminal from project root:

```bash
npm install
npm run dev
```

Vite proxies `/api` requests to the backend during development.

### Notes

- Passwords are hashed server-side before writing to `data/accounts.json`.
- No 2FA or social login is implemented.
