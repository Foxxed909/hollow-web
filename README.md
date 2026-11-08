# hollow-web

Web chat + Termux CLI for unrestricted.sh, Nvidia NIM, or any OpenAI-compatible API. Settings (API keys, provider, model) are configured inside the app — nothing hardcoded.

## deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/Foxxed909/hollow-web)

After deploy, **no env vars required** — set everything in the in-app settings panel (⚙ icon). Or optionally set env vars as fallbacks:

| var | default |
|---|---|
| `HOLLOW_BASE` | `https://api.unrestricted.sh/v1` |
| `HOLLOW_KEY` | — |
| `HOLLOW_MODEL` | `deepseek-v4.1-flash-uncensored` |
| `GITHUB_TOKEN` | — |

## local dev

```bash
npm i -g vercel
vercel dev    # localhost:3000
# set keys in-app via ⚙ settings
```

## providers

| provider | base url | notes |
|---|---|---|
| unrestricted.sh | `https://api.unrestricted.sh/v1` | uncensored models |
| nvidia nim | `https://integrate.api.nvidia.com/v1` | free tier at build.nvidia.com |
| custom | any OpenAI-compatible URL | bring your own |

## termux CLI

```bash
pkg install python
pip install openai requests
export HOLLOW_KEY=your_key
export HOLLOW_MODEL=deepseek-v4.1-flash-uncensored
python cli/hollow.py
```

## slash commands

```
/help
/model <name>     switch model
/models           list from API
/system <text>    set system prompt
/clear            wipe history
/stream           toggle streaming
/save / /sessions
/settings         open settings panel
/gh me|repos|issues|prs|commits|branches|file|search|inject
```
