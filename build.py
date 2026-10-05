#!/usr/bin/env python3
"""Regenerate the publication list from INSPIRE-HEP.

    python3 build.py            # fetch, write publications.html, refresh index.html
    python3 build.py --offline  # rebuild from the cached data/publications.json

The list is fetched once and cached, so the site can be rebuilt without network.
Papers with a major contribution are flagged from LEAD_IDS below -- INSPIRE cannot
know that, so it is the one thing kept by hand. The set mirrors the "Publications
with a major contribution" list of the HDR manuscript; add an arXiv id there when a
new one lands. The home page shows the most recent of these flagged papers.
"""
import argparse
import html
import json
import re
import urllib.request
from pathlib import Path

INSPIRE_RECID = 1888974
API = (f"https://inspirehep.net/api/literature?q=authors.recid%3A{INSPIRE_RECID}"
       "&size=300&sort=mostrecent"
       "&fields=titles,arxiv_eprints,publication_info,earliest_date,document_type,authors")

LEAD_IDS = {
    "2004.01448", "2012.04008", "2203.07886", "2203.11045", "2306.06311", "2306.06316",
    "2310.09116", "2405.03447", "2407.04473", "2412.06892", "2501.16852", "2505.09493",
    "2507.00157", "2509.13593", "2601.11139", "2601.21432", "2602.03382", "2604.09407",
    "2609.34508",
}

# Typos in the upstream INSPIRE records. Reported there; corrected here meanwhile.
TITLE_FIXES = {
    "ZTF type Iasupernovae": "ZTF type Ia supernovae",
    "Kinematic Sunyae Zel'dovich": "Kinematic Sunyaev-Zel'dovich",
    "Eboss": "eBOSS",
    "Lymanα": "Lyman-α",
    "Ly α": "Lyα",
    "ACCEL2": "ACCEL²",
    "eBOSS—Stripe 82": "eBOSS Stripe 82",
}

# Key papers signed by the collaboration as a whole (as in the HDR publication list);
# INSPIRE lists them under the first alphabetical author instead.
COLLAB_PAPERS = dict.fromkeys(
    ["2205.10939", "2306.06307", "2306.06308", "2404.03000", "2404.03001", "2404.03002",
     "2411.12020", "2411.12021", "2411.12022", "2503.14738", "2503.14739", "2503.14745",
     "2607.27410"], "DESI Collaboration")
COLLAB_PAPERS["2007.08991"] = "eBOSS Collaboration"

# Same person, spelt two ways across INSPIRE records.
AUTHOR_FIXES = {"Karaçayli": "Karaçaylı"}

ROOT = Path(__file__).parent
CACHE = ROOT / "data" / "publications.json"
N_RECENT = 6


def fetch():
    with urllib.request.urlopen(API, timeout=60) as r:
        data = json.load(r)
    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(data, indent=1))
    return data


def tex_to_html(s):
    """INSPIRE titles carry TeX fragments and, for journal versions, MathML; render both."""
    s = re.sub(r"<math[^>]*>(.*?)</math>", lambda m: re.sub(r"<[^>]+>", "", m.group(1)), s, flags=re.S)
    s = re.sub(r"\$?\\?alpha\$?", "α", s)
    s = re.sub(r"\$\\?beta\$", "β", s)
    s = re.sub(r"\$\\?sigma_?8?\$", "σ₈", s)
    s = " ".join(s.replace("$", "").replace("\\", "").split())
    for wrong, right in TITLE_FIXES.items():
        s = s.replace(wrong, right)
    return html.escape(s)


def journal(rec):
    pub = (rec.get("publication_info") or [{}])[0]
    title = pub.get("journal_title")
    if not title:
        return "preprint"
    bits = [title.replace(".", ". ").strip()]
    if pub.get("journal_volume"):
        bits.append(pub["journal_volume"])
    if pub.get("year"):
        bits.append(f"({pub['year']})")
    page = pub.get("artid") or pub.get("page_start")
    if page:
        bits.append(str(page))
    return " ".join(bits)


def parse(data):
    out = []
    for hit in data["hits"]["hits"]:
        m = hit["metadata"]
        if "thesis" in (m.get("document_type") or []):
            continue
        eid = (m.get("arxiv_eprints") or [{}])[0].get("value", "")
        authors = m.get("authors") or []
        out.append(dict(
            year=(m.get("earliest_date") or "")[:4],
            title=tex_to_html(m["titles"][0]["title"]),
            arxiv=eid,
            journal=journal(m),
            n_authors=len(authors),
            corporate=COLLAB_PAPERS.get(eid, ""),
            first=AUTHOR_FIXES.get(*[authors[0]["full_name"].split(",")[0]] * 2) if authors else "",
            lead=eid in LEAD_IDS,
        ))
    return out


