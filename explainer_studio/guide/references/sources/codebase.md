# Reading codebases, code changes and technical documents

**Kinds:** `codebase`, `change`, `spec`.

Use this when the source is a codebase, a PR or a series of commits, a design document or a specification, and the
video explains "how it works", "why it was changed this way" or "why it was designed this way" (for new team members,
for a product owner who does not write code, for the user themselves). Basis: making a six-episode series on a codebase
for engineers who had built web pages.

## Where the questions usually are

| Kind | Where the questions and prerequisites usually are | When putting it into the video |
|---|---|---|
| Codebase `codebase` | The route one request or one piece of data takes; calls between modules | Use the real code on screen, labelled with its file name |
| Code change `change` | The problem before the change; the PR discussion | Show what it looked like before the change first |
| Technical document `spec` | The problem it solves, and the decisions it made | Say out loud why it was designed this way |

A code change: read the code before the change and the PR's description and discussion first, then the diff; the
coverage list cites commits and files. A technical document: compare its decisions with the code that was actually
written from it, and note where they disagree.

## Reading it in

1. **First see how it is used, then how it is written.** Start from the entry points a user really meets: install
   instructions, the README, the commands they type, configuration files, the screens and files that appear. Trace from
   an entry point inward, rather than reading the folder structure top-down.
2. **Separate who touches which files.** A repository usually mixes files users rely on, files only for developers,
   generated files (build output, caches, settings starting with `.`) and records (documentation, handovers). The
   question viewers ask most is "which of these are actually used?", so the coverage list includes a list of every
   top-level folder: who uses it, when, and whether it can be deleted.
3. **Follow one concrete example all the way through.** One request, one command or one file: from coming in to going
   out, which code, which processes and which files it passes through. Every episode can later point back at this route.
4. **Real output is better evidence than reading alone.** Where it is available, use it: the processes really running
   (`ps`), the files really produced, the real error messages, the real list of tools. Evidence in the video built
   from this real output is more reliable than inference from the code, and more convincing.
5. **When the documentation and the code disagree, the code is right.** Note the disagreement: it is often a bug, and
   may also be a trap viewers will fall into later.
6. Before probing the viewer, skim only enough to pick probes: a few real file names, a real piece of configuration, a
   real error message.

## The coverage list

- Each item cites its source down to **the file and line number, or the function name** (for example `gates.py`
  `require()`). Line numbers change; a function name and a piece of the original text last longer.
- Also make three lists:
  - **What users can see:** commands, settings, screens, files produced.
  - **The seams between parts:** who starts whom, and how they communicate (processes, pipes, HTTP, files), with where
    each seam is defined.
  - **Where rules are enforced:** list recommendations written in the documentation separately from checks written as
    code that actually block. Viewers who want to change something need this most.

## Real content on screen

- Code, configuration files, logs, error messages, file trees and tool lists shown as real content are **always read
  from the source file or the real output, never copied by hand or invented.** For a file, use `scene_kit`'s
  `read_file_excerpt`, which records the file, the lines and a fingerprint of the content; when the code changes later,
  `render` warns that the excerpt no longer matches.
- Save real output (`ps`, a command's result) into `production/sources/` before reading it, and say in the narration or
  in small text on which computer and when it was run.
- To shorten, use "…" and keep the lines that make it understandable; never change the words of real content to make it
  look better.
- Check paths, version numbers and counts (for example "23 checks") on the day the video is made. For things that
  change, say "at the time of this episode" in the narration.

## Verifying

- Every sentence in the script about how the program behaves can point to a piece of code or a real run; the to-verify
  list cites it.
- Claims about how external tools (editors, AI assistants, platforms) work inside are the easiest to overstate. Say only
  what you can see evidence for (their output, their documentation); call the rest "roughly", or leave it out. The
  script audience review's item on claims stronger than an expert would make deserves extra attention on these
  sentences.
- After an episode is made, the code may have changed. Before delivery, read `render`'s warnings for excerpts that no
  longer match.

## Self-check

- [ ] Code, configuration, logs and error messages shown as real content were read from the source file
      (`read_file_excerpt`) or real output; nothing was copied by hand or invented.
- [ ] For every analogy to a technology the viewer knows, the script says where it stops working.
- [ ] Every sentence about program behavior was checked against the code or a real run; the to-verify list has nothing
      open.

## How it is told

How a program works is usually a system question ([teaching/question-types.md](../teaching/question-types.md)). Theo's
playbook is "walk through the system" ([presenters/theo/question-types/system.md](../presenters/theo/question-types/system.md)).
