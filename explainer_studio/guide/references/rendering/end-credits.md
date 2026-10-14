# End credits

Every episode ends on an end credits page unless `plan.yaml` turns it off (`has_end_credits: false`, which the user can
also set on the plan page).

**What it is.** After the last scene, `render` cross-fades into the page in one second and holds it to the end of five
seconds; nothing is narrated over it. The page lists what the episode is based on and the external material it shows,
and ends with a small "Made with" over the Heptabase app icon and name, in the episode's language. Viewers know
credits from films and books: they show the video is sourced and made with care, and they give the attribution that
licences such as CC BY and CC BY-SA require. Do not write a credits scene of your own: the page comes after the last
scene by itself.

## end_credits.py

`episodes/<episode>/end_credits.py` holds one `EndCreditsScene` subclass. Without it, `render` uses the default page:
every asset the episode can use (files under `shared/` and the episode's own folder) under its `credits.yaml` title,
and no sources. Write it for every episode:

```python
from explainer_studio.scene_kit import *


class EndCredits(EndCreditsScene):
    source_lines = ["Carl B. Boyer, A History of Mathematics (1968), chapters 19 and 20"]
    asset_name_by_file_path_map = {
        "shared/assets/portraits/Isaac_Newton.jpg": "Isaac Newton",
        "shared/assets/portraits/Leonhard_Euler.jpg": "Leonhard Euler",
    }
```

- `source_lines`: what the episode is based on, one line per source: the authors, the title, the year and the part
  this episode covers. The language reference says how a citation reads in the series language.
- `asset_name_by_file_path_map`: the `credits.yaml` files this episode shows, in the order they appear, each with the
  name the page gives it: what the picture shows, in the series language (an empty name keeps the `credits.yaml`
  title). The page adds each file's author and licence. Leave out files the episode does not show. A file without a
  `credits.yaml` entry fails the render; add an entry by hand for material you got another way. When an entry's
  `author` is a long note (who scanned or uploaded the file), shorten it in `credits.yaml` to the maker's name.
- **The series' type.** The page draws its text with `get_text(text, font_size, isolate)`, by default `Text` in the
  video font. When the series sets its text in another type (Theo's Computer Modern, for example), override it so the
  last frame looks like the rest of the video. Write the override once in `production/shared/` and subclass it in
  every episode. It returns a `StringMobject` (`Text`, `TexText`, `Tex`) built with `isolate=isolate`, so the page can
  colour and place the parts it names:

  ```python
  # production/shared/series.py
  class SeriesEndCreditsScene(EndCreditsScene):
      def get_text(self, text, font_size, isolate):
          return TexText(Rf"\mbox{{{text}}}", font_size=font_size, isolate=isolate)  # \mbox: one line, no wrapping
  ```

  The language reference gives the call for scripts that need another template.
- The layout, the colours and the closing are fixed, so every episode ends the same way. About eight
  assets and a source line fit at full size; a longer list shrinks.
- `get_end_credits_page(source_lines, entries, get_text)` builds the same page as a mobject, if you need it elsewhere.
- Preview it with `explainer-studio preview <episode> --end-credits` (`preview <episode>` with no options includes it);
  it writes `preview/end-credits/end-credits.png` at 1080p. Check that every external picture the episode shows is
  listed and that the names read naturally.

## When the user does not want it

Do not bring the page up yourself: the plan page shows the switch. When the user says they do not want end credits,
set `has_end_credits: false` in `plan.yaml`, note it in `decisions.md` and render again. Material that requires
attribution is then credited in the frame where it appears, in small type in a corner
([assets.md](assets.md#licences-and-credits)).
