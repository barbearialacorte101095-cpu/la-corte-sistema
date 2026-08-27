// Wrapper simples sobre fetch, usado por booking.js e admin.js.
// Em produção, a API vive no mesmo domínio (rota /api/*), então
// não é preciso configurar uma base URL separada.

const API_BASE = "/api";

async function apiRequest(path, { method = "GET", body } = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: body ? { "Content-Type": "application/json" } : undefined,
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!res.ok) {
    let detalhe = "Erro inesperado";
    try {
      const erro = await res.json();
      detalhe = erro.detail || detalhe;
    } catch (_) {
      /* corpo não é JSON */
    }
    throw new Error(detalhe);
  }

  if (res.status === 204) return null;
  return res.json();
}

const api = {
  get: (path) => apiRequest(path),
  post: (path, body) => apiRequest(path, { method: "POST", body }),
  patch: (path, body) => apiRequest(path, { method: "PATCH", body }),
};
