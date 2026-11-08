export default async function handler(req) {
  const cors = {
    'Access-Control-Allow-Origin': '*',
    'Content-Type': 'application/json',
  };
  if (req.method === 'OPTIONS') return new Response('', { headers: cors });
  if (req.method !== 'POST') return new Response('method not allowed', { status: 405 });

  let body;
  try { body = await req.json(); } catch { return new Response('bad json', { status: 400 }); }

  const { path, method = 'GET', payload, ghToken } = body;
  if (!path) return Response.json({ error: 'path required' }, { status: 400 });

  const token = ghToken || process.env.GITHUB_TOKEN || '';
  const headers = { 'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json' };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const r = await fetch(`https://api.github.com${path}`, {
    method,
    headers,
    body: payload ? JSON.stringify(payload) : undefined,
  });

  const data = await r.json().catch(() => ({}));
  return Response.json(data, { status: r.status, headers: cors });
}
