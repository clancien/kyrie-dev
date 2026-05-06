#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime
from html import escape
from pathlib import Path
from urllib.parse import quote

def load_cards(cards_json_path: Path) -> list[dict]:
    if not cards_json_path.exists():
        raise FileNotFoundError(f"Cards JSON not found: {cards_json_path}")

    with cards_json_path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        raise ValueError(f"Expected a JSON list in {cards_json_path}")

    cards = [item for item in data if isinstance(item, dict)]
    cards.sort(
        key=lambda card: (
            card.get("status", ""),
            card.get("created_date", ""),
            card.get("name", ""),
        )
    )
    return cards


def to_relative_analysis_link(project_root: Path, output_dir: Path, md_link: str) -> str:
    raw = (md_link or "").strip()
    if not raw:
        return "#"

    target = (project_root / raw).resolve()
    rel = Path(os.path.relpath(target, output_dir))
    return quote(str(rel), safe="/._-")


def collect_attachment_links(
    project_root: Path, output_dir: Path, md_link: str
) -> list[tuple[str, str]]:
    raw = (md_link or "").strip()
    if not raw:
        return []

    analysis_path = (project_root / raw).resolve()
    card_dir = analysis_path.parent
    if not card_dir.is_dir():
        return []

    links: list[tuple[str, str]] = []
    for path in sorted(card_dir.iterdir()):
        if not path.is_file():
            continue
        if path.name.lower() == "analysis.md":
            continue
        rel = Path(os.path.relpath(path.resolve(), output_dir))
        href = quote(str(rel).replace("\\", "/"), safe="/._-")
        links.append((path.name, href))
    return links


