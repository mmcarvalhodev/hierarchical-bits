"""bhtrace demo — a distributed trace as a .bht envelope, measured.

Builds a realistic, attribute-heavy trace (a checkout request fanning across
services), writes it as .bht, and shows each reading reads only the fraction it
needs — against the honest baseline (a flat trace JSON loaded whole for any
query).

Run:  X:/miniconda3/python.exe X:/bitH/bhtrace/demo.py
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from bhtrace import Span, TraceReader, TraceStore  # noqa: E402

OUT = Path(__file__).resolve().parent
SERVICES = ["gateway", "auth", "users", "orders", "payments", "db", "cache",
            "search", "email", "inventory"]
OPS = ["handle", "query", "fetch", "validate", "render", "call", "lookup",
       "write", "read", "authorize", "charge", "enqueue"]


def build() -> TraceStore:
    """A checkout request: one root span fanning into nested service calls.

    Attribute-heavy on purpose (SQL, headers, stack traces on errors) — the
    payload dominates, the structure is light. That is exactly the shape where
    reading the skeleton without the payload pays off, as the study's law says.
    """
    store = TraceStore("checkout-7f3a91")
    rnd = random.Random(0)
    counter = [0]

    def new_id() -> str:
        counter[0] += 1
        return f"s{counter[0]:04d}"

    def attrs(service: str, op: str, err: bool) -> dict:
        # Realistic OTel-style attribute set — real spans are attribute-heavy
        # (semantic conventions, headers, baggage, resource attributes).
        d = {
            "service.name": service, "span.kind": "server",
            "http.method": rnd.choice(["GET", "POST", "PUT"]),
            "http.route": f"/{service}/{op}",
            "http.status_code": 500 if err else 200,
            "http.user_agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                               "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "http.response.body.sample": "{" + ",".join(
                f'"field_{i}":"{rnd.randrange(16**8):08x}"' for i in range(rnd.randint(8, 22))) + "}",
            "net.peer.ip": f"10.0.{rnd.randint(0,255)}.{rnd.randint(0,255)}",
            "host.name": f"ip-10-0-{rnd.randint(0,255)}-{rnd.randint(0,255)}.ec2.internal",
            "k8s.pod.name": f"{service}-{rnd.randrange(16**8):08x}-"
                            + "".join(rnd.choice("abcdefghijklmnop") for _ in range(5)),
            "k8s.namespace.name": "production",
            "thread.name": f"http-worker-{rnd.randint(1,64)}",
            "telemetry.sdk.name": "opentelemetry", "telemetry.sdk.version": "1.25.0",
            "deployment.environment": "production", "cloud.region": "us-east-1",
            "user.id": f"u_{rnd.randint(1000,9999)}",
            "request.id": "req_%016x" % rnd.getrandbits(64),
        }
        if service == "db":
            d["db.system"] = "postgresql"
            d["db.statement"] = (
                f"SELECT t.*, j.label, j.created_at FROM {op}_table t "
                "LEFT JOIN labels j ON j.entity_id = t.id "
                "WHERE t.tenant_id = $1 AND t.id = ANY($2) AND t.deleted_at IS NULL "
                "ORDER BY t.created_at DESC LIMIT 100 OFFSET $3")
        if err:
            d["exception.type"] = "RuntimeError"
            d["exception.message"] = "downstream call failed: timeout after 3000ms"
            d["exception.stacktrace"] = "Traceback (most recent call last):\n" + "\n".join(
                f'  File "svc/{service}/{op}.py", line {rnd.randint(1,400)}, in handler'
                for _ in range(35))
        return d

    def events(err: bool) -> list:
        evs = [{"ts_us": rnd.randint(0, 1000), "name": "enter", "level": "debug"}]
        if err:
            evs.append({"ts_us": rnd.randint(0, 1000), "name": "exception",
                        "level": "error", "message": "downstream call failed: timeout after 3000ms"})
        return evs

    def gen(parent_id, service, op, start, dur, depth) -> None:
        sid = new_id()
        err = rnd.random() < 0.06
        store.add(Span(sid, parent_id, service, op, start, dur,
                       "error" if err else "ok", attrs(service, op, err), events(err)))
        if depth <= 0:
            return
        n = rnd.randint(2, 4) if depth > 1 else rnd.randint(0, 2)
        t = start + max(1, dur // 20)
        for _ in range(n):
            csvc = rnd.choice(SERVICES)
            cop = rnd.choice(OPS)
            cdur = max(50, int(dur * rnd.uniform(0.12, 0.5)))
            gen(sid, csvc, cop, t, cdur, depth - 1)
            t += max(1, cdur // 2)

    gen(None, "gateway", "POST /checkout", 0, 482_000, 5)
    return store


def main() -> None:
    store = build()
    bht = OUT / "trace.bht"
    store.save(bht)

    flat = OUT / "trace.json"
    flat.write_text(json.dumps([
        {**{k: getattr(s, k) for k in ("span_id", "parent_id", "service",
            "operation", "start_us", "dur_us", "status")},
         "attributes": s.attributes, "events": s.events}
        for s in store._spans], ensure_ascii=False), encoding="utf-8")  # noqa: SLF001

    reader = TraceReader(bht)
    flat_size = flat.stat().st_size
    bht_size = reader.file_size

    # pick a representative mid-depth branch (a typical drill-in: 3–15 spans),
    # not a near-root span whose subtree is most of the trace
    def subtree_size(sid):
        n, stack = 0, [sid]
        while stack:
            n += 1
            stack.extend(reader._children.get(stack.pop(), []))  # noqa: SLF001
        return n
    candidates = [e["id"] for e in reader.tree
                  if e["parent"] is not None and 3 <= subtree_size(e["id"]) <= 15]
    branch = candidates[len(candidates) // 2] if candidates else reader.tree[1]["id"]

    L: list[str] = []
    p = L.append
    p("# bhtrace — distributed trace as .bht (measured demo)\n")
    p(f"- spans: **{len(store)}** · services: **{len(reader.summary()[0]['services'])}**")
    p(f"- `.bht` file: **{bht_size:,} bytes** · flat JSON: **{flat_size:,} bytes**\n")
    p("The flat baseline reads the **whole** trace for any query. The `.bht` "
      "keeps the span tree as the index and reads heavy attributes only on demand.\n")
    p("| reading | what it returns | bytes read | % of file | vs flat |")
    p("|---|---|---|---|---|")

    def row(label, what, stats, n):
        ratio = flat_size / stats.bytes_read if stats.bytes_read else float("inf")
        p(f"| `{label}` | {what} ({n}) | {stats.bytes_read:,} B | "
          f"{stats.fraction*100:.1f}% | **{ratio:.0f}× less** |")

    sm, st = reader.summary()
    row("summary()", "per-service + critical path + slowest", st, len(sm["services"]))
    cp, st = reader.critical_path()
    row("critical_path()", "root→leaf latency chain", st, len(cp))
    sub, st = reader.subtree(branch)
    row(f"subtree('{branch}')", "a span + its descendants", st, len(sub))
    dbs, st = reader.service("db")
    row("service('db')", "all db spans", st, len(dbs))
    fl, st = reader.full()
    row("full()", "everything (baseline)", st, len(fl))

    p("\n## What this demonstrates\n")
    p("- **The same envelope as `bhmem`, a different domain.** A trace is a tree; "
      "'which spans are slow' and 'the critical path' are answered from the "
      "structure index alone — without loading a single attribute or stack trace.")
    p("- **Drill-in is a branch read.** `subtree(span)` and `service(name)` read "
      "only the blocks they touch, proportional to the question.")
    p("- **Honest boundary.** Full-text search across attributes still delegates "
      "to an inverted index; bhtrace makes the structure explicit and routes to "
      "the specialist, it does not replace it.")

    out = OUT / "RESULTS_BHTRACE_DEMO.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")

    print(f"spans={len(store)} bht={bht_size}B flat={flat_size}B")
    for label, fn in [("summary", reader.summary), ("critical_path", reader.critical_path),
                      (f"subtree({branch})", lambda: reader.subtree(branch)),
                      ("service(db)", lambda: reader.service("db")), ("full", reader.full)]:
        _, s = fn()
        r = flat_size / s.bytes_read if s.bytes_read else 0
        print(f"  {label:20s} {s.bytes_read:7d} B  {s.fraction*100:5.1f}%  {r:5.0f}x less")
    print(f"report: {out}")


if __name__ == "__main__":
    main()
