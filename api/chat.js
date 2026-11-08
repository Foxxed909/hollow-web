import OpenAI from 'openai';

export const config = { runtime: 'edge' };

export default async function handler(req) {
  if (req.method !== 'POST') return new Response('method not allowed', { status: 405 });

  let body;
  try { body = await req.json(); } catch { return new Response('bad json', { status: 400 }); }

  const {
    messages = [],
    model,
    system,
    // client-supplied keys override env (for in-app settings)
    apiKey,
    baseUrl,
  } = body;

  const client = new OpenAI({
    baseURL: baseUrl  || process.env.HOLLOW_BASE  || 'https://api.unrestricted.sh/v1',
    apiKey:  apiKey   || process.env.HOLLOW_KEY   || '',
  });

  const msgs = system
    ? [{ role: 'system', content: system }, ...messages]
    : messages;

  const enc = new TextEncoder();

  const readable = new ReadableStream({
    async start(ctrl) {
      try {
        const stream = await client.chat.completions.create({
          model: model || process.env.HOLLOW_MODEL || 'deepseek-v4.1-flash-uncensored',
          messages: msgs,
          stream: true,
        });
        for await (const chunk of stream) {
          const delta = chunk.choices[0]?.delta?.content || '';
          if (delta) ctrl.enqueue(enc.encode(`data: ${JSON.stringify({ delta })}\n\n`));
        }
      } catch (e) {
        ctrl.enqueue(enc.encode(`data: ${JSON.stringify({ error: e.message })}\n\n`));
      }
      ctrl.enqueue(enc.encode('data: [DONE]\n\n'));
      ctrl.close();
    }
  });

  return new Response(readable, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Access-Control-Allow-Origin': '*',
    }
  });
}
