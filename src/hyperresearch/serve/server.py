"""Lightweight HTTP server for browsing hyperresearch vaults."""

from __future__ import annotations

import html as html_mod
import json
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer

from hyperresearch.serve import prd_scanner, prd_views, research_views
from hyperresearch.serve.renderer import render_markdown

# -- Vintage cream & dark brown theme --
CSS = """
:root {
  --nav-width: 300px;
  --bg: #fdf6ec;
  --bg-alt: #f5ead6;
  --fg: #3b2f1e;
  --fg-dim: #7a6b57;
  --accent: #8b5e3c;
  --accent-light: #c4956a;
  --link: #6b4226;
  --link-hover: #8b5e3c;
  --nav-bg: #2c1e0f;
  --nav-fg: #e8d5b8;
  --nav-link: #d4b896;
  --nav-heading: #f0e0c8;
  --border: #d4c4a8;
  --tag-bg: #e8d5b8;
  --tag-fg: #5a3e24;
  --code-bg: #efe3cf;
  --pre-bg: #2c1e0f;
  --pre-fg: #e8d5b8;
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
       line-height: 1.6; color: var(--fg); background: var(--bg); }
a { color: var(--link); text-decoration: none; border-bottom: 1px solid transparent; }
a:hover { border-bottom-color: var(--accent); }
.wiki-link { color: var(--accent); font-weight: 600; }

.layout { display: flex; min-height: 100vh; }
nav { width: var(--nav-width); min-width: 200px; max-width: 500px;
      background: var(--nav-bg); color: var(--nav-fg); padding: 1.2rem;
      position: fixed; height: 100vh; overflow-y: auto; resize: horizontal; overflow-x: hidden;
      display: flex; flex-direction: column; }
nav .nav-top { flex: 1; overflow-y: auto; min-height: 0; }
nav .nav-bottom { flex-shrink: 0; padding-top: 0.8rem; margin-top: 0.5rem;
                  border-top: 1px solid rgba(255,255,255,0.1); }
nav .nav-bottom a { font-size: 0.9rem; padding: 6px 0; }
nav a { color: var(--nav-link); display: block; padding: 3px 0; font-size: 0.82rem;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        border: none; }
nav a:hover { color: #fff; }
nav h3 { color: var(--nav-heading); margin: 1.2rem 0 0.4rem 0; font-size: 0.7rem;
         text-transform: uppercase; letter-spacing: 0.08em;
         font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
nav .brand { font-size: 1.2rem; font-weight: bold; color: #fff;
             letter-spacing: 0.02em; }
nav .brand-sub { font-size: 0.7rem; color: var(--fg-dim); margin-top: -0.2rem; margin-bottom: 1rem;
                 font-family: -apple-system, sans-serif; }
.nav-handle { width: 5px; position: fixed; left: var(--nav-width); top: 0; height: 100vh;
              cursor: col-resize; background: transparent; z-index: 10; }
.nav-handle:hover { background: var(--accent-light); }

main { margin-left: var(--nav-width); padding: 2.5rem 3rem;
       max-width: min(1400px, calc(100vw - var(--nav-width)));
       width: 100%; flex: 1; box-sizing: border-box; }
main .prose-narrow { max-width: 880px; }
main h1 { margin-bottom: 0.5rem; font-weight: 700; color: var(--fg); }
main h2 { margin-top: 2rem; margin-bottom: 0.5rem; border-bottom: 1px solid var(--border);
           padding-bottom: 0.3rem; color: var(--accent); }
main h3 { margin-top: 1.2rem; color: var(--fg); }

.meta { color: var(--fg-dim); font-size: 0.82rem; margin-bottom: 1.5rem;
        font-family: -apple-system, sans-serif; }
.meta .tag { background: var(--tag-bg); color: var(--tag-fg); padding: 2px 8px; border-radius: 3px;
             font-size: 0.72rem; margin-right: 4px; }
.meta .status { background: var(--bg-alt); color: var(--accent); padding: 2px 8px; border-radius: 3px;
                font-size: 0.72rem; border: 1px solid var(--border); }
.meta .status.deprecated { background: #f0d0c0; color: #8b3a2a; }
.meta .status.draft { background: #f5e6c8; color: #7a5a2a; }

.backlinks { background: var(--bg-alt); border: 1px solid var(--border);
             border-radius: 6px; padding: 1rem; margin-top: 2rem; }
.backlinks h3 { font-size: 0.85rem; margin-bottom: 0.5rem; color: var(--accent); }
.backlinks li { font-size: 0.82rem; }

code { background: var(--code-bg); padding: 2px 6px; border-radius: 3px; font-size: 0.88em; }
pre { background: var(--pre-bg); color: var(--pre-fg); padding: 1rem; border-radius: 6px;
      overflow-x: auto; margin: 1rem 0; font-size: 0.88rem; }
pre code { background: none; padding: 0; color: inherit; }

.md-table { border-collapse: collapse; margin: 1rem 0; }
.md-table th, .md-table td { border: 1px solid var(--border); padding: 8px 12px; text-align: left; }
.md-table th { background: var(--bg-alt); font-weight: 600; }
.md-table tr:nth-child(even) { background: var(--bg-alt); }

blockquote { border-left: 3px solid var(--accent-light); padding-left: 1rem;
             color: var(--fg-dim); margin: 1rem 0; font-style: italic; }
ul { margin: 0.5rem 0 0.5rem 1.5rem; }
li { margin: 0.2rem 0; }
hr { border: none; border-top: 1px solid var(--border); margin: 1.5rem 0; }

.search-box { margin-bottom: 1rem; }
.search-box input { width: 100%; padding: 7px 10px; border: 1px solid #5a4030;
                    border-radius: 4px; background: #1e1208; color: var(--nav-fg);
                    font-family: -apple-system, sans-serif; font-size: 0.85rem; }
.search-box input::placeholder { color: #7a6b57; }
.results .result { margin-bottom: 1.2rem; }
.results .result .title { font-weight: 600; }
.results .result .snippet { color: var(--fg-dim); font-size: 0.82rem;
                            font-family: -apple-system, sans-serif; }
mark { background: #f0d8a0; color: var(--fg); padding: 1px 2px; border-radius: 2px; }

/* Graph page */
.graph-container { position: relative; width: 100%; height: calc(100vh - 120px);
                   background: var(--bg-alt); border: 1px solid var(--border); border-radius: 6px; }
.graph-fullpage { height: 100vh; border: none; border-radius: 0;
                  position: fixed; top: 0; left: var(--nav-width); right: 0; bottom: 0;
                  width: calc(100vw - var(--nav-width)); z-index: 1; }
.graph-container canvas { width: 100%; height: 100%; cursor: grab; }
.graph-container canvas:active { cursor: grabbing; }
.graph-search { position: absolute; top: 12px; right: 12px; z-index: 5;
                padding: 6px 10px; border: 1px solid var(--border); border-radius: 4px;
                background: var(--bg); color: var(--fg); font-size: 0.85rem; width: 200px; }
.graph-info { position: absolute; bottom: 12px; left: 12px; z-index: 5;
              background: var(--bg); border: 1px solid var(--border); border-radius: 4px;
              padding: 6px 10px; font-size: 0.78rem; color: var(--fg-dim);
              font-family: -apple-system, sans-serif; pointer-events: none; }
""" + prd_views.PRD_CSS + research_views.RESEARCH_CSS

