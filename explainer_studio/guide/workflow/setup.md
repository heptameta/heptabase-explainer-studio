# Setup

## Narration keys

Only `narrate` needs a key, so ask for it when production is about to start, not before. Ask the user to run this in
their own terminal (never ask them to paste a key into the chat, and never read or print one yourself):

```bash
explainer-studio setup narration
```

It asks for the provider, reads the key without showing it, tests it and stores it. A key in an environment variable
(for example `ELEVENLABS_API_KEY`) also works. To try the workflow without a key on macOS, set the plan's narration
to `{provider_name: macos-say}`.

## Optional tools

Only when a video needs them, explain the size and ask:

- `explainer-studio setup blender` installs Blender (about 1 GB) for `asset blender render`.
- `explainer-studio setup playwright` installs Chromium (about 150 MB) for `asset playwright record`.

## When something fails

Show the user the error's first lines and what you will try. Run `explainer-studio setup` again once. If it still
fails, record it with `explainer-studio gap add --kind tool` and tell the user what they can do (the error's `next:`
line says it).
