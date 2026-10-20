# Sound

Contents: [What is in the mix](#what-is-in-the-mix) · [self.play_sound](#selfplay_sound) ·
[Placing a sound in time](#placing-a-sound-in-time) · [Clip and score sound](#clip-and-score-sound) ·
[Background music](#background-music) · [Checking](#checking)

## What is in the mix

`render` mixes four things: the narration, the sounds the scene code places, the sound of video clips and scores, and
the background music under all of them when the plan turns it on. Levels are set for you:

- Narration sits at -20 dBFS RMS (one gain for the whole episode, so the voice keeps its own dynamics).
- Built-in effects play at fixed levels well under the voice. Audio files and clip sound are levelled to the speech,
  then shifted by their `gain_decibels`.
- Background music sits 15 dB under the speech and drops another 7 dB while someone speaks or while a sound that ducks
  the music plays.
- The finished mix is normalized to -16 LUFS with a true peak of at most -1.5 dBTP.

`preview` mixes the narration (where it is current) and the sounds, without background music, into each scene's
`clip.mp4`.

The script has no sound field. A sound in the middle of the narration is described in the beat's `visual`, and the
beat's `pause_duration_seconds` leaves the time for it, so the audience reviewer also knows it is there.

## self.play_sound

```python
self.play_sound(name_or_path, gain_decibels=0.0, should_duck_background_music=None, *, source_start_seconds=0.0,
                duration_seconds=None)
```

- **A built-in effect** by name. They are synthesized, original, with no licence to track, and leave the background
  music alone unless `should_duck_background_music=True`:

  | Name | Sound | Length | Played automatically by |
  |---|---|---|---|
  | `whoosh_out` | a soft whoosh, left to right | 0.75 s | `shrink_to_inset` |
  | `whoosh_in` | the same whoosh reversed | 0.75 s | `expand_from_inset` |
  | `questioner` | two soft bell notes | 1.9 s | `play_questioner_entrance` |
  | `ghost` | the same two bell notes | 1.9 s | |
  | `bubble` | a short pop | 0.09 s | `play_questioner_question` |
  | `title` | a three-note bell chime for the title card | 3.0 s | (call it when the title card appears) |

- **An audio file**, by a path relative to `production/` (for example a recording from `asset commons search
  "<words>" --media-type audio`, [assets.md](assets.md)). Files duck the background music by default, so two pieces of
  music never play over each other; pass `should_duck_background_music=False` for a quiet ambience.
  `source_start_seconds` and `duration_seconds` play part of the file.
- A name that is neither an effect nor an existing file stops the scene with the list of effects, and a file outside
  `production/` stops it too: copy the file into `production/shared/assets/audio/` first.
- Every sound is recorded into the render's `timeline.json` under `sounds`, with its start time.

## Placing a sound in time

A sound starts at the scene's current time: the moment the code reaches `self.play_sound(...)`. Time moves only in
`self.play` and `self.wait`, so the order of the code is the order in the video.

**A sound in a beat's pause.** Leaving a `with self.play_beat(...)` block waits through the line and its whole pause,
so a sound written after the block starts only when the pause is over. To play it in the pause, stay inside the block:
wait for the line to end, start the sound, and animate through the pause.

```python
# script: wheel_appears has pause_duration_seconds: 2
with self.play_beat("wheel_appears") as beat:
    self.play_sound("whoosh_in")
    self.play(FadeIn(wheel, scale=0.8))
    self.wait(beat.remaining_seconds)               # to the end of the line
    self.play_sound("shared/assets/audio/chord.ogg")  # starts as the line ends
    self.play(Rotate(wheel, PI, rate_func=linear), run_time=2)   # turns during the pause
```

The block's closing wait then has nothing left to wait for. If the animations in the pause run longer than the pause,
the next line starts later.

**A sound on a word.** Start it inside the block at `beat.get_seconds_until(f)`:
`self.wait(beat.get_seconds_until(0.5))`, then `self.play_sound(...)`.

**A sound between beats with no narration around it** (a recording that speaks for itself): write it after one block
and before the next, followed by a `self.wait(...)` or animations as long as the sound. The next line starts after them.

## Clip and score sound

- `play_clip(self, clip, start_seconds, end_seconds, should_play_audio=True, gain_decibels=-3.0, speed=1.0)` plays a
  stretch of a video clip and puts its own sound into the mix (ducking the music). Inside a beat it runs under the
  narration; pass `should_play_audio=False` to keep footage with sound silent under speech. A clip with no sound
  track (Blender shots, screen recordings) adds nothing, and a clip played at another `speed` is always silent.
  Between beats, it lets the footage speak for itself.
- `play_score(self, score, should_play_audio=True, gain_decibels=-4.0)` lights the notes as they sound and mixes a
  plain piano rendering of the score, written to `shared/assets/audio/scores/`.
- Both wait while they play, like `self.wait`: place them where the time should go, by the same rules as above.

## Background music

The plan chooses the music; scene code does not.

- `background_music` in `plan.yaml`, for the series or one episode (an episode's block replaces the series' block
  entirely). Omitted means `{provider_name: none}`, no music; `{provider_name: synthesized-piano}` turns it on.
- `synthesized-piano` is original music made by the program: a slow felt piano over a warm pad, a key of its own per
  episode, a new phrase at the start of every scene. It has no licence to track.
- The music fades in at the start and out at the end, and ducks under the narration and under ducking sounds on its
  own.

## Checking

- Preview's `clip.mp4` has the narration and the sounds; you cannot listen to it, so check the placement in the code
  (the order of `self.play_sound` against the beats and waits).
- After `render`, `render/timeline.json` lists every beat's start and duration and every sound's start, duration,
  gain and ducking, in seconds of the finished video (the cover takes the first second). Compare a sound's start with
  the end of the beat it should follow.
