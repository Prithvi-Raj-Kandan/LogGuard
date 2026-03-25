
  # Log Analyzer Frontend

  This is a code bundle for Log Analyzer Frontend. The original project is available at https://www.figma.com/design/l1ovnN9KUdc7AN1DBRywIl/Log-Analyzer-Frontend.

  ## Running the code

  1. Create `.env` from `.env.example` and set backend URL:

  `VITE_API_BASE_URL=http://localhost:8000`

  Run `npm i` to install the dependencies.

  Run `npm run dev` to start the development server.

  ## Backend Endpoint Used

  The frontend is connected to:

  - `POST /analyze/upload` for multipart file uploads

  Ensure backend is running before uploading files.
  