# Cover

Every episode needs a cover; `render` refuses an episode without `cover.py`.

**Why.** Chat apps (Discord, Slack, LINE, Telegram and others) show a video's first frame as its preview. A 3Blue1Brown
style opening starts from black and draws something, so without a cover every preview would be a black rectangle.
`render` holds the cover for the first second of the video and cross-fades it into the first scene in half a second
(narration, sounds and subtitles start one second later), and delivers the same picture next to the video as
`<nn>-<title>.png`, ready to use as a thumbnail.

**The cover is not the opening.** The episode itself still starts with a concrete hook in its first seconds, never a
title card ([teaching/visual.md](../teaching/visual.md#openings-sections-endings)). The cover exists only in the first
second of the delivered file and is never part of a scene.

## cover.py

`episodes/<episode>/cover.py` holds one `CoverScene` subclass. You write only `get_visual()`, which returns the
episode's central picture; the layout is fixed so the covers of a series match: a dark-grey background, a black rounded
panel on the left holding the picture, and on the right the series title, the episode label in yellow ("Episode 1", or
its form in the episode's language) and the episode title in very large type.

```python
from explainer_studio.scene_kit import *

from shared.series import get_dam


class Cover(CoverScene):
    title = "Why can water\nturn a wheel?"   # optional: plan.yaml's title otherwise; two short lines read best

    def get_visual(self):
        return get_dam(left=3.2, right=0.8)
```

- The title, series title and label come from `plan.yaml`. Set the class attributes `title`, `series_title` or
  `label` only to override them; `\n` in `title` is a manual line break.
- Build the picture from the same shared builders the episode uses, or reuse a scene's central object. A picture file
  works too: `return get_image("shared/assets/images/dam.png", height=4)`. The layout scales the picture to fit the
  panel.
- `get_episode_cover(title, series_title, label, visual)` builds the same layout as a mobject, if you need it
  elsewhere.
- Preview it with `explainer-studio preview <episode> --cover` (`preview <episode>` with no options includes it); it
  writes `preview/cover/cover.png` at full 1080p.

## Design rules

- **Readable at 400 px wide**, the size of a preview on a phone: the title is the first thing you read. Write at most
  two lines. The full type size fits about ten Latin letters per line; longer lines shrink the whole title, and past
  about fourteen Latin letters per line it stops reading at phone size (other scripts: the language reference). Break
  the line by hand at a natural pause.
- The title is the episode's title as the plan and the video say it; do not invent a different cover wording.
- **One central object** in the panel: the single most representative picture of the episode (the Weierstrass function
  with its zoom box, the cut at √2, the dam with its two levels). No small explanatory text in the panel.
- **Colours** follow the series bible; at most three accent colours.
- The layout keeps the text column clear of the right edge; do not move it.
- When a series has several episodes, look at all the episodes' `preview/cover/cover.png` together: they should read
  as one series (same kind of picture, same colours, titles of similar length).
