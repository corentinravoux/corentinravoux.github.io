# corentinravoux.github.io

Personal research site, served at <https://corentinravoux.github.io>.

Static HTML/CSS with one small script. No framework, no build step for the pages
themselves: GitHub Pages serves the files as they are.

## Layout

```
index.html            home: about, research, software, recent papers, contact
publications.html     full publication list (generated, do not edit by hand)
build.py              regenerates publications.html + the list inside index.html
data/publications.json  cached INSPIRE-HEP response
assets/css/site.css   the whole stylesheet
assets/js/rail.js     highlights the redshift tick of the section in view
assets/img/           images (see below)
```

## The two images to add

The design expects these files; the page degrades gracefully without them, so add
them whenever you like:

| file | what | used where |
|---|---|---|
| `assets/img/cosmic-web.jpg` | the dark-matter field image | hero background |
| `assets/img/portrait.jpg` | portrait photo, square-ish crop | about section |
| `assets/img/fsigma8.png` | fσ8 figure (already in) | research section |

## Updating the publications

```bash
python3 build.py             # fetch from INSPIRE, rewrite both pages
python3 build.py --offline   # rebuild from the cached JSON, no network
```

INSPIRE cannot know which papers carry a major contribution from you, so that stays
by hand: `LEAD_IDS` in `build.py` mirrors the "Publications with a major
contribution" list of the HDR manuscript. Those entries get the ● mark, and the home
page shows the six most recent of them. Upstream typos in INSPIRE titles are patched
through `TITLE_FIXES` (MathML in journal titles is stripped automatically), and
collaboration-signed papers are labelled through `COLLAB_PAPERS`.

## Design notes

The left rail is a redshift axis: the sections run from z = 0 (peculiar velocities,
the local Universe) through the BAO and the Lyman-α tomographic map (z ≈ 2.5) to the
one-dimensional power spectrum (z ≈ 2.2–4.2), which is the range the work actually
spans. Every number in the research sections is taken from the HDR manuscript or the
abstract of the paper it links to. Colours are sampled from the simulation image in the hero, with a
single warm accent reused from the f(R) curves in the growth figures.

Fonts are Newsreader (display), IBM Plex Sans (body) and IBM Plex Mono (labels),
loaded from Google Fonts.
