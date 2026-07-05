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

_HUB = """<!doctype html><html><head><meta charset="utf-8"><title>Crosscheck + Argus</title>
<style>
 body{font-family:-apple-system,Helvetica,Arial,sans-serif;margin:0;min-height:100vh;
   background:#0f0f14;color:#e7e7ee;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:28px}
 h1{font-size:26px;margin:0;color:#a78bfa}
 .tag{color:#9a9aae;font-size:13px;margin-top:-14px}
 .cards{display:flex;gap:22px;flex-wrap:wrap;justify-content:center;max-width:760px}
 a.card{width:320px;text-decoration:none;color:inherit;background:#17171f;border:1px solid #262633;
   border-radius:14px;padding:24px;transition:border-color .15s,transform .15s}
 a.card:hover{border-color:#a78bfa;transform:translateY(-3px)}
 .card h2{margin:0 0 6px;font-size:19px}
 .cc h2{color:#8b5cf6}.ar h2{color:#f87171}
 .card p{margin:0;font-size:13px;color:#b6b6c6;line-height:1.5}
 .go{margin-top:14px;font-size:12px;color:#8b8b9e}
</style></head><body>
 <div><h1>◎ Crosscheck &amp; Argus</h1></div>
 <div class="tag">Two tools on one contradiction engine, built on cognee.</div>
 <div class="cards">
   <a class="card cc" href="/crosscheck/">
     <h2>Crosscheck</h2>
     <p>Persistent research memory that catches when your sources disagree — with who
        said what, and when.</p>
     <div class="go">Open Crosscheck →</div>
   </a>
   <a class="card ar" href="/argus/">
     <h2>◎ Argus</h2>
     <p>Spend &amp; contract leakage auditor. Finds where invoices, POs and contracts
        disagree — and puts a dollar figure on each.</p>
     <div class="go">Open Argus →</div>
   </a>
 </div>
</body></html>"""


@app.get("/", response_class=HTMLResponse)
def hub():
    return _HUB


app.mount("/crosscheck", crosscheck_app)
app.mount("/argus", argus_app)