FAVICON = (
    "data:image/svg+xml,"
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'>"
    "<rect x='10' y='20' width='80' height='65' rx='4' fill='%232c1e0f' stroke='%238b5e3c' stroke-width='3'/>"
    "<rect x='20' y='10' width='60' height='15' rx='3' fill='%238b5e3c'/>"
    "<line x1='25' y1='42' x2='75' y2='42' stroke='%23d4b896' stroke-width='2'/>"
    "<line x1='25' y1='52' x2='65' y2='52' stroke='%23d4b896' stroke-width='2'/>"
    "<line x1='25' y1='62' x2='70' y2='62' stroke='%23d4b896' stroke-width='2'/>"
    "<circle cx='72' cy='72' r='8' fill='%238b5e3c'/>"
    "<line x1='72' y1='67' x2='72' y2='77' stroke='%23fdf6ec' stroke-width='2'/>"
    "<line x1='67' y1='72' x2='77' y2='72' stroke='%23fdf6ec' stroke-width='2'/>"
    "</svg>"
)

DRAG_JS = """
<script>
(function() {
  var handle = document.querySelector('.nav-handle');
  var nav = document.querySelector('nav');
  var dragging = false;
  if (!handle) return;
  handle.addEventListener('mousedown', function(e) { dragging = true; e.preventDefault(); });
  document.addEventListener('mousemove', function(e) {
    if (!dragging) return;
    var w = Math.min(Math.max(e.clientX, 200), 500);
    document.documentElement.style.setProperty('--nav-width', w + 'px');
    nav.style.width = w + 'px';
  });
  document.addEventListener('mouseup', function() { dragging = false; });
})();
</script>
"""

