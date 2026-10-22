# The series' whiteboard

How the video page shows a series' cards on a whiteboard drawn by Heptabase and saves it to the user's Heptabase: what
the user sees, which part owns what, how each step works, and what Studio relies on from Heptabase. It is the one place
the package talks to Heptabase's product. The terms are in the [glossary](glossary.md#delivery-and-feedback); the
rules the agent follows for the cards are in [`references/cards.md`](../explainer_studio/guide/references/cards.md),
and the fields of `notes.yaml` and `heptabase-whiteboard.json` in
[`references/file-formats.md`](../explainer_studio/guide/references/file-formats.md).

## What the user sees

The video page has two views next to theater mode, one of the three at a time, both built from the cards the agent
writes for each episode (`production/episodes/<episode>/notes.yaml`):

- **Chapters** (N): the episode's chapters and scenes, read from top to bottom; choosing a scene plays it in its
  chapter's frame. It needs nothing from Heptabase.
- **Whiteboard** (W): every delivered episode's cards on one whiteboard for the series, drawn by Heptabase's web app in
  a frame. An episode is a section, its chapters are sections inside it, a scene is a column of cards, and arrows join
  the cards, also across episodes. The whiteboard is read only on the video page.

The whiteboard is either a preview or saved:

- **Preview**, until the user saves. Studio lays out the cards and the frame draws them in the browser; nothing leaves
  the computer but the frame's own load from Heptabase. **Save to Heptabase** explains in a dialog what saving does and
  which account it goes to, signs in when needed, and creates the whiteboard.
- **Saved**. The whiteboard is in the user's Heptabase, and the frame reads it from there, so it shows what the user
  changed there too. Each episode delivered later is added when one of the series' video pages opens. The toolbar opens
  the whiteboard in Heptabase, brings the episode into view, reads it again, and, in its menu, unlinks it or signs out.

A saved whiteboard that cannot be read says why, with what the user can do: it is in Heptabase's trash (open it in
Heptabase, which offers to restore it, or unlink), deleted (unlink), not shared with the signed-in account, the computer is signed out or Heptabase no
longer accepts its sign-in (sign in again), or Heptabase was not reached (retry).

## Who owns what

Studio owns the content, the ids and the layout; Heptabase measures, draws and stores. Heptabase knows nothing about
series, episodes or Studio's keys: it gets sections, cards, pictures and connections with the ids Studio made.

| Part | Where | Does |
|---|---|---|
| The agent | `notes.yaml` | Writes each episode's chapters, scenes and cards |
| `notes check`, `deliver` | `chapters.py`, `deliver.py` | Check the cards against the render; `deliver` refuses cards that do not fit, unless run with `--skip-notes-check` |
| The page server | `web/server.py` (`/api/series-whiteboard`), `heptabase_whiteboard.py`, `heptabase_sign_in.py` | Gives the page the cards to show and the link; signs in and hands the page access tokens; makes and records the ids, uploads the pictures and asks Heptabase to import; unlinks |
| The video page | `web/static/video.js` | Lays out the cards, talks to the embedded page, shows the whiteboard's state and toolbar |
| Heptabase's embedded whiteboard page | `<app URL>/embed/whiteboard`, in an iframe | Measures cards, shows the preview, reads and shows the saved whiteboard, brings an object into view |
| Heptabase's OAuth server and REST API | `<API URL>` | The sign-in, picture uploads, the import, and the reads the embedded page makes |

## How it works

### The preview

1. The page reads `GET /api/series-whiteboard`: where Heptabase is, the email of the signed-in account, the link, the
   episodes to add (delivered episodes whose cards pass `notes check` and are not on the whiteboard yet) with their
   cards and pictures, a version of those cards, and the delivered episodes without cards.
2. It loads the embedded page in the iframe and waits for `ready`; after 30 seconds it shows that Heptabase was not
   reached.
3. It sends the cards and their pictures with `measureCards`. The embedded page renders each card as a whiteboard would
   at the card width and answers its height. A picture goes as a `Blob` whose key is the picture's URL in the card's
   content.
4. It lays the cards out and sends `showObjects`. The layout rules are in `video.js` (`WHITEBOARD_LAYOUT`,
   `layoutWhiteboardEpisodes`): episodes one under the next; in an episode, its chapters side by side, coloured in turn;
   in a chapter, a column per scene; in a column, a card one row below the cards of its scene that lead to it. The
   preview shows the cards as `notes.yaml` has them when the page lays them out.

### Saving

