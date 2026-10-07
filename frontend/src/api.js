async function req(path, opts = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}

export const api = {
  createSession: (motion, persona, difficulty, lang) =>
    req('/api/sessions', {
      method: 'POST',
      body: JSON.stringify({ motion, persona, difficulty, lang }),
    }),
  getSession: (id) => req(`/api/sessions/${id}`),
  postMove: (id, text) =>
    req(`/api/sessions/${id}/moves`, {
      method: 'POST',
      body: JSON.stringify({ text }),
    }),
  endDebate: (id) => req(`/api/sessions/${id}/end`, { method: 'POST' }),
  flipSides: (id) => req(`/api/sessions/${id}/flip-sides`, { method: 'POST' }),
  getProgress: () => req('/api/progress'),
};