GRAPH_JS = """
<script>
(function() {
  var canvas = document.getElementById('graph-canvas');
  var ctx = canvas.getContext('2d');
  var info = document.getElementById('graph-info');
  var searchBox = document.getElementById('graph-search');
  var nodes = [], edges = [], nodeMap = {};
  var W, H, scale = 1, panX = 0, panY = 0, dragging = false, dragX = 0, dragY = 0;
  var hoverNode = null, searchTerm = '';

  function resize() { W = canvas.width = canvas.parentElement.clientWidth; H = canvas.height = canvas.parentElement.clientHeight; }
  window.addEventListener('resize', resize);
  resize();

  fetch('/api/graph').then(r => r.json()).then(function(data) {
    nodes = data.nodes; edges = data.edges;
    // Center around origin
    nodes.forEach(function(n, i) { nodeMap[n.id] = i; n.x = (Math.random()-0.5)*800; n.y = (Math.random()-0.5)*800; n.vx = 0; n.vy = 0; });
    simulate();
  });

  function fitToScreen() {
    if (nodes.length === 0) return;
    var minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;
    nodes.forEach(function(n) {
      if (n.x < minX) minX = n.x; if (n.x > maxX) maxX = n.x;
      if (n.y < minY) minY = n.y; if (n.y > maxY) maxY = n.y;
    });
    var gw = maxX - minX + 100, gh = maxY - minY + 100;
    var cx = (minX + maxX) / 2, cy = (minY + maxY) / 2;
    scale = Math.min(W / gw, H / gh) * 0.9;
    scale = Math.min(Math.max(scale, 0.02), 3);
    panX = -cx;
    panY = -cy;
  }

  function simulate() {
    var alpha = 1.0;
    function tick() {
      if (alpha < 0.001) { fitToScreen(); draw(); return; }
      alpha *= 0.98;
      // Repulsion
      for (var i = 0; i < nodes.length; i++) {
        for (var j = i+1; j < nodes.length; j++) {
          var dx = nodes[j].x - nodes[i].x, dy = nodes[j].y - nodes[i].y;
          var d2 = dx*dx + dy*dy + 1;
          var f = 800 / d2 * alpha;
          nodes[i].vx -= dx * f; nodes[i].vy -= dy * f;
          nodes[j].vx += dx * f; nodes[j].vy += dy * f;
        }
      }
      // Attraction along edges
      edges.forEach(function(e) {
        var si = nodeMap[e[0]], ti = nodeMap[e[1]];
        if (si === undefined || ti === undefined) return;
        var dx = nodes[ti].x - nodes[si].x, dy = nodes[ti].y - nodes[si].y;
        var d = Math.sqrt(dx*dx + dy*dy) + 1;
        var f = (d - 120) * 0.005 * alpha;
        nodes[si].vx += dx/d * f; nodes[si].vy += dy/d * f;
        nodes[ti].vx -= dx/d * f; nodes[ti].vy -= dy/d * f;
      });
      // Center gravity
      nodes.forEach(function(n) {
        n.vx += (0 - n.x) * 0.0005 * alpha;
        n.vy += (0 - n.y) * 0.0005 * alpha;
        n.vx *= 0.85; n.vy *= 0.85;
        n.x += n.vx; n.y += n.vy;
      });
      draw();
      requestAnimationFrame(tick);
    }
    tick();
  }

  function toScreen(x, y) { return [(x + panX) * scale + W/2, (y + panY) * scale + H/2]; }
  function toWorld(sx, sy) { return [(sx - W/2) / scale - panX, (sy - H/2) / scale - panY]; }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    ctx.save();
    ctx.translate(W/2, H/2);
    ctx.scale(scale, scale);
    ctx.translate(panX, panY);

    // Edges
    ctx.strokeStyle = 'rgba(139,94,60,0.12)';
    ctx.lineWidth = 0.5 / scale;
    edges.forEach(function(e) {
      var si = nodeMap[e[0]], ti = nodeMap[e[1]];
      if (si === undefined || ti === undefined) return;
      var s = nodes[si], t = nodes[ti];
      var highlight = hoverNode && (s.id === hoverNode.id || t.id === hoverNode.id);
      if (highlight) { ctx.strokeStyle = 'rgba(139,94,60,0.6)'; ctx.lineWidth = 1.5 / scale; }
      ctx.beginPath(); ctx.moveTo(s.x, s.y); ctx.lineTo(t.x, t.y); ctx.stroke();
      if (highlight) { ctx.strokeStyle = 'rgba(139,94,60,0.12)'; ctx.lineWidth = 0.5 / scale; }
    });

    // Nodes
    var sl = searchTerm.toLowerCase();
    nodes.forEach(function(n) {
      var r = Math.max(3, Math.min(20, 3 + Math.pow(n.inbound, 0.7) * 1.5));
      var isHover = hoverNode && n.id === hoverNode.id;
      var isConnected = hoverNode && n.connected && n.connected.has(hoverNode.id);
      var isSearch = sl && n.title.toLowerCase().includes(sl);
      var alpha = (hoverNode && !isHover && !isConnected) ? 0.15 : 1;
      if (isSearch) alpha = 1;

      ctx.globalAlpha = alpha;
      ctx.fillStyle = isSearch ? '#c4652a' : isHover ? '#6b4226' : n.status === 'evergreen' ? '#8b5e3c' : n.status === 'draft' ? '#b8a080' : '#a08060';
      ctx.beginPath(); ctx.arc(n.x, n.y, r / scale, 0, Math.PI * 2); ctx.fill();

      if ((isHover || isSearch) && scale > 0.1) {
        ctx.fillStyle = '#3b2f1e';
        ctx.font = (11 / scale) + 'px -apple-system, sans-serif';
        ctx.fillText(n.title.substring(0, 40), n.x + r/scale + 4/scale, n.y + 3/scale);
      }
      ctx.globalAlpha = 1;
    });

    ctx.restore();
    if (hoverNode) info.textContent = hoverNode.title + ' (' + hoverNode.inbound + ' inbound)';
    else info.textContent = nodes.length + ' notes, ' + edges.length + ' links';
  }

  // Build connectivity sets for hover highlighting
  function buildConnections() {
    nodes.forEach(function(n) { n.connected = new Set(); });
    edges.forEach(function(e) {
      var si = nodeMap[e[0]], ti = nodeMap[e[1]];
      if (si !== undefined && ti !== undefined) {
        nodes[si].connected.add(e[1]);
        nodes[ti].connected.add(e[0]);
      }
    });
  }
  setTimeout(buildConnections, 1000);

  // Mouse interaction
  var mouseDown = false, lastMX = 0, lastMY = 0;
  canvas.addEventListener('wheel', function(e) {
    e.preventDefault();
    var factor = e.deltaY > 0 ? 0.9 : 1.1;
    scale = Math.min(Math.max(scale * factor, 0.02), 5);
    draw();
  });
  canvas.addEventListener('mousedown', function(e) { mouseDown = true; lastMX = e.clientX; lastMY = e.clientY; });
  canvas.addEventListener('mousemove', function(e) {
    if (mouseDown) {
      panX += (e.clientX - lastMX) / scale;
      panY += (e.clientY - lastMY) / scale;
      lastMX = e.clientX; lastMY = e.clientY;
      draw();
    } else {
      // Hit test for hover
      var rect = canvas.getBoundingClientRect();
      var wp = toWorld(e.clientX - rect.left, e.clientY - rect.top);
      hoverNode = null;
      for (var i = 0; i < nodes.length; i++) {
        var dx = nodes[i].x - wp[0], dy = nodes[i].y - wp[1];
        if (dx*dx + dy*dy < 100) { hoverNode = nodes[i]; break; }
      }
      canvas.style.cursor = hoverNode ? 'pointer' : 'grab';
      draw();
    }
  });
  canvas.addEventListener('mouseup', function() { mouseDown = false; });
  canvas.addEventListener('click', function() {
    if (hoverNode) window.location.href = '/note/' + hoverNode.id;
  });

  searchBox.addEventListener('input', function() { searchTerm = this.value; draw(); });
})();
</script>
"""


