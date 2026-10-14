# Reading books, articles and other text

**Kinds:** `essay`, `notes`, `popular`, `textbook`, `survey`, `monograph`, `primary`, `manual`, `literature`, `rules`,
`case`, `conversation`.

Use this when the source is a book (or a chapter), an article, lecture notes, a legal text, a case or an interview
transcript, and the video must cover it faithfully and completely. The steps below use a PDF as the example; for other
file formats, first get the content out as described in [sources/README.md](README.md).

## Where these kinds hide their questions

Where to look when drawing the question map during deep reading, and what to watch for when putting the source into
the video. This only helps you read; it does not decide how many episodes there are
([teaching/plan.md](../teaching/plan.md)).

| Kind | Where the questions and prerequisites usually are | When putting it into the video |
|---|---|---|
| Essay `essay` | The author's main line is the main question | Use the author's examples wherever possible |
| Notes and slides `notes` | Headings are usually the questions; the reasoning between them is often missing | Mark the reasoning you add as not from the original |
| Popular book `popular` | The big question is in the preface; each chapter is one step of the argument | The author's stories can serve as openings |
| Textbook `textbook` | Definitions, theorems, worked examples; prerequisites are often stated at the start of a chapter or in its exercises | Use the book's worked examples to let the viewer try it once |
| Survey `survey` | Topics rarely depend on each other; names and years are dense | Count the names and years when planning |
| Monograph `monograph` | The core argument is in the introduction and conclusion; the middle is evidence | Translate the jargon into plain words first |
| Primary source `primary` | Follows the author's own order of argument; many prerequisites are the historical background | Quote the original; give the historical background first, then say how it is seen today |
| Manual `manual` | One chapter teaches one thing you can do | The demonstration really does it once, completely |
| Literature `literature` | The reader's puzzle: why is this passage written this way? | Let the viewer read the passage itself first |
| Rules and texts of law `rules` | What situation each provision governs; how provisions refer to each other | Pair every provision with a case |
| Case `case` | The decision the people involved faced | Stop at the decision point first and let the viewer judge |
| Conversation `conversation` | Scattered across passages, often repeated | Use the speakers' own words and say who said each |

## Reading it in

- Extract the whole chapter as text (for example `pdftotext -layout`) and **read every page**. Never read only a
  summary.
- **Read the footnotes too:** they often hold the best anecdotes and historiographical debates, and are the source of
  "actually, that's not quite right" moments.
- For scanned pages, or pages whose text will not extract, read the page images directly.

## The coverage list

- List every argument, example, person, year and quotation, section by section, **with page numbers** (for a
  transcript, the time or paragraph). This is the basis of completeness.
- When a chapter is very long (for example over 70 pages), first split it into sections and list each one, then merge
  them into one coverage list.

## Verifying and quoting

- Check quotations, years and anecdotes against the book's page numbers, and mark them verified in the to-verify list.
- When quoting an author's own analysis, use only short phrases and say "X argues"; mostly paraphrase. When quoting a
  primary source, prefer the public-domain original, translate it yourself, and say so.
- Never scan pictures from a copyrighted book into the video.

The other kinds (papers, codebases, code changes, technical documents) each have their own guide; see
[sources/README.md](README.md).
