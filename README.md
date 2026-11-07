# hollow-web

Web chat interface + Termux CLI for unrestricted.sh (or any OpenAI-compatible API). One-click Vercel deploy.

## deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Foxxed909/hollow-web)

Set these environment variables in your Vercel project settings:

| var | value |
|---|---|
| `HOLLOW_BASE` | `https://api.unrestricted.sh/v1` |
| `HOLLOW_KEY` | your API key |
| `HOLLOW_MODEL` | `deepseek-v4.1-flash-uncensored` |
| `GITHUB_TOKEN` | your GH PAT (for private repo access) |

## local dev

```bash
npm i -g vercel
cp .env.example .env.local   # fill in your keys
vercel dev                    # runs on localhost:3000
```

## termux CLI

```bash
pkg install python
pip install openai requests
export HOLLOW_KEY=your_key
export HOLLOW_MODEL=deepseek-v4.1-flash-uncensored
python cli/hollow.py
```

## commands

```
/help          full command list
/model <name>  switch model mid-session
/models        list available from API
/system <text> set system prompt
/clear         wipe history
/stream        toggle streaming
/save          save session
/load <name>   restore session
/gh me         github user info
/gh repos      your repos
/gh issues <owner/repo>
/gh prs    <owner/repo>
/gh inject <owner/repo> <path>   push file into context
```
