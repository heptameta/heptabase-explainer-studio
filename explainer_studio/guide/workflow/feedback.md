# After delivery: comments, answers, changes and sharing

## Collecting comments

- The user comments on the video page while watching (`explainer-studio video open <episode>`), or in chat.
- Every remark about the video while watching is a comment, including learning questions; chit-chat is not.
- When the user writes about the video in chat, record it: `explainer-studio feedback add <episode> [--at 1:23] "<their
  words>"`. Keep their words; do not categorize them.
- After a delivery, whenever the user writes to you about the series, first read the `feedback.json` of each
  delivered episode for comments without a `resolution`, and handle them together with what they just said. The video
  page saves comments without telling you, so the ones made since your last reply are only there.
- Before you start the next episode, every comment on the delivered episodes has a `resolution`.

## Responding

The default is to respond, not to change the video.

- Answer learning questions using the images and examples the video already built.
- Explain what a confusing passage meant, and admit flaws plainly.
- Propose a change only when the user asks for one or the problem is systemic (a whole stretch lost them, the same
  kind of problem repeats, or the video is meant for other people). Change it only after they agree.
- Analyse each comment with `references/teaching/feedback-analysis.md`, then record it:
  `explainer-studio feedback resolve <episode> <comment> --category <question|teaching|production|direction> "<cause
  and what you did>"`. The note says why, for example "this line was badly written: two unfamiliar names in one
  sentence".

## Changing the video

Edit the script or scenes, then run what the change needs: script audience review for changed scenes, `narrate`,
`render`, a look at its screenshots, `deliver`, `video open`. Comments stay with the episode; the page marks those
made before the latest delivery as on an older video.

When the viewer got lost earlier than the plan expected, make the remaining episodes lighter (smaller steps, fewer
new terms per episode) in `plan.yaml` and say so.

## Sharing feedback with the Heptabase Explainer Studio team

Share only with the user's explicit agreement, given at that moment. The video page's Send feedback button is the
usual way; ask in chat only when an episode has feedback worth sending. When the language reference of the user's
language gives its own wording for what you say below (`references/languages/<language>.md`, section 11), use that
instead; otherwise say it in the user's language.

- The first time you deliver an episode in a series, tell the user in one sentence that the video page can send their
  feedback to the team:

  > On the video page you can also send your comments to the Heptabase Explainer Studio team with the "Send feedback"
  > button. Nothing is sent unless you press it.

- Ask in chat only when you judge the episode's feedback would teach the team something, for example a comment that
  showed the video teaching badly or something going wrong, or a change or remake of the video. Not for learning
  questions or small things. Ask at most once per episode: before you change or remake the video, or when the user
  moves on.
- If they ignore the question, do not share and do not ask again for that episode. If they say no, do not ask again
  for the rest of the series; they can still share by asking you or with the video page's button.
- Before asking, run `explainer-studio feedback share <episode> --dry-run` and list in the same message what would be
  sent.
- The first time you ask, explain it with this text:

  > May I share this episode's feedback with the Heptabase Explainer Studio team, to help improve how the videos teach
  > and how the tools work? It sends this episode's comments and ratings (what you told me about the video in chat
  > included), my notes on how I handled each comment, frames of the video around the comments, the script, the series
  > plan and the numbers of what making it cost. It does not include your source files, the full video or the audio.
  > The team uses it only inside Heptabase and never to train AI models.
  >
  > You can also decline; I will help you revise the video either way.

  Later times, a short question is enough.
- When they agree: `explainer-studio feedback share <episode>`. A share sends the episode's whole feedback, your
  resolutions, the gaps and every comment screenshot sheet included, and only when something is new since the last
  share.
- The video page's button lists what the user wrote since the last share and sends the same bundle.
- If sending fails, nothing is marked as shared; tell the user and try again at the next agreed share.
