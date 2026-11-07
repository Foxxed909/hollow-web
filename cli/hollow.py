#!/usr/bin/env python3
# hollow — termux chat cli
# lang: python3 | target: android/termux

import os, sys, json, signal, argparse, atexit
from pathlib import Path
from datetime import datetime

try:
    import readline
    _RL = Path.home() / '.hollow_readline'
    try: readline.read_history_file(_RL)
    except FileNotFoundError: pass
    atexit.register(readline.write_history_file, _RL)
except ImportError:
    pass

try:
    from openai import OpenAI
except ImportError:
    print('pip install openai'); sys.exit(1)

try:
    import requests
    _GH = True
except ImportError:
    _GH = False

BASE_URL = os.getenv('HOLLOW_BASE',  'https://api.unrestricted.sh/v1')
API_KEY  = os.getenv('HOLLOW_KEY',   '')
MODEL    = os.getenv('HOLLOW_MODEL', 'deepseek-v4.1-flash-uncensored')
GH_TOKEN = os.getenv('GITHUB_TOKEN', '')
SESS_DIR = Path.home() / '.hollow_sessions'
SESS_DIR.mkdir(exist_ok=True)

client = OpenAI(base_url=BASE_URL, api_key=API_KEY)

R='\033[0m'; B='\033[1m'; D='\033[2m'
CY='\033[36m'; GR='\033[32m'; YL='\033[33m'; RD='\033[31m'; MG='\033[35m'

def pr(tag, text, color=CY):
    print(f'{color}{B}{tag}{R} {text}')

class GitHub:
    BASE = 'https://api.github.com'
    def __init__(self, token=''):
        self.h = {'Accept': 'application/vnd.github+json'}
        if token: self.h['Authorization'] = f'Bearer {token}'
    def _get(self, path, params=None):
        if not _GH: return None, 'pip install requests'
        try:
            r = requests.get(f'{self.BASE}{path}', headers=self.h, params=params, timeout=10)
            if r.ok: return r.json(), None
            return None, f'{r.status_code}: {r.text[:200]}'
        except Exception as e: return None, str(e)
    def me(self):
        d, e = self._get('/user'); return e or f"{d['login']}  {d.get('name','')}  repos:{d['public_repos']}"
    def repos(self, page=1):
        d, e = self._get('/user/repos', {'sort':'updated','per_page':12,'page':page})
        return e or '\n'.join(f"  {r['full_name']}  [{r['visibility']}]  *{r['stargazers_count']}" for r in d)
    def issues(self, repo):
        d, e = self._get(f'/repos/{repo}/issues', {'state':'open','per_page':10})
        if e: return e
        items = [i for i in d if 'pull_request' not in i]
        return 'none' if not items else '\n'.join(f"  #{i['number']} {i['title']}" for i in items)
    def prs(self, repo):
        d, e = self._get(f'/repos/{repo}/pulls', {'state':'open','per_page':10})
        return e or ('none' if not d else '\n'.join(f"  #{p['number']} {p['title']}" for p in d))
    def file(self, repo, path):
        import base64
        d, e = self._get(f'/repos/{repo}/contents/{path}')
        if e: return e
        if isinstance(d, list): return '\n'.join(f"  {'d' if i['type']=='dir' else 'f'}  {i['name']}" for i in d)
        content = base64.b64decode(d['content']).decode('utf-8', errors='replace')
        return content[:4000] + ('\n...truncated' if len(content)>4000 else '')
    def search(self, q):
        d, e = self._get('/search/repositories', {'q':q,'per_page':6})
        return e or '\n'.join(f"  {r['full_name']}  *{r['stargazers_count']}  {(r['description'] or '')[:60]}" for r in d['items'])
    def branches(self, repo):
        d, e = self._get(f'/repos/{repo}/branches')
        return e or '\n'.join(f'  {b["name"]}' for b in d)
    def commits(self, repo, branch=''):
        p = {'per_page': 8}
        if branch: p['sha'] = branch
        d, e = self._get(f'/repos/{repo}/commits', p)
        return e or '\n'.join(f"  {c['sha'][:7]}  {c['commit']['message'].splitlines()[0][:60]}" for c in d)

gh = GitHub(GH_TOKEN)

class Session:
    def __init__(self, model=MODEL, system=''):
        self.model=model; self.system=system; self.msgs=[]
        self.name=datetime.now().strftime('%Y%m%d_%H%M%S')
    def add(self, role, content): self.msgs.append({'role':role,'content':content})
    def build(self):
        m=[]
        if self.system: m.append({'role':'system','content':self.system})
        return m+self.msgs
    def save(self):
        p=SESS_DIR/f'{self.name}.json'
        p.write_text(json.dumps({'model':self.model,'system':self.system,'msgs':self.msgs},indent=2))
        return p
    def clear(self): self.msgs.clear()
    @staticmethod
    def load(name):
        p=SESS_DIR/(name if name.endswith('.json') else f'{name}.json')
        d=json.loads(p.read_text())
        s=Session(d['model'],d.get('system',''))
        s.msgs=d['msgs']; s.name=name.replace('.json','')
        return s
    @staticmethod
    def list_saved(): return sorted(SESS_DIR.glob('*.json'),key=lambda x:x.stat().st_mtime,reverse=True)

