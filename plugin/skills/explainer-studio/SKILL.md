---
name: explainer-studio
description: Turns teaching material (lecture notes, a book chapter, a paper, a design document, a codebase) into narrated, animated explainer videos with the Heptabase Explainer Studio command-line tool on the user's computer. Learns who the audience is, reads the material deeply, plans which question each episode answers, picks a presenter for each episode, writes and audience-reviews the script, then makes the narration, animation, music and video. Use when the user asks to make a teaching or explainer video, turn material into a video series, or write an explainer script or storyboard.
---

# Heptabase Explainer Studio

You make teaching videos from the user's sources with the `explainer-studio` command. This file gets the command
ready. How to make the videos is in the guide that comes with the installed command, so it always matches the
version that runs.

## Always

- Talk to the user in the language they write in, including every short progress note. This skill and the guide are
  in English; that is no reason to switch.
- Never ask for, read or print an API key. When one is needed, the guide says how the user enters it in their own
  terminal.
- Making videos runs programs on this computer. Without a shell (ChatGPT on the web, Claude chat), tell the user to
  use Claude Code or Codex on their computer instead.

## Get the command ready

Run `explainer-studio doctor`.

- **Command not found:** tell the user what will be installed, ask once, and install only after they agree:
  - `uv` (the Python tool manager), if missing, in their home folder;
  - the `explainer-studio` command with ManimGL and its Python packages (about 1 GB);
  - ffmpeg, a user-level LaTeX (TinyTeX, about 300 MB) when no LaTeX with Chinese support exists, the fonts, and
    the map data. Nothing needs an administrator password.

  Then run the installer from this skill's folder: `bash <skill folder>/scripts/install.sh` on macOS and Linux, or
  `powershell -ExecutionPolicy Bypass -File <skill folder>\scripts\install.ps1` on Windows. It takes several
  minutes: run it in the background. It installs the command and then runs `explainer-studio setup`. Run `doctor`
  again afterwards.
- **Doctor lists missing parts:** run `explainer-studio setup` (safe to run again; it repairs and upgrades).
- **Ready:** go on to the guide.

## The guide

Run `explainer-studio guide` and follow it. Run it before your first step, again whenever a command says the
Explainer Studio version changed, and again whenever its text is no longer in your context (for example after the
conversation was summarized).
