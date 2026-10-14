# Reading papers (PDF, arXiv, LaTeX)

**Kind:** `paper`.

Use this when the source is a research paper (or a link to one, or an arXiv number).

## Where the questions usually are

| Kind | Where the questions and prerequisites usually are | When putting it into the video |
|---|---|---|
| Paper `paper` | The abstract and introduction state the claim; the figures and tables are the evidence; the methods section is often a mechanism | Look for a web version first; use the paper's own figures |

A paper often has both an argument (does this claim hold?) and a mechanism (how does the new method work?). Draw both on
the question map; which one is the main question depends on the viewer's goal ([teaching/plan.md](../teaching/plan.md)).

## Reading it in

0. **Look for a web version first.** Many papers have an HTML version (arXiv's HTML version, Distill,
   transformer-circuits.pub, the publisher's page). On the web, formulas are LaTeX source and figures are complete
   originals; a PDF printed from a web page often has its right side cut off and its sub- and superscripts scattered.
   If you find one, work mainly from the web version, with the PDF as backup. If you cannot, and the PDF looks printed
   from a web page, find out during the probes whether the user has a web version. If they have none either, look at
   the page images one by one: where formulas and tables are complete on the page image, you need nothing else.
1. **Confirm the version:** the title, authors and year on the PDF, and whether it is a preprint. Note the arXiv number
   as the source when there is one.
2. **Text:** extract the full text (for example `pdftotext -layout`) as the skeleton.
3. **Formulas and figures:** text extraction scrambles formulas and figures. **Read the pages with formulas, figures and
   tables as page images**; never understand a formula from extracted text alone. First run
   `explainer-studio asset pdf draw-page-thumbnail-sheets <pdf>` for thumbnails of every page (six to a page thumbnail
   sheet), pick the pages with figures and formulas, then read them closely. When the LaTeX source (for example arXiv's
   source files) or a web version exists, its formulas are the authority.
4. **Reading order:** abstract and conclusion → introduction (the contributions the authors claim) → core method → key
   experiments → limitations and discussion → appendices, skimmed and read deeply only when needed. Before probing the
   viewer, skim only enough to pick probes (original sentences, depth probes).

## The coverage list

- Each item cites its source down to **section, figure or table, and page** (for example §3.2, Fig. 4, p. 12).
- Also make two lists:
  - **The contributions the authors claim** (usually at the end of the introduction), each marked with whether it has
    matching evidence (which experiment, which figure).
  - **Key figures and tables:** those the video might use, each with one sentence on what it proves.
- For a long paper, most coverage-map items will be depth C or in `excluded_topics`. That is normal: an episode answers
  only one main question.

## Using the paper's figures

- Cut a figure out with `explainer-studio asset pdf crop <pdf> --page <n> --box x0,y0,x1,y1`: first look at the whole
  page without `--box`, then frame the figure with proportional coordinates from 0 to 1.
- Put it on screen with `scene_kit`'s `get_paper_figure(...)`, with the figure number and a small source line.
- **Licence:** check the paper's licence (the arXiv page usually shows it, for example CC BY). Credit every figure the
  video uses (add an entry to `production/credits.yaml`); when the licence is unclear, redraw the figure from the
  original and say so.

## Verifying

- Check every number, conclusion and experimental setting against the original, and mark it verified in the to-verify
  list.
- Keep apart what the authors claim, what the evidence supports, and your interpretation. The gaps the authors admit in
  their limitations and discussion go into the coverage list.
