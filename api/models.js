import OpenAI from 'openai';

export default async function handler(req) {
  const cors = { 'Access-Control-Allow-Origin': '*', 'Content-Type': 'application/json' };
  if (req.method === 'OPTIONS') return new Response('', { headers: cors });

  let apiKey, baseUrl;
  if (req.method === 'POST') {
    try { const b = await req.json(); apiKey = b.apiKey; baseUrl = b.baseUrl; } catch {}
  } else {
    const url = new URL(req.url);
    apiKey  = url.searchParams.get('apiKey')  || '';
    baseUrl = url.searchParams.get('baseUrl') || '';
  }

  try {
    const client = new OpenAI({
      baseURL: baseUrl || process.env.HOLLOW_BASE || 'https://api.unrestricted.sh/v1',
      apiKey:  apiKey  || process.env.HOLLOW_KEY  || '',
    });
    const list = await client.models.list();
    return Response.json({ models: list.data.map(m => m.id) }, { headers: cors });
  } catch (e) {
    return Response.json({ error: e.message }, { status: 500, headers: cors });
  }
}
