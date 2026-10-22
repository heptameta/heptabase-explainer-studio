# Language: Chinese (Taiwan, zh-TW)

Contents: [Speaking rate and length](#1-speaking-rate-and-length) · [Sentences](#2-sentences) ·
[Narration for the picture](#3-writing-narration-for-the-picture) · [Terms and names](#4-terms-and-names) ·
[Saying mathematics](#5-saying-mathematics-with-the-mathematics-subject-reference) · [Subtitles](#6-subtitles) ·
[Quotations](#7-translating-quotations) · [Narration voices](#8-narration-voices) ·
[Characters and length](#9-measured-conversions-between-characters-and-length) · [Fonts](#10-fonts) ·
[Sharing feedback](#11-sharing-feedback) · [Introducing the whiteboard](#12-introducing-the-whiteboard) ·
[Self-check](#self-check)

Load this when the narration is Traditional Chinese for Taiwan. Carry 3b1b's spoken English style into Chinese by
rewriting it, not translating it. The aim: sound like a Taiwanese teacher who is very good at teaching, talking to you
face to face: precise, spoken, warm, with no translationese. (Written for a mathematics series first; for another
subject, replace "a mathematics teacher" with a good teacher of that subject.)

Length is counted in characters.

## 1. Speaking rate and length

- 3b1b in English is about 180 to 195 wpm. A comfortable rate for Chinese explanation is about **230 to 260 characters
  per minute** (news reading is about 250 to 280; mathematics should be a little slower).
- The tools estimate length with a rate per voice: VoAI about 312 characters per minute, macOS `say` about 250, other
  voices 300. `script validate` uses it to warn when an episode will run well under the plan's length, and `preview`
  uses it for beats not yet narrated.
- Rough guide: **a 20-minute episode ≈ 4,600 to 5,200 characters** of narration (pauses included); 15 minutes ≈ 3,500 to
  3,900; 25 minutes ≈ 5,800 to 6,500.
- Leave a 0.5 to 1 second pause before and after a key sentence: give the key sentence a beat of its own, and set
  `pause_duration_seconds` on it and on the beat before it.
- **Measured:** VoAI 子墨 (Neo model, style 穩健, speed 1.0) reads about **310 characters per minute**. With it, an 18 to
  20 minute episode ≈ 5,500 to 6,000 characters of narration.

## 2. Sentences

- **One idea per sentence.** Long sentences are harder to follow by ear in Chinese than in English: keep a sentence to
  40 characters or fewer, and split anything longer. (`script validate` warns when a beat is over 60.)
- Keep 3b1b's rhythm of a long sentence followed by a short punch: 「……這就是 Dedekind 的想法。很簡單。簡單到有點可疑。」
- Spoken particles in moderation: 「其實」「你看」「換句話說」「好，」「那麼問題來了」. At most one or two per passage; never let
  them become a verbal tic.
- Ask guesses and questions the way a person talks: 「你覺得……？」「會不會……？」. Never open with 「先押」「先猜猜看」「押一個」:
  they sound like commands.
- Avoid stacking written connectives (「然而」「因此」「此外」 in a row); use the spoken 「可是」「所以」「而且」.
- **Avoid 「顯然」「易知」「不難看出」.**
- Mostly the second person 「你」; use 「我們」 when deriving something together.
- Questions should really sound like questions: 「你覺得呢？」「先停一下，你會怎麼定義？」

## 3. Writing narration for the picture

- Demonstratives must match the picture: 「這條線」「左邊這一堆藍色的點」「注意這裡的指數」.
- Say a colour only when you first declare it: 「接下來，藍色都代表有理數。」 After that, no need to say it again.
- The narration does not read out every word on screen. Text on screen is the anchor; the narration is the explanation.

## 4. Terms and names

- **One translation table for the whole series** (in the series bible). At first appearance, the narration says the
  Chinese and the screen shows Chinese plus the original (for example 戴德金分割 Dedekind cut). Afterwards the narration can
  use the Chinese alone.
- Follow the translations current in Taiwan for the subject. Each series' table is in its series bible.
- People's names: use the usual translation; the screen shows the original and the years of birth and death at first
  appearance. For example 克萊因（Felix Klein）、戴德金（Richard Dedekind）、希爾伯特（David Hilbert）. List uncertain
  translations as undecided in the series bible.
- Foreign book and paper titles: the narration says a Chinese rendering of the meaning; the screen shows the original
  (italic) plus the Chinese. For example 《數是什麼？數應該是什麼？》*Was sind und was sollen die Zahlen?*
- A paper's names kept on screen only (`teaching/rules.md`): the original plus one Chinese line, for example
  「QK 迴路：看哪裡」.

## 5. Saying mathematics (with the mathematics subject reference)

- Say what it means, not each symbol: `q² < 2` → 「q 的平方小於 2」; `(A | B)` → 「A 跟 B 這一刀」 (the first time, you can
  say 「記作 A 豎線 B」).
- Set-builder notation: `{q ∈ ℚ : q² < 2}` → 「所有平方小於 2 的有理數」.
- Greek letters: ω is read 「omega」, ℵ 「aleph」, ε 「epsilon」 (Taiwanese classrooms use the English names). Paid voices
  swallow symbols they cannot read (σ, μ and σ² have all come out as silence). So `narrate` rewrites the narration
  automatically before synthesis: Greek letters become their English names, ² and ³ become 「平方」「立方」, a − before a
  number becomes 「負」, any other − becomes 「減」. The subtitles keep the symbols. Write symbols in the narration as
  usual.
- Numbers: voices often misread large numbers, so write large numbers in Chinese in the narration (「一千七百五十億」).
  Write years in Arabic numerals: `narrate` reads a year from 1500 to 2099 digit by digit (1872 → 一八七二). Check a
  sample after narration.
- A long formula: first say what it says, then let the picture light up term by term while the narration explains each
  term.

## 6. Subtitles

- `render` makes the subtitles from the beat text and breaks Chinese lines at punctuation. When a beat is over about 40
  characters its subtitle gets too long: another reason to keep beats short.
- Subtitles use Traditional Chinese and full-width punctuation. Original-language terms already on screen need not be
  repeated in the subtitles.

## 7. Translating quotations

- Quotations from primary sources: translate them yourself from the original (or a public-domain English translation).
  The narration reads the Chinese; on screen, the original small and grey above, the Chinese large below.
- Aim for faithful and fluent translation, and keep the original's tone (acid, elation, self-mockery).
- When citing a modern author's analysis, say 「某某認為…」「某某指出…」 with their name, and mostly
  paraphrase.

## 8. Narration voices

- **Paid narration with ElevenLabs (the default):** the plan's `narration` is
  `{provider_name: elevenlabs, voice_id: FS8UtxyDrvYcNCxVaziq}`, set when the series starts and kept for the whole
  series. The model defaults to `eleven_v4`, which reads Chinese with far more natural rise and fall than
  `eleven_multilingual_v2`; do not set an older model. The plan page lists the Chinese voices chosen for it; another
  Voice Library voice works by its id.
- **Paid narration with VoAI (Taiwanese Mandarin only):** `{provider_name: voai, ...}` with `version`, `speaker`,
  `style` and `speed`. Recommended: the speaker 子墨, the Classic model, the style 平靜. Avoid the Neo model: it clips
  the first syllable of a sentence and the first syllable after a pause. VoAI bills by character.
- Changing the voice re-narrates the affected beats; render again afterwards, since the timeline follows the voice.
- **Automatic spoken text:** before synthesis, `narrate` rewrites each line into what the voice reads: years from 1500
  to 2099 digit by digit (1872 → 一八七二), Greek letters, superscripts and minus signs as in section 5, dashes and
  ellipses as pauses, and corner brackets and book-title marks (「」『』《》) removed. The result is the `spoken_text` text in
  `narration/narration.yaml`; the subtitles keep the original.
- **Changing what the voice reads, not the subtitles:** set `spoken_text_override` on that beat. The voice reads it; the
  subtitles keep the `narration_text`. Use it for things like 「f(x)」 → 「f x」, or to stop the voice from reading a German
  word.
- **Characters with several readings (破音字):** `script validate` warns about spellings paid voices misread (for example
  「多種的」, where 種 is read as in 種類). Rewrite as the warning says, or set `spoken_text_override` with a homophone. When a
  comment points out a misreading the warnings did not catch, fix it with `spoken_text_override`, narrate that beat
  again (`narrate <episode> --beats <id>`), and record it with `explainer-studio gap add --kind tool`.
- **Trying things for free:** `{provider_name: macos-say}` (macOS only, a Taiwanese Mandarin voice, mechanical).
- **Abbreviations and mixed letters and digits:** voices often read strings like 「3b1b」「GPT-3」「QKV」 strangely. Rewrite
  them in the narration when you can (for example 「那支介紹 Transformer 的影片」); when one must stay, set
  `spoken_text_override` with how to say it. After narration, check those beats first.

## 9. Measured conversions between characters and length

- VoAI 子墨 (Neo, 穩健, speed 1.0) measured about **310 to 315 characters per minute** (punctuation included). An 18 to
  20 minute episode ≈ 5,500 to 6,000 characters. Around 7,200 characters (≈ 23 minutes of speech ≈ 24.5 minutes of
  video) is the most an episode should carry; `script validate` warns above it.
- When an episode is over, cut before paying for narration: compress bibliographic and biographical details and delete
  beats that are pure transitions; never cut core content.
- `script validate` warns when a beat is over 60 characters. A scene usually has 3 to 10 beats.
- For a question type's length: 5 minutes ≈ 1,500 characters and 30 to 45 beats.

## 10. Fonts

- Video text uses `scene_kit`'s video font (Noto Sans TC, which covers Chinese and Latin); code uses its monospace font
  (JetBrains Mono); formulas use LaTeX.
- Problems rendering Chinese in ManimGL (stray lines, ℤℚℝ turning into plain letters, colours by substring being lost,
  LaTeX inside Chinese text, the ctex template) are in the rendering references (`rendering/`).
- Chinese with inline math: `get_cjk_tex(R"戴德金分割 $(A \mid B)$")`. A default word for helpers shared across
  languages: `choose_local_text("素材出處", "Credits")`.
- theo's style sets Chinese text in **Noto Sans TC**, which setup installs on every operating system.
- Map region labels default to everyday Traditional Chinese names.
- Cover: the episode label reads 「第 1 集」. The title at full size fits about five characters per line; past about seven
  per line it stops reading at phone size.
- End credits: the page writes 「素材出處」, and 「製作工具」 over the Heptabase icon and name. A source line reads 「Carl B. Boyer《A History of Mathematics》（1968），
  第十九、二十章」: authors joined with 、, the title in 《》, the part the episode covers last. Name each picture by what it shows (「牛頓畫像」). A series in theo's type
  overrides `get_text` with his Chinese face:
  `TexText(Rf"\mbox{{{text}}}", font_size=font_size, template="basic_ctex", additional_preamble=R"\setCJKmainfont{Noto Sans TC}", isolate=isolate)`.

## 11. Sharing feedback

Use these texts as they are. At the first delivery of the series:

> 影片頁上也可以按「送出回饋」，把留言提供給 Heptabase Explainer Studio 團隊。不按就不會送出。

The first time you ask:

> 可以把這一集的回饋提供給 Heptabase Explainer Studio 團隊，協助改善教學方式與製作工具嗎？
>
> 會送出這一集的留言和評分（包括你在對話裡對影片說的話）、我對每則留言的處理說明、留言前後的影片截圖、劇本、系列方案和製作花費的數字。不包含教材原檔、完整影片或音檔。這些資料只在 Heptabase 內部使用，也不會拿來訓練 AI 模型。
>
> 不分享也可以，我一樣會協助修改影片。

## 12. Introducing the whiteboard

Use this text as it is, at the first delivery of an episode with cards:

> 除了影片，我也把這一集的重點整理成筆記卡片，排在一張白板上，不用重看影片也能複習。在影片頁按「白板」就能看到。每一集是白板上的一個區塊，每個場景的卡片排成一欄，箭頭表示推論的方向；黃色卡片是核心主張，綠色是推出的結論，紅色是常見的錯誤。之後的每一集都會加進同一張白板，按「存到 Heptabase」就能存下來。

## Self-check

- [ ] Every abbreviation and mix of letters and digits in the narration was rewritten or given a `spoken_text_override`.
- [ ] Sentences are 40 characters or fewer, with short sentences between long ones.
- [ ] No 「顯然」「易知」「不難看出」.
- [ ] Translations match the series bible, and the original appears on screen at first use.
- [ ] `script validate` shows no length warnings, or each one has a reason.
