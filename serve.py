"""Single-port host: a landing hub that mounts both apps under one port.

    uvicorn serve:app --port 8000

- http://localhost:8000/            -> hub with two cards
- http://localhost:8000/crosscheck/ -> Crosscheck (contradiction memory)
- http://localhost:8000/argus/      -> Argus (spend/contract leakage auditor)

Both sub-apps still run standalone (`crosscheck.api:app`, `argus.api:app`) — their
panels use relative fetches, so they work at the root or under a mount prefix.
One process = one shared local model load (kind to 8GB laptops).
"""
from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from crosscheck.api import app as crosscheck_app
from argus.api import app as argus_app

app = FastAPI(title="Crosscheck + Argus")

_HUB = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Crosscheck + Argus</title>
<style>
 :root{--paper:#0b0b10;--panel:#14141c;--line:#26262f;--line2:#33333f;--ink:#eef0f5;
   --muted:#9a9aad;--faint:#6c6c7c;--brand:#8b5cf6;--brand2:#a78bfa;--risk:#f2565b;
   --font:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
 *{box-sizing:border-box}
 body{margin:0;min-height:100vh;background:var(--paper);color:var(--ink);font-family:var(--font);
   display:flex;flex-direction:column;align-items:center;justify-content:center;padding:32px;gap:8px}
 .kick{color:var(--brand2);font-size:12px;font-weight:600;letter-spacing:.14em;text-transform:uppercase}
 h1{font-size:clamp(26px,5vw,38px);margin:6px 0 0;letter-spacing:-.02em;font-weight:700}
 .tag{color:var(--muted);font-size:15px;margin:8px 0 28px;text-align:center;max-width:52ch}
 .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,340px));gap:20px;width:100%;
   max-width:720px;justify-content:center}
 a.card{text-decoration:none;color:inherit;background:var(--panel);border:1px solid var(--line);
   border-radius:16px;padding:26px;transition:border-color .15s,transform .15s;display:block}
 a.card:hover{border-color:var(--brand);transform:translateY(-3px)}
 .card .ico{width:26px;height:26px;border-radius:50%;border:3px solid var(--accent);position:relative;margin-bottom:14px}
 .card .ico::after{content:"";position:absolute;inset:5px;border-radius:50%;background:var(--accent)}
 .cc{--accent:var(--brand)}.ar{--accent:var(--risk)}
 .card h2{margin:0 0 8px;font-size:20px;letter-spacing:-.01em}
 .card p{margin:0;font-size:13.5px;color:var(--muted);line-height:1.55}
 .go{margin-top:16px;font-size:13px;font-weight:600;color:var(--brand2)}
 .foot{color:var(--faint);font-size:12px;margin-top:28px}
</style></head><body>
 <div class="kick">Built on cognee</div>
 <h1>Crosscheck &amp; Argus</h1>
 <div class="tag">Two tools on one idea: catch when sources disagree — then act on it.</div>
 <div class="cards">
   <a class="card cc" href="/crosscheck/">
     <div class="ico"></div>
     <h2>Crosscheck</h2>
     <p>Persistent research memory that flags when your sources contradict each other — with who said what, and when.</p>
     <div class="go">Open Crosscheck →</div>
   </a>
   <a class="card ar" href="/argus/">
     <div class="ico"></div>
     <h2>Argus</h2>
     <p>Spend &amp; contract leakage auditor. Finds where invoices, POs and contracts disagree — and puts a dollar figure on each.</p>
     <div class="go">Open Argus →</div>
   </a>
 </div>
 <div class="foot">Same contradiction engine, two problems.</div>
</body></html>"""


@app.get("/", response_class=HTMLResponse)
def hub():
    return _HUB


app.mount("/crosscheck", crosscheck_app)
app.mount("/argus", argus_app)