class HyperresearchHandler(BaseHTTPRequestHandler):
    vault = None
    _db = None

    @property
    def db(self):
        if self.__class__._db is None:
            import sqlite3
            self.__class__._db = sqlite3.connect(str(self.__class__.vault.db_path), check_same_thread=False)
            self.__class__._db.row_factory = sqlite3.Row
        return self.__class__._db

    def _prd_records(self):
        return prd_scanner.scan_prds(self.__class__.vault.root)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        if path == "/" or path == "":
            self._serve_home()
        elif path == "/notes":
            show_stubs = bool(query.get("show_stubs", ["0"])[0] in ("1", "true", "yes"))
            self._serve_index(show_stubs=show_stubs)
        elif path.startswith("/note/"):
            note_id = urllib.parse.unquote(path[6:])
            self._serve_note(note_id)
        elif path.startswith("/tag/"):
            tag = urllib.parse.unquote(path[5:])
            self._serve_tag(tag)
        elif path == "/tags":
            self._serve_tags()
        elif path == "/search":
            q = query.get("q", [""])[0]
            self._serve_search(q)
        elif path == "/graph":
            self._serve_graph()
        elif path == "/api/graph":
            self._serve_graph_api()
        elif path == "/features":
            self._serve_features()
        elif path.startswith("/feature/"):
            tag = urllib.parse.unquote(path[len("/feature/"):])
            self._serve_feature(tag)
        elif path == "/prds":
            self._serve_prds()
        elif path.startswith("/prd/"):
            tag = urllib.parse.unquote(path[len("/prd/"):])
            self._serve_prd(tag)
        elif path == "/api/features":
            self._serve_features_api()
        else:
            self._send(404, "<h1>Not Found</h1>")

    def _send(self, code: int, body_html: str, title: str = "Home", extra_head: str = "", extra_body: str = ""):
        nav = self._build_nav()
        full = f"""<!DOCTYPE html><html><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} | LLM-Hyperresearch</title>
<link rel="icon" href="{FAVICON}">
<style>{CSS}</style>{extra_head}</head>
<body><div class="layout"><nav>{nav}</nav><div class="nav-handle"></div><main>{body_html}</main></div>{DRAG_JS}{extra_body}</body></html>"""
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(full.encode("utf-8"))

    def _send_json(self, data):
        body = json.dumps(data)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body.encode("utf-8"))

    def _build_nav(self) -> str:
        vault = self.__class__.vault
        name = vault.config.name
        lines = [
            '<div class="nav-top">',
            '<div class="brand">LLM-Hyperresearch</div>',
            f'<div class="brand-sub">{html_mod.escape(name)}</div>',
            '<form action="/search"><div class="search-box">'
            '<input type="text" name="q" placeholder="Search..."></div></form>',
            '<a href="/">Home</a>',
            '<a href="/features">Features</a>',
            '<a href="/prds">PRDs</a>',
            '<a href="/notes">All notes</a>',
            '<a href="/tags">Tags</a>',
            '<h3>Recent</h3>',
        ]
        rows = self.db.execute(
            "SELECT id, title, type, COALESCE(summary,'') AS summary FROM notes "
            "WHERE type NOT IN ('index') "
            "ORDER BY COALESCE(updated, created) DESC LIMIT 15"
        ).fetchall()
        for r in rows:
            if research_views.is_stub_note(r["summary"]):
                continue
            pretty = research_views.clean_title(r["title"] or "")
            tag = "F" if (r["id"] or "").startswith("final_report_") or pretty.lower().startswith("final report") else ("I" if r["type"] == "interim" else "N")
            tag_style = "color:#c4956a" if tag == "F" else ("color:#d4b896" if tag == "I" else "color:#7a6b57")
            badge = f'<span style="{tag_style};font-size:0.66rem;margin-right:5px">[{tag}]</span>'
            lines.append(
                f'<a href="/note/{html_mod.escape(r["id"])}" title="{html_mod.escape(pretty)}">'
                f'{badge}{html_mod.escape(pretty)}</a>'
            )
        lines.append('</div>')
        lines.append(
            '<div class="nav-bottom">'
            '<a href="/graph" title="Knowledge Graph" style="display:flex;align-items:center;gap:6px">'
            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">'
            '<circle cx="5" cy="6" r="2.5"/><circle cx="19" cy="6" r="2.5"/>'
            '<circle cx="12" cy="18" r="2.5"/><circle cx="5" cy="18" r="2.5"/>'
            '<circle cx="19" cy="18" r="2.5"/><circle cx="12" cy="10" r="2.5"/>'
            '<line x1="7" y1="7" x2="10" y2="9"/><line x1="17" y1="7" x2="14" y2="9"/>'
            '<line x1="12" y1="12.5" x2="12" y2="15.5"/>'
            '<line x1="7" y1="17" x2="10" y2="16"/><line x1="17" y1="17" x2="14" y2="16"/>'
            '</svg>Graph</a></div>'
        )
        return "\n".join(lines)

    def _serve_index(self, show_stubs: bool = False):
        rows = self.db.execute(
            "SELECT id, title, type, status, COALESCE(summary,'') AS summary, "
            "word_count FROM notes WHERE type NOT IN ('index') "
            "ORDER BY COALESCE(updated, created) DESC"
        ).fetchall()
        tag_rows = self.db.execute(
            "SELECT note_id, tag FROM tags ORDER BY tag"
        ).fetchall()
        tags_by_note: dict[str, list[str]] = {}
        for tr in tag_rows:
            tags_by_note.setdefault(tr["note_id"], []).append(tr["tag"])

        note_rows = [
            research_views.NoteRow(
                id=r["id"],
                raw_title=r["title"] or "",
                type=r["type"] or "",
                status=r["status"] or "",
                summary=r["summary"] or "",
                word_count=r["word_count"] or 0,
                tags=tags_by_note.get(r["id"], []),
            )
            for r in rows
        ]
        body = research_views.render_grouped_index(
            note_rows,
            show_stubs=show_stubs,
            total_count=len(note_rows),
        )
        self._send(200, body, "All notes")

    def _serve_note(self, note_id: str):
        row = self.db.execute(
            "SELECT n.*, nc.body FROM notes n "
            "JOIN note_content nc ON n.id = nc.note_id WHERE n.id = ?",
            (note_id,),
        ).fetchone()
        if not row:
            self._send(404, f"<h1>Note not found: {html_mod.escape(note_id)}</h1>")
            return

        tags = [r["tag"] for r in self.db.execute("SELECT tag FROM tags WHERE note_id = ?", (note_id,))]
        backlinks = self.db.execute(
            "SELECT l.source_id, n.title FROM links l "
            "JOIN notes n ON l.source_id = n.id WHERE l.target_id = ? ORDER BY n.title",
            (note_id,),
        ).fetchall()

        html_body = render_markdown(row["body"])
        html_body = prd_views._inject_heading_anchors(html_body, row["body"])
        toc_html = prd_views._build_toc(row["body"])

        pretty_title = research_views.clean_title(row["title"] or "")
        meta = research_views.render_note_meta_header(
            title=pretty_title,
            note_type=row["type"] or "",
            status=row["status"] or "",
            tags=tags,
            word_count=row["word_count"] or 0,
        )
        title_block = f'<h1>{html_mod.escape(pretty_title)}</h1>' if pretty_title else ""
        bl_html = ""
        if backlinks:
            bl_items = "\n".join(
                f'<li><a href="/note/{html_mod.escape(r["source_id"])}">{html_mod.escape(r["title"])}</a></li>' for r in backlinks
            )
            bl_html = f'<div class="backlinks"><h3>Backlinks</h3><ul>{bl_items}</ul></div>'

        related_prds_html = ""
        try:
            related = prd_scanner.prds_for_research(self._prd_records(), note_id)
            related_prds_html = prd_views.render_related_prds_panel(related)
        except Exception:
            related_prds_html = ""

        self._send(
            200,
            f"{title_block}\n{meta}\n{toc_html}\n{html_body}\n{related_prds_html}\n{bl_html}",
            html_mod.escape(pretty_title or row["title"]),
        )

    def _serve_tag(self, tag: str):
        rows = self.db.execute(
            "SELECT n.id, n.title, n.status, n.summary FROM notes n "
            "JOIN tags t ON n.id = t.note_id WHERE t.tag = ? ORDER BY n.title",
            (tag,),
        ).fetchall()
        safe_tag = html_mod.escape(tag)
        body = f"<h1>Tag: {safe_tag}</h1>\n<p>{len(rows)} notes</p>\n<ul>\n"
        for r in rows:
            summary = f' <span style="color:var(--fg-dim);font-size:0.85rem">-- {html_mod.escape(r["summary"] or "")}</span>' if r["summary"] else ""
            body += f'<li><a href="/note/{html_mod.escape(r["id"])}">{html_mod.escape(r["title"])}</a>{summary}</li>\n'
        body += "</ul>"
        self._send(200, body, f"Tag: {safe_tag}")

    def _serve_tags(self):
        rows = self.db.execute(
            "SELECT tag, COUNT(*) as c FROM tags GROUP BY tag ORDER BY c DESC"
        ).fetchall()
        body = "<h1>All Tags</h1>\n<ul>\n"
        for r in rows:
            body += f'<li><a href="/tag/{html_mod.escape(r["tag"])}">{html_mod.escape(r["tag"])}</a> ({r["c"]})</li>\n'
        body += "</ul>"
        self._send(200, body, "Tags")

    def _serve_search(self, query: str):
        safe_q = html_mod.escape(query)
        body = f'<h1>Search: {safe_q}</h1>\n'
        if not query:
            body += "<p>Enter a search term.</p>"
            self._send(200, body, "Search")
            return

        from hyperresearch.search.fts import search_fts
        results = search_fts(self.db, query, limit=50)
        body += f"<p>{len(results)} results</p>\n<div class='results'>\n"
        for r in results:
            snippet = r["snippet"].replace(">>>", "<mark>").replace("<<<", "</mark>")
            body += (
                f'<div class="result"><div class="title">'
                f'<a href="/note/{html_mod.escape(r["id"])}">{html_mod.escape(r["title"])}</a></div>'
                f'<div class="snippet">{snippet}</div></div>\n'
            )
        body += "</div>"
        self._send(200, body, f"Search: {safe_q}")

    def _serve_home(self):
        records = self._prd_records()
        if records:
            groups = prd_scanner.feature_groups(records)
            body = prd_views.render_features_index(groups)
            self._send(200, body, "Home")
            return
        self._serve_index()

    def _serve_features(self):
        records = self._prd_records()
        groups = prd_scanner.feature_groups(records)
        body = prd_views.render_features_index(groups)
        self._send(200, body, "Features")

    def _serve_feature(self, prd_tag: str):
        records = self._prd_records()
        record = prd_scanner.find_prd(records, prd_tag)
        if not record:
            self._send(404, f"<h1>Feature not found: {html_mod.escape(prd_tag)}</h1>")
            return
        title, body = prd_views.render_feature_detail(record)
        self._send(200, body, html_mod.escape(title))

    def _serve_prds(self):
        records = self._prd_records()
        body = prd_views.render_prds_index(records)
        self._send(200, body, "PRDs")

    def _serve_prd(self, prd_tag: str):
        records = self._prd_records()
        record = prd_scanner.find_prd(records, prd_tag)
        if not record:
            self._send(404, f"<h1>PRD not found: {html_mod.escape(prd_tag)}</h1>")
            return
        title, body = prd_views.render_prd_detail(record)
        self._send(200, body, html_mod.escape(title))

    def _serve_features_api(self):
        records = self._prd_records()
        payload = [
            {
                "prd_tag": r.prd_tag,
                "title": r.title,
                "tier": r.tier,
                "modality": r.modality,
                "word_count": r.word_count,
                "research_note_id": r.research_note_id,
                "research_path": r.research_path,
                "has_feature_request": r.feature_request is not None,
            }
            for r in records
        ]
        self._send_json({"features": payload, "count": len(payload)})

    def _serve_graph(self):
        body = (
            '<div class="graph-container graph-fullpage">'
            '<canvas id="graph-canvas"></canvas>'
            '<input type="text" class="graph-search" id="graph-search" placeholder="Filter nodes...">'
            '<div class="graph-info" id="graph-info">Loading...</div>'
            '</div>'
        )
        self._send(200, body, "Graph", extra_body=GRAPH_JS)

    def _serve_graph_api(self):
        nodes_rows = self.db.execute(
            "SELECT n.id, n.title, n.status, n.word_count FROM notes n WHERE n.type NOT IN ('index')"
        ).fetchall()
        inbound_counts = {}
        for r in self.db.execute(
            "SELECT target_id, COUNT(*) as c FROM links WHERE target_id IS NOT NULL GROUP BY target_id"
        ):
            inbound_counts[r["target_id"]] = r["c"]

        nodes = [
            {"id": r["id"], "title": r["title"], "status": r["status"],
             "words": r["word_count"], "inbound": inbound_counts.get(r["id"], 0)}
            for r in nodes_rows
        ]
        edges_rows = self.db.execute(
            "SELECT DISTINCT source_id, target_id FROM links WHERE target_id IS NOT NULL"
        ).fetchall()
        edges = [[r["source_id"], r["target_id"]] for r in edges_rows]

        self._send_json({"nodes": nodes, "edges": edges})

    def log_message(self, format, *args):
        pass


def run_server(vault, port: int = 9089, open_browser: bool = False):
    import signal
    import sys

    HyperresearchHandler.vault = vault
    server = HTTPServer(("127.0.0.1", port), HyperresearchHandler)
    server.timeout = 0.5  # Check for Ctrl+C every 500ms
    url = f"http://127.0.0.1:{port}"
    print(f"Serving at {url}")
    print("Press Ctrl+C to stop.\n")

    if open_browser:
        import webbrowser
        webbrowser.open(url)

    running = True

    def _shutdown(sig, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, _shutdown)

    while running:
        server.handle_request()

    print("\nStopped.")
    server.server_close()
    sys.exit(0)
