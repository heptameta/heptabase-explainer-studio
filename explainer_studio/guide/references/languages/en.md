# Language: English (en)

Load this when the narration is English. Length is counted in **words**.

## 1. Speaking rate and length

- 3b1b runs at about 180 to 195 wpm (counting silent animation time). A comfortable rate for English explanation is
  about **150 to 170 wpm**; slow down for mathematics and passages dense with new concepts.
- The tools estimate length with a rate per voice: OpenAI `gpt-4o-mini-tts` about 170 wpm, macOS `say` (Samantha) about
  175 wpm, other voices 165. `script validate` uses it to warn when an episode will run well under the plan's length,
  and `preview` uses it for beats not yet narrated.
- Limits: 32 words per beat (`script validate` warns above it). About 3,400 words per episode (roughly 20 minutes) is a
  safe ceiling for narration cost, not a length target; `script validate` warns above it, and a longer plan simply goes
  past it. Each episode's length comes from the plan's `estimated_duration_seconds`; when the user named a length, the
  plan uses it.

## 2. Sentences

- Write speech, not prose: contractions are fine (it's, doesn't, we'll), and one sentence carries one new idea.
- Mix long and short: a long sentence of up to 25 words, followed by a short one such as "That's odd." or "And it
  works."
- Put the subject first; do not make the viewer wait until the end of the sentence to know what it is about.
- Avoid stock phrases such as "In this video, we will…", "Let's dive in", "delve" and "it's important to note"; start
  straight from something concrete.
- Mostly "you", with "we" for company (we'll see, let's try); never "the viewer" or "one".

## 3. Writing narration for the picture

- Every sentence can point at "this", "here" or "that line" on screen.
- Declare a colour once ("the blue one is the input"); after that just say "blue".
- When reading a formula, say what it means, not each symbol ("how fast f changes", not "d f d x"); the first time it
  appears, say both.

## 4. Terms and names

- A term gets one plain sentence the first time it appears; an abbreviation gets its full name the first time ("a large
  language model, an LLM").
- People's names use the usual English spelling and pronunciation. For a non-English name, set `spoken_text_override` on
  the beat where it first appears, with how to say it (section 8).

## 5. Saying mathematics (with the mathematics subject reference)

- x² is "x squared"; xⁿ is "x to the n"; √2 is "root two"; Σ is "the sum over…"; ∫ is "the integral of… from… to…".
- A fraction is "a over b"; a decimal is "zero point five"; a very large number is said rounded ("about one point four
  billion"), never as a long string of digits.
- `narrate` already turns ² and ³ into "squared" and "cubed", Greek letters into their names, and a − before a number
  into "minus"; the subtitles keep the symbols.

## 6. Subtitles

- One subtitle per beat; the player wraps lines itself. When a subtitle runs past two lines (about 84 characters), split
  the beat into two.
- Subtitles match the narration text exactly (`spoken_text_override` changes only what the voice reads, never the
  subtitles).

## 7. Quotations

- For an original not in English, give an English translation first, with the original beside it on screen
  (`scene_kit`'s `get_quote_pair`). Say whose translation it is (the translator, or "our translation").

## 8. Narration voices

- **Paid narration with ElevenLabs (the default):** the plan's `narration` is
  `{provider_name: elevenlabs, voice_id: JBFqnCBsd6RMkjVDRZzb}` (George). The model defaults to `eleven_v4`, the most
  expressive; do not set an older model. The plan page lists other voices; another Voice Library voice works by its id.
- **Paid narration with OpenAI:** `{provider_name: openai, model: gpt-4o-mini-tts, voice: ash}`, with `instructions`
  asking for a warm, curious voice, not a newsreader's.
- **Trying things for free:** `{provider_name: macos-say}` (macOS only, Samantha, mechanical). Use it only to check
  pictures; anything meant to be watched uses a paid voice.
- **Changing what the voice reads, not the subtitles:** set `spoken_text_override` on that beat. Common uses: spelling
  abbreviations letter by letter (`LLM` → `L L M`), mathematical symbols, non-English names, heteronyms (read, lead).
- After narration, check the opening and the hardest passage first, especially numbers, abbreviations and names: read
  their spoken text in `narration/narration.yaml`, and redo any beat `narrate` flags for an odd speaking rate
  (`narrate <episode> --beats <id>`).

## 9. Measured conversions between words and length

- OpenAI `gpt-4o-mini-tts` (ash, speed 1.175, the default): about 170 wpm; marin reads faster, about 210. An 18 to
  20 minute episode with ash ≈ 3,000 to 3,400 words of narration.
- The video runs a little longer than the speech alone: there are pauses between beats and transitions between scenes
  (the tools' estimate includes them).

## 10. Fonts

- On-screen English uses `Text(...)`, which takes `scene_kit`'s video font (Noto Sans TC, which covers Latin too); code
  uses its monospace font; formulas use `Tex`. Keep one choice for the whole series and note it in the series bible.
- End credits: the page writes "Credits", and "Made with" over the Heptabase icon and name. A source line reads "Carl B. Boyer, A History of
  Mathematics (1968), chapters 19 and 20": the authors, the title, the year, then the part the episode covers. Name each picture by what it shows ("Portrait of Isaac Newton").

## 11. Sharing feedback

- Use the texts in `workflow/feedback.md` as they are.

## 12. Introducing the whiteboard

- Use the text in `guide.md` (Deliver) as it is.

## Self-check

- [ ] The narration was read through aloud: no long written-style sentences, no stock opening, every sentence points at
      something on screen.
- [ ] Abbreviations, mathematical symbols and non-English names have a `spoken_text_override` where needed, and were
      checked after narration.
- [ ] The estimated length (`script validate`) falls within the episode's length in the plan.
