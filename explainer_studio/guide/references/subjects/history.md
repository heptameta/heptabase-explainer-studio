# Subject: history

Use this whenever any presenter covers history, people or primary sources. It was taken out of Theo's playbook for
conceptual change ([presenters/theo/question-types/conceptual-change.md](../presenters/theo/question-types/conceptual-change.md)):
portrait cards, quotations from primary sources, historical honesty and how to say people's names hold whoever presents
history.

## Portrait cards (T10)

- A small engraving or photograph (35 to 60% of the frame height when alone, about 20% when three stand in a column),
  with a thin light-grey frame (`scene_kit`'s `get_portrait_card`).
- Below it, the name in serif (in the original), then the name in the narration language, then the years of birth and
  death on a smaller line.
- **Above the portrait, their key formula or one sentence of theirs, with an arrow pointing at what that idea later
  became** (for example "How it started / How it's going").
- The frame and the name take the colour of their school (see the series bible).
- Portraits use only public-domain images (engravings and photographs from before 1926 on Wikimedia Commons;
  `explainer-studio asset wikipedia download-portrait` keeps only public-domain and CC0 images). The source and licence
  go in `production/credits.yaml`, and a very small credit sits in the bottom-right corner of the frame. **Never scan
  pictures from a copyrighted book.** How portraits are used across a series is in the rendering references
  ([rendering/assets.md](../rendering/assets.md)).

## Texts and quotations

**The text is an object, and then it is extracted** (the most important device):

1. On the commentary layer, show a public-domain scan of the primary source's first page (Riemann 1854, Dedekind 1872,
   Hilbert 1899...) for 3 to 8 seconds.
2. Zoom in on one line and put a yellow box around it.
3. Pull that line out into typeset text: **the original small and grey above, the translation in the narration language
   large below** (`scene_kit`'s `get_quote_pair`).
4. **Transform the sentence into the mathematical object it describes** (for example Dedekind's "cut the line into two
   parts" → a real cut on the number line).
5. Give the source in very small text in the bottom-right corner.

Other rules:

- **One to three quotations from primary sources per episode**, each at most 2 lines of on-screen text. One "anchor
  quotation" can be raised in the opening and answered at the close, like Wigner in the π video.
- Show a quotation as the top of a notebook page (a real hand and paper, in split screen with the animation), or as a
  1 to 2 line caption right above the picture it inspired. **Never a full-screen quotation slide.**
- Colour the key words in a quotation with concept colours, to show which side the author leans to.
- Quoting an author's own words: use only short phrases and say "the author argues"; prefer paraphrase.
  Quoting a primary source: prefer the public-domain original, translate it yourself, and say so.

## Historical honesty

This takes the place of the "named omissions" in physics videos.

- **Discount legends:** "It is said that...", "Poincaré himself recalled it this way in 1908...".
- **Warn about anachronism:** "At the time, 'set' did not yet mean what it means in your textbook", "The word
  'injective' did not exist yet; Dedekind said 'similar'".
- **Separate the author's argument from the consensus:** "The author argues that...", "An earlier view (for example
  Birkhoff's) held that the Erlangen Program was deeply influential; more recent research (Hawkins, Scholz) holds that
  it had almost no influence at the time." A historiographical debate like this is a ready-made "actually, that's not
  quite right" moment.
- **A discovery fiction** (reconstructing someone's possible line of thought) is allowed only with a clear statement that
  "this is not the real historical path".
- **Verification:** every anecdote, year and quotation is marked verified in the to-verify list of the research notes;
  quotations are checked against the book's page numbers. A common slip: the smoke-ring experiment is often credited to
  Kelvin; it is usually attributed to Tait.

## How names are said

When a person, a book title or a term first appears, the narration uses the name in the narration language, and the
screen shows that name plus the original, with the years of birth and death. The translation table is in the series
bible. Language-specific details are in the language reference ([languages/](../languages/)).
