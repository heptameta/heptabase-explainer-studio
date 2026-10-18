# Privacy

Explainer Studio runs on your computer, and what it makes stays there: your sources, the series folder, the videos.
Three kinds of things leave it: the feedback you choose to share with Heptabase, the series' whiteboard once you save
it to your Heptabase, and what the services that do the work for you need, such as the narration provider you chose.
This page says what each one is and what happens to it.

## What leaves your computer

| Where it goes | What | When | Whose terms apply |
|---|---|---|---|
| Heptabase | An episode's feedback bundle | Only when you agree to share it | This page |
| Heptabase | The video page's whiteboard view loads Heptabase's web app in a frame, which draws the cards inside your browser; the cards do not leave your computer for it | When you open the whiteboard view, and in the background when a saved series has episodes to add | Heptabase's |
| Heptabase | The sign-in to your Heptabase account (Heptabase tells Studio which account signed in and its email, which Studio keeps on this computer to show where saving goes), then the series' title, each episode's and chapter's title, the cards, their pictures (frames of your videos, and pictures from the series folder) and where each goes, to a whiteboard in your own Heptabase account | Only once you press Save to Heptabase on the video page; after that, when you open any of the series' video pages, every delivered episode not on the whiteboard yet | Heptabase's, under your account |
| The narration provider you chose (ElevenLabs, OpenAI or VoAI) | The narration text and voice settings, with your key | When the agent narrates an episode, and when you test your key | The provider's, under your account |
| Image and data sites (Wikimedia Commons, Bioicons, Wikipedia, Our World in Data, the World Bank) | Search queries, and the files the agent downloads | When the agent looks for pictures or data | Each site's |
| Web pages the agent records | A visit by a browser with no window | When the agent records a page for a video | Each site's |
| GitHub and the sites tools come from (astral.sh, PyPI, CTAN mirrors, blender.org, Playwright) | Checks for a new release, and downloads | When installing, setting up or upgrading; `doctor` checks for a new release at most once a day | Each site's |
| Your coding agent's model provider | What the agent reads and writes, your sources included | Whenever the agent works | Your agreement with that provider |

The macOS voice and the background music are made on your computer.

## Feedback you share with Heptabase

Nothing is shared unless you agree. The usual way is the video page's "Send feedback" button: it lists what will be
sent and sends only when you confirm. When an episode's feedback seems worth sending, such as a flaw in the video or a
remake, the agent may also ask you in chat, listing the same, and shares only if you say yes. No account is
involved.

### What a share sends

A share sends one episode's feedback bundle:

- your comments on the episode, made on the video page or in chat (the agent records what you say about the video,
  your questions included, as comments), and your answers to the video page's questions, such as your rating;
- the agent's notes on how it handled each comment, and the limits of the tools it ran into;
- for each comment about a moment of the video, one picture of the video's frames a few seconds around it;
- the script of each version of the episode delivered to you: what each scene is for, its narration, a description of
  what is on screen and its citations, which may quote or name your sources; and where each scene and sound sits;
- the series plan as written: how it lists your sources (by file name, or by their full path on your computer if the
  agent wrote them so), what the agent learned about you as the viewer (what you know, your answers to its questions
  as evidence, the misconceptions it noted), the goal, the episodes, the topics left out, and the narration voice and
  budget;
- what making the series' plan and this episode took: each model call with its model, token counts and time, the
  time worked, and the narration's length and estimated cost;
- the date and time of each of these (comments, answers, notes, deliveries and each step of the work), in your
  computer's time zone;
- the Explainer Studio version and your operating system.

A share never sends your source files, the video file, the audio, your keys, or any other file in the series folder.
A bundle can still contain passages of your sources quoted in the script, and pictures from your video, which can
show figures, pages or code from your sources.

Each share sends the episode's whole feedback as it stands, and only when something is new since the last share.

### What happens to it

- A bundle goes over HTTPS to Heptabase's server, which stores it as received.
- The Heptabase Explainer Studio team reads it to find where the videos fail to teach and where the tools fall short,
  and to improve them.
- It is never used to train AI models, and never shared outside Heptabase.
- It is kept until you ask for it to be deleted.
- Like any web request, a share reaches the server from your IP address. The server uses it to limit how many bundles
  one address can send per hour and records it in its request logs, as it does for every request; it is not stored
  with the bundle.

### Deleting it

Email [support@heptabase.com](mailto:support@heptabase.com) with the episode's feedback id, and every bundle shared for
that episode is deleted. The id is the `id` in `production/episodes/<episode>/feedback.json`; you can also ask the
agent for it.

## Services that do the work

Explainer Studio talks to these services directly from your computer, with your own key where one is needed; none of
it goes through Heptabase. What each service does with it is governed by its own terms.

- **Narration:** when the agent narrates an episode, each beat's narration text and the episode's narration settings
  (for OpenAI, its voice instructions) go to the provider you chose, with your key; ElevenLabs also gets the text of
  the beats around each one, for intonation. `explainer-studio setup narration` sends the key you enter to the
  provider once, to test it. The key is kept on your computer and never goes through the chat.
- **Images and data:** when the agent looks for pictures or data, its search queries go to Wikimedia Commons,
  Bioicons, Wikipedia, Our World in Data or the World Bank, and it downloads the files it picks from them.
- **Recording web pages:** when the agent records a web page for a video, a browser with no window visits that page.
- **Installing and upgrading:** installing, `setup` and `upgrade` download uv (astral.sh), Python packages (PyPI),
  ffmpeg, a TeX distribution, fonts and map data (GitHub), TeX packages (CTAN mirrors), Blender (blender.org),
  Playwright's browser, and Explainer Studio itself (GitHub). `upgrade` asks GitHub for the latest release each time
  it runs, and `doctor` at most once a day.
- **Your coding agent:** the agent reads your sources and writes the scripts through its own model provider, under
  your agreement with that provider; Explainer Studio does not change what the agent sends there.

[The system design](docs/system-design.md#what-leaves-the-computer) lists the same in more technical detail.