def chat(session, user_msg, stream=True):
    session.add('user', user_msg)
    try:
        resp = client.chat.completions.create(model=session.model,messages=session.build(),stream=stream)
        if stream:
            print(f'\n{GR}{B}*{R} ',end='',flush=True)
            full=''
            for chunk in resp:
                delta=chunk.choices[0].delta.content or ''
                print(delta,end='',flush=True); full+=delta
            print(); session.add('assistant',full); return full
        else:
            text=resp.choices[0].message.content
            session.add('assistant',text); print(f'\n{GR}{B}*{R} {text}'); return text
    except Exception as ex:
        pr('ERR',str(ex),RD); session.msgs.pop(); return ''

HELP=f"""
{B}{CY}chat{R}
  /clear   /model [name]   /models   /system [text]   /stream   /token
{B}{CY}sessions{R}
  /save   /sessions   /load [name]
{B}{CY}github{R}
  /gh me|repos|issues|prs|commits|branches|file|search|inject
  /gh file   <owner/repo> <path>
  /gh inject <owner/repo> <path>  — push file into context
{B}{CY}exit{R}
  /exit  Ctrl-C
"""

def handle_cmd(line, session, sf):
    p=line.strip().split(None,4); cmd=p[0].lower()
    if cmd in('/help','/?'): print(HELP); return True
    if cmd in('/exit','/quit','/q'): raise KeyboardInterrupt
    if cmd=='/clear': session.clear(); pr('OK','history cleared',YL); return True
    if cmd=='/model':
        if len(p)>1: session.model=p[1]; pr('model ->',session.model,YL)
        else: pr('model',session.model,YL)
        return True
    if cmd=='/models':
        try:
            ms=client.models.list(); print('\n'.join(f'  {m.id}' for m in ms.data))
        except Exception as e: pr('ERR',str(e),RD)
        return True
    if cmd=='/system':
        session.system=' '.join(p[1:]) if len(p)>1 else ''
        pr('system','set' if session.system else 'cleared',YL); return True
    if cmd=='/save': pr('saved',str(session.save()),YL); return True
    if cmd=='/sessions':
        fs=Session.list_saved()
        if not fs: pr('none','',YL)
        for f in fs[:15]: print(f'  {f.stem}')
        return True
    if cmd=='/load':
        if len(p)<2:
            for f in Session.list_saved()[:10]: print(f'  {f.stem}')
            return True
        try:
            ld=Session.load(p[1]); session.model=ld.model; session.system=ld.system
            session.msgs=ld.msgs; session.name=ld.name
            pr('loaded',f'{p[1]} ({len(session.msgs)//2} turns)',YL)
        except Exception as e: pr('ERR',str(e),RD)
        return True
    if cmd=='/stream': sf[0]=not sf[0]; pr('stream','on' if sf[0] else 'off',YL); return True
    if cmd=='/token':
        n=sum(len(m['content'].split()) for m in session.msgs)*4//3
        pr('~tokens',str(n),YL); return True
    if cmd=='/gh':
        if len(p)<2: pr('usage','/gh me|repos|issues|prs|commits|branches|file|search|inject',YL); return True
        raw=line.strip().split(None,3); sub=p[1].lower()
        a1=raw[2] if len(raw)>2 else ''
        a2=raw[3] if len(raw)>3 else ''
        if sub=='me': pr('gh',gh.me(),GR)
        elif sub=='repos': print(gh.repos())
        elif sub=='issues': print(gh.issues(a1) if a1 else pr('need','owner/repo',YL))
        elif sub=='prs': print(gh.prs(a1) if a1 else pr('need','owner/repo',YL))
        elif sub=='branches': print(gh.branches(a1) if a1 else pr('need','owner/repo',YL))
        elif sub=='commits': print(gh.commits(a1,a2) if a1 else pr('need','owner/repo',YL))
        elif sub=='file':
            if a1 and a2: print(gh.file(a1,a2))
            else: pr('usage','/gh file owner/repo path',YL)
        elif sub=='search':
            q=' '.join(raw[2:]) if len(raw)>2 else ''
            print(gh.search(q) if q else pr('need','query',YL))
        elif sub=='inject':
            if a1 and a2:
                content=gh.file(a1,a2)
                session.add('user',f'[injected: {a1}/{a2}]\n```\n{content}\n```')
                pr('injected',f'{a1}/{a2} -> context',GR)
            else: pr('usage','/gh inject owner/repo path',YL)
        else: pr('?',f'unknown: /gh {sub}',YL)
        return True
    return False

def main():
    ap=argparse.ArgumentParser(prog='hollow',add_help=False)
    ap.add_argument('--model','-m',default=MODEL)
    ap.add_argument('--system','-s',default='')
    ap.add_argument('--load','-l',default='')
    ap.add_argument('--no-stream',action='store_true')
    args=ap.parse_args()
    session=Session(model=args.model,system=args.system)
    if args.load:
        try: session=Session.load(args.load)
        except Exception as e: pr('ERR',str(e),RD)
    sf=[not args.no_stream]
    print(f'\n{MG}{B}hollow{R}  {D}{session.model}{R}  {D}/help{R}\n')
    signal.signal(signal.SIGINT,lambda s,f:(_ for _ in ()).throw(KeyboardInterrupt()))
    while True:
        try: line=input(f'{CY}>{R} ').strip()
        except (EOFError,KeyboardInterrupt): print('\nexit'); break
        if not line: continue
        if line.startswith('/'):
            try: handle_cmd(line,session,sf)
            except KeyboardInterrupt: print('\nexit'); break
            continue
        chat(session,line,stream=sf[0])

if __name__=='__main__':
    main()