1. When the computer is not signed in, the tab goes to Heptabase's sign-in and comes back (see
   [Signing in and out](#signing-in-and-out)); the save then goes on by itself.
2. The page sends the layout to `POST /api/series-whiteboard/import`: where each section, card and arrow goes, by its
   key, and the version of the cards it laid out. The page server reads the cards from `notes.yaml` again and refuses a
   layout of other cards (`cards_changed`; the page lays them out again), so what is saved is what was measured.
3. The page server makes a Heptabase id for every object and records them in `production/heptabase-whiteboard.json`
   before asking Heptabase. It uploads each picture (`POST /v1/getUploadUrl`, then a `PUT` to the URL it answers) and
   sends one `POST /v1/explainerStudio/importWhiteboardObjects`: the whiteboard's id and title, the files, the
   sections, the cards (Hepta Markdown, a picture as `hepta-image-ref:<file id>`) and the connections. Once Heptabase
   confirms, it records the episode's `imported_at`.
4. A retry sends the same ids, and Heptabase skips what it has, so nothing is added twice. A picture Heptabase already
   has is not uploaded again, and Heptabase never replaces a picture's bytes. A first save that was never confirmed is
   not a link yet: when Heptabase refuses its whiteboard (trashed, deleted, another account's), the save goes to a new
   one.

### Adding later episodes

When a saved series' video page opens, the iframe loads in the background. Once the saved whiteboard shows, the
episodes to add are measured, laid out under everything on the whiteboard (from the `contentBounds` the embedded page
reports), and imported the same way. Each episode goes on once and only adds; Studio never changes what is there, so
a later change to `notes.yaml` does not reach an episode already on the whiteboard. An arrow from an earlier episode
goes with the later episode, and only when the earlier one is on the whiteboard.

### Showing the saved whiteboard

The page asks the page server for an access token (`GET /api/series-whiteboard/access-token`) and sends
`showWhiteboard`. The embedded page reads the whiteboard from Heptabase's REST API with that token and answers
`whiteboardShown` (its title, its space and the box around its contents) or `failed` with a reason. The page reads it
again with a fresh token (`updateAccessToken`, then `refreshWhiteboard`) after an import and whenever the page comes
back to the foreground; a whiteboard that could not be read is tried again from the start, since it may be back from
the trash. Choosing a chapter, or the episode, sends `focusObject`.

Once the user clicks in the whiteboard, the keyboard focus is in the iframe, so the video page's keydown never sees a
key. The embedded page passes keys on as `keyPressed`, and the video page runs its shortcut for each, as it would for
the same key pressed on the page. When the whiteboard closes, the video page takes the focus back.

### Signing in and out

- The sign-in is per computer and serves every series. It uses Heptabase's OAuth server: its metadata
  (`/.well-known/oauth-authorization-server`), a public client registered the first time with a loopback redirect, the
  authorization code flow with PKCE, the scope `openid email offline_access space:read space:write` for the REST API's
  resource, and the account and its email from `/me`. Heptabase sends the browser back to the page server's
  `/heptabase-callback` on 127.0.0.1, and the page server sends it on to the page that started the sign-in.
- Studio relies on every endpoint in the metadata being on the issuer's own origin over HTTPS (HTTP only on
  localhost), and refuses to sign in otherwise: the refresh token is kept under the issuer, so it only ever goes back
  there. Token and revocation requests do not follow redirects.
- `credentials.toml` keeps the client registration, the account, its email and the refresh token under
  `[heptabase."<issuer>"]`. Access tokens stay in the page server's memory, refreshed five minutes before they expire,
  and in the iframe's.
- Signing out revokes the refresh token and deletes that table, client registration included. The links stay, and a
  saved whiteboard then asks for a sign-in. A sign-in Heptabase refuses loses only its refresh token, so every series'
  page says it expired rather than that the computer is signed out.
- Saving with another account than the one that saved the whiteboard is refused (`other_account`).

### Unlinking

Unlinking deletes `heptabase-whiteboard.json`. The whiteboard stays in Heptabase, and the next save makes a new one.

## What Studio relies on from Heptabase

A released Studio talks to whatever Heptabase has deployed, and older releases keep running. Once a release uses
something below, Heptabase changes it only by addition: new messages, fields, reasons and codes, never one removed or
renamed. Studio ignores messages and fields it does not know. A failure reason or error code it does not know shows as
such, with a hint that updating Studio may fix it. A Studio change that needs something new from Heptabase is released
after Heptabase deploys it.

A change that cannot be made by addition breaks the releases that use what it changes, and Heptabase answers them with
`upgrade_required`. The REST API answers `{"code": "upgrade_required"}`, whatever the HTTP status, to the releases it
tells by the User-Agent (`explainer-studio/<version>`). The embedded page, which does not know the release, answers
`failed` with that reason to a request it can no longer serve. Studio then asks the user to update it. Studio has known
both since its first release with the whiteboard.

### The embedded whiteboard page

The video page loads `<app URL>/embed/whiteboard` in an iframe. The embedded page accepts a host page only on
`http://127.0.0.1` or `http://localhost`, where the page server listens, and the page server's Content Security Policy
allows frames from the app's origin only. They talk with `postMessage`, and the video page reads messages only from
that iframe's window and origin. When it loads, the embedded page sends `ready` with its `protocolVersion`. A request
that gets a reply carries a `requestId`, which the reply repeats; the embedded page handles one message at a time, in
the order they came.

| The video page sends | With | The embedded page answers |
|---|---|---|
| `measureCards` | `requestId`, `cardWidth`, `cards` (`key`, `content`), `files` (`key`, `blob`) | `cardsMeasured` with the `heights` by key, or `failed` (`reason`) |
| `showObjects` | `title`, `sections`, `cards`, `connections`, `files`, and optionally `focusTarget` | nothing |
| `showWhiteboard` | `requestId`, `whiteboardId`, `accessToken`, and optionally `focusTarget` | `whiteboardShown` (`title`, `spaceId`, `contentBounds`) or `failed` (`reason`, and `spaceId` with `trashed`) |
| `refreshWhiteboard` | `requestId`, and optionally `focusTarget` | the same as `showWhiteboard` |
| `focusObject` | `focusTarget`: a `key` given in `showObjects`, or the `objectId` of an object on the saved whiteboard | nothing |
| `updateAccessToken` | `accessToken` | nothing |

`failed` gives one of `trashed`, `deleted`, `forbidden`, `unauthorized` and `network`, or `upgrade_required` (above).
With `trashed` it also gives the whiteboard's `spaceId`, so the link to restore it opens the whiteboard itself; without
one, it opens Heptabase.

The embedded page also sends `keyPressed` (`key`, `code`, as in the browser's `KeyboardEvent`), answering no request:
a key pressed in the embedded page without Cmd, Ctrl or Alt, not typed into a field, not taken by an input method,
and not one the page handled. Letters come. Space and the arrow keys may come although the whiteboard uses them
(to grab the canvas and to move between objects), so the video page leaves them alone while the whiteboard shows.

### The REST API and the OAuth server

| Request | For | Answers Studio handles |
|---|---|---|
| The OAuth metadata, registration, authorization, token and revocation endpoints | Signing in and out | `access_denied` from the consent page: the sign-in was canceled |
| `GET /me` | The signed-in account (`sub`) and its `email` | |
| `POST /v1/getUploadUrl` | A presigned URL to upload one picture | `{status: "file_exists"}`: the picture is there already |
| `POST /v1/explainerStudio/importWhiteboardObjects` | Creating the whiteboard and adding episodes | `401`: the page server refreshes the access token once, then asks for a sign-in. `403 subscription_required`. `409 outdated_db_schema_version`: the account's data is older than the whiteboard needs, which opening the Heptabase app and updating it fixes. `409 whiteboard_trashed`, `409 whiteboard_deleted` and `403 forbidden`: for a first save, a new whiteboard |

`GET /me`, `getUploadUrl` and the import may also answer `upgrade_required` (above). A refusal without a code shows
with its HTTP status.

Saving needs an active Heptabase subscription (`subscription_required`). The preview needs no account.

## Files and state

| Where | What | Written by |
|---|---|---|
| `production/episodes/<episode>/notes.yaml` | The episode's chapters, scenes and cards | the agent |
| `production/heptabase-whiteboard.json` | The link: the Heptabase it is in (its OAuth issuer), the account that saved it, the whiteboard's id, the Heptabase id of everything Studio put on it by its key, and each episode's `imported_at`; never a token | the page server, from the first save |
| `credentials.toml`, `[heptabase."<issuer>"]` | The sign-in: the client registration, the account, its email and the refresh token | the page server |
| The page server's memory | Access tokens, and sign-ins under way (for 15 minutes) | the page server |
| The iframe | The access token it was given last | the video page |

`EXPLAINER_STUDIO_HEPTABASE_APP_URL` and `EXPLAINER_STUDIO_HEPTABASE_API_URL` point the whiteboard at another Heptabase
than `https://app.heptabase.com` and `https://api.heptabase.com`, such as a local web app and backend while developing.
The page server reads them when it starts.