def render_index_html(cards: list[dict], generated_at: str) -> str:
    rows = []
    for card in cards:
        card_id = escape(str(card.get("id", "")))
        card_name = escape(str(card.get("name", "")))
        status = escape(str(card.get("status", "")))
        created_date = escape(str(card.get("created_date", "")))
        members_count = len(card.get("members") or [])
        comments_count = len(card.get("comments") or [])
        detail_file = f"card_{card_id}.html"
        rows.append(
            f"""
            <tr class="clickable-row" data-href="{detail_file}">
              <td class="mono">{card_id}</td>
              <td>{card_name}</td>
              <td><span class="pill status-{status.lower()}">{status or "N/A"}</span></td>
              <td class="hide-sm">{members_count}</td>
              <td class="hide-sm">{comments_count}</td>
              <td>{created_date}</td>
              <td><a class="btn" href="{detail_file}">Ver</a></td>
            </tr>
            """
        )

    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>SIDOT Trello Cards</title>
  <style>
    :root {{
      --bg: #f7f8fb;
      --card: #ffffff;
      --text: #111827;
      --muted: #6b7280;
      --line: #e5e7eb;
      --accent: #0b6ff0;
      --ok: #0f766e;
      --warn: #b45309;
      --closed: #4b5563;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: var(--text);
      background: linear-gradient(180deg, #eef4ff 0%, var(--bg) 180px);
    }}
    .wrap {{ width: 100%; min-height: 100vh; margin: 0; padding: 0; }}
    .panel {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 0;
      box-shadow: none;
      overflow: hidden;
      min-height: 100vh;
    }}
    header {{ padding: 20px 24px 8px; }}
    h1 {{ margin: 0; font-size: 1.5rem; }}
    .meta {{ margin-top: 8px; color: var(--muted); font-size: 0.95rem; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 10px 12px; border-top: 1px solid var(--line); text-align: left; vertical-align: top; }}
    th {{ background: #f9fafb; font-size: 0.9rem; color: #374151; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.86rem; }}
    .pill {{
      display: inline-block;
      border-radius: 999px;
      padding: 4px 10px;
      font-size: 0.78rem;
      font-weight: 600;
      border: 1px solid var(--line);
      background: #f3f4f6;
      color: #374151;
    }}
    .status-descargado {{ background: #e0efff; color: #0c4a9a; border-color: #bfdbfe; }}
    .status-solucionado {{ background: #dcfce7; color: var(--ok); border-color: #86efac; }}
    .status-cerrado {{ background: #e5e7eb; color: var(--closed); border-color: #d1d5db; }}
    .btn {{
      display: inline-block;
      text-decoration: none;
      background: var(--accent);
      color: #fff;
      padding: 6px 10px;
      border-radius: 8px;
      font-weight: 600;
      font-size: 0.86rem;
    }}
    .hint {{ color: var(--muted); font-size: 0.86rem; margin: 10px 24px 20px; }}
    .clickable-row {{ cursor: pointer; }}
    .clickable-row:hover td {{ background: #f8fbff; }}
    @media (max-width: 760px) {{
      .hide-sm {{ display: none; }}
      th, td {{ padding: 9px 8px; }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="panel">
      <header>
        <h1>SIDOT Trello Cards</h1>
        <div class="meta">Total: {len(cards)} tarjetas | Generado: {escape(generated_at)}</div>
      </header>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Nombre</th>
            <th>Estado</th>
            <th class="hide-sm">Asignados</th>
            <th class="hide-sm">Comentarios</th>
            <th class="hide-sm">Fecha</th>
            <th>Detalle</th>
          </tr>
        </thead>
        <tbody>
          {"".join(rows)}
        </tbody>
      </table>
      <div class="hint">Abre "Ver" para navegar una tarjeta y usar "Volver al listado".</div>
    </section>
  </div>
  <script>
    document.querySelectorAll(".clickable-row").forEach(function(row) {{
      row.addEventListener("click", function(event) {{
        if (event.target.closest("a")) return;
        const href = row.getAttribute("data-href");
        if (href) window.location.href = href;
      }});
    }});
  </script>
</body>
</html>
"""


def render_card_detail_html(
    card: dict, analysis_link: str, attachments: list[tuple[str, str]]
) -> str:
    card_id = escape(str(card.get("id", "")))
    card_name = escape(str(card.get("name", "")))
    status = escape(str(card.get("status", "")))
    created_date = escape(str(card.get("created_date", "")))
    desc = escape(str(card.get("description", "")))
    members = card.get("members") or []
    comments = card.get("comments") or []

    members_items = []
    for member in members:
        full_name = escape(str((member or {}).get("full_name") or "Sin nombre"))
        username = escape(str((member or {}).get("username") or "sin_usuario"))
        members_items.append(
            f'<li><span class="member-name">{full_name}</span> '
            f'<span class="member-user">(@{username})</span></li>'
        )
    members_html = "".join(members_items) or '<li class="muted">Sin miembros asignados.</li>'

    comments_items = []
    for comment in comments:
        member = (comment or {}).get("member") or {}
        full_name = escape(str(member.get("full_name") or "Sin nombre"))
        username = escape(str(member.get("username") or "sin_usuario"))
        date = escape(str((comment or {}).get("date") or ""))
        text = escape(str((comment or {}).get("text") or ""))
        comments_items.append(
            f'<li class="comment-item"><div class="comment-meta">{full_name} (@{username})'
            f' · <span class="mono">{date}</span></div><div>{text or "(Sin texto)"}</div></li>'
        )
    comments_html = "".join(comments_items) or '<li class="muted">Sin comentarios.</li>'

    analysis_href = escape(analysis_link, quote=True)
    resource_buttons = [
        f'<a class="resource-btn attachment-link" href="{analysis_href}" data-src="{analysis_href}">Análisis (.md)</a>'
    ]
    for name, href in attachments:
        safe_href = escape(href, quote=True)
        safe_name = escape(name)
        resource_buttons.append(
            f'<a class="resource-btn attachment-link" href="{safe_href}" data-src="{safe_href}">{safe_name}</a>'
        )
    resources_html = "".join(resource_buttons)

    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{card_name} - SIDOT Trello Card</title>
  <style>
    :root {{
      --bg: #f8fafc;
      --text: #111827;
      --muted: #6b7280;
      --line: #e5e7eb;
      --card: #ffffff;
      --accent: #0b6ff0;
      --secondary: #475569;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: var(--text);
      background: var(--bg);
    }}
    .wrap {{ width: 100%; min-height: 100vh; margin: 0; padding: 0; }}
    .panel {{
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 0;
      box-shadow: none;
      padding: 20px;
      min-height: 100vh;
    }}
    .detail-grid {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 42%;
      gap: 20px;
      align-items: start;
    }}
    .topbar {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 12px;
      margin-bottom: 10px;
    }}
    .top-actions {{
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }}
    .left-column {{ min-width: 0; }}
    .right-column {{
      border: 1px solid var(--line);
      border-radius: 10px;
      background: #fff;
      min-height: 620px;
      overflow: hidden;
      position: sticky;
      top: 10px;
    }}
    .viewer-head {{
      padding: 10px 12px;
      border-bottom: 1px solid var(--line);
      background: #f8fafc;
      color: #334155;
      font-size: 0.9rem;
      font-weight: 600;
    }}
    .viewer-frame {{
      width: 100%;
      height: calc(100vh - 90px);
      min-height: 560px;
      border: 0;
      background: #fff;
    }}
    h1 {{ margin: 0 0 10px; font-size: 1.35rem; }}
    .row {{ margin: 8px 0; }}
    .label {{ color: var(--muted); font-size: 0.9rem; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
    .desc {{
      margin-top: 16px;
      padding: 12px;
      border: 1px dashed var(--line);
      border-radius: 10px;
      color: #1f2937;
      background: #fbfdff;
      white-space: pre-wrap;
    }}
    .info-box {{
      margin-top: 16px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: #ffffff;
    }}
    .info-box h3 {{
      margin: 0 0 8px;
      font-size: 1rem;
      color: #334155;
    }}
    .simple-list {{
      margin: 0;
      padding-left: 20px;
    }}
    .simple-list li {{
      margin: 6px 0;
    }}
    .member-name {{
      font-weight: 600;
    }}
    .member-user {{
      color: #475569;
    }}
    .comment-item {{
      padding: 8px 0;
      border-top: 1px dashed #e2e8f0;
    }}
    .comment-item:first-child {{
      border-top: 0;
      padding-top: 0;
    }}
    .comment-meta {{
      color: #334155;
      font-size: 0.9rem;
      margin-bottom: 4px;
    }}
    .muted {{
      color: var(--muted);
    }}
    .analysis {{
      margin-top: 16px;
      padding: 14px;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: #ffffff;
      line-height: 1.5;
    }}
    .analysis h1, .analysis h2, .analysis h3 {{ margin-top: 0.8em; }}
    .analysis pre {{
      overflow-x: auto;
      background: #f1f5f9;
      border-radius: 8px;
      padding: 10px;
    }}
    .analysis code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 0.9em;
    }}
    .analysis .loading {{ color: var(--muted); }}
    .analysis .error {{
      color: #b91c1c;
      background: #fef2f2;
      border: 1px solid #fecaca;
      border-radius: 8px;
      padding: 10px;
    }}
    .resources {{
      margin-top: 16px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: 10px;
      background: #f8fafc;
    }}
    .resources h3 {{
      margin: 0 0 8px;
      font-size: 1rem;
      color: #334155;
    }}
    .resource-grid {{
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }}
    .resource-btn {{
      display: inline-block;
      text-decoration: none;
      padding: 7px 10px;
      border-radius: 8px;
      border: 1px solid #bfdbfe;
      background: #eaf2ff;
      color: #0c4a9a;
      font-size: 0.9rem;
      font-weight: 600;
      max-width: 100%;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }}
    .resource-btn:hover {{
      background: #dbeafe;
    }}
    .btn {{
      text-decoration: none;
      border-radius: 8px;
      padding: 8px 12px;
      font-weight: 600;
      font-size: 0.92rem;
    }}
    .btn-primary {{ background: var(--accent); color: #fff; }}
    .btn-secondary {{ background: #e2e8f0; color: var(--secondary); }}
    @media (max-width: 980px) {{
      .detail-grid {{
        grid-template-columns: 1fr;
      }}
      .right-column {{
        position: static;
      }}
      .viewer-frame {{
        height: 60vh;
        min-height: 420px;
      }}
      .topbar {{
        flex-direction: column;
      }}
      .top-actions {{
        width: 100%;
        justify-content: flex-start;
      }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <section class="panel">
      <div class="detail-grid">
        <div class="left-column">
          <div class="topbar">
            <h1>{card_name}</h1>
            <div class="top-actions">
              <a class="btn btn-primary attachment-link" href="{analysis_href}" data-src="{analysis_href}">Abrir análisis (.md)</a>
              <a class="btn btn-secondary" href="index.html">Volver al listado</a>
            </div>
          </div>
          <div class="row"><span class="label">ID:</span> <span class="mono">{card_id}</span></div>
          <div class="row"><span class="label">Estado:</span> {status or "N/A"}</div>
          <div class="row"><span class="label">Fecha:</span> {created_date}</div>
          <div class="desc">{desc or "Sin descripción resumida."}</div>
          <div class="info-box">
            <h3>Miembros Asignados</h3>
            <ul class="simple-list">
              {members_html}
            </ul>
          </div>
          <div class="info-box">
            <h3>Comentarios</h3>
            <ul class="simple-list">
              {comments_html}
            </ul>
          </div>
          <div class="resources">
            <h3>Recursos</h3>
            <div class="resource-grid">
              {resources_html}
            </div>
          </div>
          <div class="analysis" id="analysis-root">
            <div class="loading">Cargando análisis Markdown...</div>
          </div>
        </div>
        <aside class="right-column">
          <div class="viewer-head">Visor de adjuntos</div>
          <iframe id="attachment-viewer" class="viewer-frame" title="Visor de adjuntos"></iframe>
        </aside>
      </div>
    </section>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <script>
    (function() {{
      const analysisPath = "{analysis_href}";
      const root = document.getElementById("analysis-root");
      function renderError(message) {{
        root.innerHTML = '<div class="error">' + message + '</div>';
      }}
      fetch(analysisPath)
        .then(function(resp) {{
          if (!resp.ok) throw new Error('HTTP ' + resp.status);
          return resp.text();
        }})
        .then(function(md) {{
          if (!window.marked) throw new Error('marked.js no cargada');
          root.innerHTML = window.marked.parse(md);
        }})
        .catch(function(err) {{
          renderError('No se pudo cargar el análisis Markdown. Error: ' + err.message);
        }});

      const viewer = document.getElementById("attachment-viewer");
      const links = Array.from(document.querySelectorAll(".attachment-link"));
      function escapeHtml(text) {{
        return String(text)
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;");
      }}
      function renderInIframe(title, bodyHtml) {{
        if (!viewer) return;
        const doc = `<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>${{title}}</title>
<style>
body {{ margin: 0; font-family: Segoe UI, Roboto, Helvetica, Arial, sans-serif; color: #111827; }}
.wrap {{ padding: 14px; }}
h1 {{ margin: 0 0 10px; font-size: 1rem; color: #334155; }}
pre {{ white-space: pre-wrap; word-break: break-word; background: #f8fafc; border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px; }}
code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }}
</style></head><body><div class="wrap"><h1>${{title}}</h1>${{bodyHtml}}</div></body></html>`;
        viewer.srcdoc = doc;
      }}
      function openInViewer(src) {{
        if (!src || !viewer) return;
        const lower = src.toLowerCase().split("?")[0];
        if (lower.endsWith(".md") || lower.endsWith(".txt")) {{
          fetch(src)
            .then(function(resp) {{
              if (!resp.ok) throw new Error("HTTP " + resp.status);
              return resp.text();
            }})
            .then(function(text) {{
              if (lower.endsWith(".md")) {{
                if (!window.marked) throw new Error("marked.js no cargada");
                renderInIframe(src, window.marked.parse(text));
              }} else {{
                renderInIframe(src, "<pre>" + escapeHtml(text) + "</pre>");
              }}
            }})
            .catch(function() {{
              viewer.removeAttribute("srcdoc");
              viewer.setAttribute("src", src);
            }});
          return;
        }}
        viewer.removeAttribute("srcdoc");
        viewer.setAttribute("src", src);
      }}
      links.forEach(function(link) {{
        link.addEventListener("click", function(event) {{
          event.preventDefault();
          const src = link.getAttribute("data-src");
          openInViewer(src);
        }});
      }});

      if (links.length > 0 && viewer) {{
        openInViewer(links[0].getAttribute("data-src"));
      }}
    }})();
  </script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate static HTML from doc/.trello/cards.json."
    )
    parser.add_argument(
        "--project-root",
        default=str(Path.cwd().resolve()),
        help="Project root path (default: current working directory).",
    )
    parser.add_argument(
        "--cards-json",
        default="doc/.trello/cards.json",
        help="Path to cards.json relative to project root.",
    )
    parser.add_argument(
        "--out-dir",
        default="doc/.trello/cards-ui",
        help="Output directory for static HTML files, relative to project root.",
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    cards_json_path = (project_root / args.cards_json).resolve()
    out_dir = (project_root / args.out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    cards = load_cards(cards_json_path)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    active_detail_files = set()
    for card in cards:
        card_id = str(card.get("id", "")).strip()
        if not card_id:
            continue
        active_detail_files.add(f"card_{card_id}.html")

    # Remove stale card detail pages that no longer exist in cards.json.
    for path in out_dir.glob("card_*.html"):
        if path.name not in active_detail_files:
            path.unlink()

    index_html = render_index_html(cards, generated_at)
    (out_dir / "index.html").write_text(index_html, encoding="utf-8")

    for card in cards:
        card_id = str(card.get("id", "")).strip()
        if not card_id:
            continue
        md_link = str(card.get("md_link", "")).strip()
        analysis_link = to_relative_analysis_link(project_root, out_dir, md_link)
        attachments = collect_attachment_links(project_root, out_dir, md_link)
        detail_html = render_card_detail_html(card, analysis_link, attachments)
        (out_dir / f"card_{card_id}.html").write_text(detail_html, encoding="utf-8")

    print(f"Generated {len(cards)} card pages in {out_dir}")
    print(f"Open: {out_dir / 'index.html'}")


if __name__ == "__main__":
    main()
