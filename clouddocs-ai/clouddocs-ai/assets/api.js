// Set this to your deployed backend URL once it's live on Render.
// While developing locally, point it at your local FastAPI server.
const API_BASE_URL = window.API_BASE_URL || "http://localhost:8000";

async function apiUpload(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE_URL}/documents`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed." }));
    throw new Error(err.detail || "Upload failed.");
  }
  return res.json();
}

async function apiGetDocument(id) {
  const res = await fetch(`${API_BASE_URL}/documents/${id}`);
  if (!res.ok) throw new Error("Could not fetch document status.");
  return res.json();
}

async function apiListDocuments() {
  const res = await fetch(`${API_BASE_URL}/documents`);
  if (!res.ok) throw new Error("Could not fetch documents.");
  return res.json();
}

async function apiQuery(documentId, question) {
  const res = await fetch(`${API_BASE_URL}/chat/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: documentId, question }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Query failed." }));
    throw new Error(err.detail || "Query failed.");
  }
  return res.json();
}