def entry_html(p, repeat_year=False):
    link = f"https://arxiv.org/abs/{p['arxiv']}" if p["arxiv"] else "#"
    meta = p["journal"]
    if p["corporate"]:
        meta += f" · {p['corporate']} ({p['n_authors']} authors)"
    elif p["n_authors"] > 12:
        meta += f" · {p['first']} et al. ({p['n_authors']} authors)"
    elif p["first"]:
        meta += f" · {p['first']} et al."
    if p["arxiv"]:
        meta += f" · arXiv:{p['arxiv']}"
    return (f'    <li class="pub{" pub--lead" if p["lead"] else ""}">\n'
            f'      <span class="pub__year{" pub__year--repeat" if repeat_year else ""}">{p["year"]}</span>\n'
            f'      <span><a class="pub__title" href="{link}">{p["title"]}</a>\n'
            f'        <span class="pub__meta">{html.escape(meta)}</span></span>\n'
            f'    </li>')


def write_publications(pubs):
    lead = sum(p["lead"] for p in pubs)
    years = [p["year"] for p in pubs]
    body = "\n".join(entry_html(p, repeat_year=i > 0 and years[i - 1] == p["year"])
                     for i, p in enumerate(pubs))
    page = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Publications, Corentin Ravoux</title>
<meta name="description" content="Publication list of Corentin Ravoux, CNRS researcher at the Laboratoire de Physique de Clermont Auvergne (LPCA).">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,300;0,6..72,400;1,6..72,400&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<link rel="canonical" href="https://corentinravoux.github.io/publications.html">
<meta property="og:type" content="website">
<meta property="og:title" content="Publications, Corentin Ravoux">
<meta property="og:description" content="Full publication list of Corentin Ravoux, CNRS researcher at the Laboratoire de Physique de Clermont Auvergne, generated from INSPIRE-HEP.">
<meta property="og:url" content="https://corentinravoux.github.io/publications.html">
<meta property="og:image" content="https://corentinravoux.github.io/assets/img/cosmic-web.jpg">
<meta property="og:site_name" content="Corentin Ravoux">
<meta name="twitter:card" content="summary_large_image">
<meta name="author" content="Corentin Ravoux">
<meta name="theme-color" content="#060d18">
<link rel="stylesheet" href="assets/css/site.css">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'><circle cx='16' cy='16' r='9' fill='none' stroke='%2386e0b4' stroke-width='2'/><circle cx='16' cy='16' r='2' fill='%23f77f00'/></svg>">
</head>
<body>
<a class="skip" href="#list">Skip to the list</a>
<main class="page page--plain">
  <section aria-labelledby="pubs-title">
    <div class="wrap">
      <a class="link-quiet" href="index.html">Back to the home page</a>
      <h1 id="pubs-title">Publications</h1>
      <p>{len(pubs)} papers, {lead} of them with a major contribution from me, marked
        <span class="mark-lead">●</span>. The list is generated from INSPIRE-HEP and includes
        collaboration papers.</p>
      <div class="actions">
        <a class="btn" href="https://inspirehep.net/authors/{INSPIRE_RECID}">INSPIRE-HEP</a>
        <a class="btn" href="https://scholar.google.com/citations?user=qcvRqBAAAAAJ">Google Scholar</a>
        <a class="btn" href="https://arxiv.org/a/ravoux_c_1">arXiv</a>
      </div>
      <div class="filter" role="group" aria-label="Filter the list" hidden>
        <button type="button" aria-pressed="true" data-filter="all">All papers ({len(pubs)})</button>
        <button type="button" aria-pressed="false" data-filter="lead">Major contribution ({lead})</button>
      </div>
      <ul class="pubs" id="list">
{body}
      </ul>
    </div>
  </section>
</main>
<script>
  // Filter between all papers and the major-contribution ones. Hidden without JS.
  (function () {{
    var group = document.querySelector(".filter"), list = document.getElementById("list");
    if (!group || !list) return;
    group.hidden = false;
    group.addEventListener("click", function (e) {{
      var b = e.target.closest("button");
      if (!b) return;
      group.querySelectorAll("button").forEach(function (x) {{ x.setAttribute("aria-pressed", String(x === b)); }});
      list.classList.toggle("pubs--lead-only", b.dataset.filter === "lead");
    }});
  }})();
</script>
</body>
</html>
"""
    (ROOT / "publications.html").write_text(page)


def refresh_index(pubs):
    index = ROOT / "index.html"
    text = index.read_text()
    recent = "\n".join(entry_html(p) for p in [p for p in pubs if p["lead"]][:N_RECENT])
    block = f'<!-- RECENT-PUBS -->\n      <ul class="pubs">\n{recent}\n      </ul>\n      <!-- /RECENT-PUBS -->'
    if "<!-- /RECENT-PUBS -->" in text:
        text = re.sub(r"<!-- RECENT-PUBS -->.*?<!-- /RECENT-PUBS -->", block, text, flags=re.S)
    else:
        text = text.replace("<!-- RECENT-PUBS -->", block)
    index.write_text(text)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--offline", action="store_true", help="use data/publications.json")
    args = ap.parse_args()

    raw = json.loads(CACHE.read_text()) if args.offline else fetch()
    print(f"{raw['hits']['total']} INSPIRE records")
    pubs = parse(raw)
    write_publications(pubs)
    refresh_index(pubs)
    missing = LEAD_IDS - {p["arxiv"] for p in pubs}
    if missing:
        print("LEAD_IDS not found on INSPIRE:", sorted(missing))
    print(f"{len(pubs)} publications ({sum(p['lead'] for p in pubs)} major contribution) "
          f"-> publications.html, index.html refreshed")
