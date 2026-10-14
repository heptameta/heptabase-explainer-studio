// The video page: the latest delivery of one episode, its comments, the survey (a rating, and the watch depth in dev
// mode) and sharing with the team.
// Keys: Space plays or pauses, the arrows move 5 s, M adds a comment (the video pauses; Enter saves and plays on,
// Esc cancels), C turns subtitles on or off and T turns theater mode on or off. The video element is made once;
// everything else is shown again from the server's JSON whenever feedback.json or the delivery changes, so the agent's
// changes show up without a reload.
'use strict';

const EPISODE_ID = BOOT.episodeId;
const SEEK_SECONDS = 5;
// The survey's questions by survey answer kind, in the page's order. `stringKey` names the question's strings: its
// heading, its answers and its line in the share dialog.
const SURVEY_QUESTION_BY_KIND_MAP = {
  rating: {stringKey: 'rating', values: ['good', 'okay', 'bad']},
  watch_depth: {stringKey: 'watchDepth', values: ['closely', 'skimmed', 'partly']},
};
let pageData = null;
let pageDigest = null;
let video = null;
let commentDraft = null;  // {momentSeconds, isAboutMoment, wasPlaying, isSaving}
let editingCommentId = null;
let isHandledOpen = false;
let isOlderVideosOpen = false;
let isRefreshPending = false;
let isShowingSubtitles = (() => {
  try { return localStorage.getItem('subtitles') === 'on'; } catch (error) { return false; }
})();
let isTheaterModeOn = (() => {
  try { return localStorage.getItem('theaterMode') === 'on'; } catch (error) { return false; }
})();
const nodes = {};

async function fetchPageJson() {
  const result = await callApi('GET', `/api/video/${EPISODE_ID}`);
  if (!result.isOk && result.status && !pageData) {
    document.getElementById('app').replaceChildren(buildElement('div', {class: 'hb-banner error', role: 'alert'},
      buildElement('b', {}, translate('common.error.load')),
      result.body.message ? buildElement('div', {}, result.body.message) : null));
  }
  return result.isOk ? result.body : null;
}

// Player ------------------------------------------------------------------------------------------------------------
function applySubtitles() {
  if (video && video.textTracks.length) video.textTracks[0].mode = isShowingSubtitles ? 'showing' : 'hidden';
  if (nodes.subtitles) nodes.subtitles.setAttribute('aria-pressed', String(isShowingSubtitles));
}

function toggleSubtitles() {
  if (!pageData.delivery.subtitles.length) return;
  isShowingSubtitles = !isShowingSubtitles;
  try { localStorage.setItem('subtitles', isShowingSubtitles ? 'on' : 'off'); } catch (error) { /* private window */ }
  applySubtitles();
}

// Theater mode: the video as large as the window allows, on a black band across the page, with the toolbar still in
// view under it.
function applyTheaterMode() {
  document.body.classList.toggle('theater-mode', isTheaterModeOn);
  if (nodes.theaterMode) nodes.theaterMode.setAttribute('aria-pressed', String(isTheaterModeOn));
}

function toggleTheaterMode() {
  if (!video) return;
  isTheaterModeOn = !isTheaterModeOn;
  try { localStorage.setItem('theaterMode', isTheaterModeOn ? 'on' : 'off'); } catch (error) { /* private window */ }
  applyTheaterMode();
  if (isTheaterModeOn) video.scrollIntoView({block: 'start'});
}

function togglePlay() {
  if (!video) return;
  if (video.paused || video.ended) video.play(); else video.pause();
}

function seekBy(seconds) {
  if (!video) return;
  video.currentTime = Math.min(Math.max(0, video.currentTime + seconds), video.duration || Infinity);
}

function jumpTo(seconds) {
  if (!video || seconds === null || seconds === undefined) return;
  video.currentTime = seconds;
  video.scrollIntoView({behavior: 'smooth', block: 'nearest'});
}

// Composer ----------------------------------------------------------------------------------------------------------
// A comment is about the moment the video was paused at, or about the whole episode. Before the video has started
// and after it has ended there is no moment the viewer is reacting to, so the composer starts with the whole episode.
function startComment() {
  if (commentDraft) { nodes.composer.querySelector('textarea').focus(); return; }
  const momentSeconds = video && video.currentTime > 0 && !video.ended ? video.currentTime : null;
  commentDraft = {momentSeconds, isAboutMoment: momentSeconds !== null,
    wasPlaying: !!video && !video.paused && !video.ended};
  if (video) video.pause();
  const input = buildElement('textarea', {rows: 2, 'aria-label': translate('video.composer.label')});
  input.addEventListener('input', () => growTextarea(input));
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !event.shiftKey && !checkIsImeEnter(event)) {
      event.preventDefault();
      submitComment(input.value);
    }
    if (event.key === 'Escape') { event.preventDefault(); endComment(); }
  });
  const target = buildElement('div', {class: 'at'});
  const showTarget = () => {
    input.placeholder = translate(commentDraft.isAboutMoment
      ? 'video.composer.placeholder' : 'video.composer.placeholderWholeEpisode');
    target.hidden = commentDraft.momentSeconds === null;  // nothing to choose: the comment is about the whole episode
    if (target.hidden) return;
    const buildOption = (isAboutMoment, text) => buildElement('button', {class: 'hb-btn', type: 'button',
      'aria-pressed': String(commentDraft.isAboutMoment === isAboutMoment),
      onclick: () => { commentDraft.isAboutMoment = isAboutMoment; showTarget(); input.focus(); }}, text);
    target.replaceChildren(buildElement('div', {class: 'segmented small', role: 'group',
      'aria-label': translate('video.composer.target')},
      buildOption(true, formatTime(commentDraft.momentSeconds)),
      buildOption(false, translate('video.comment.noTime'))));
  };
  showTarget();
  nodes.composer.replaceChildren(
    target,
    input,
    buildElement('div', {class: 'row'},
      buildElement('button', {class: 'hb-btn text', type: 'button', onclick: () => endComment()},
        translate('common.cancel')),
      buildElement('button', {class: 'hb-btn fill', type: 'button', onclick: () => submitComment(input.value)},
        translate('video.composer.save'))));
  nodes.composer.hidden = false;
  input.focus();
}

function endComment(wasSaved) {
  if (!commentDraft) return;
  const shouldResume = commentDraft.wasPlaying;
  commentDraft = null;
  nodes.composer.hidden = true;
  nodes.composer.replaceChildren();
  if (shouldResume && video) video.play();
  if (isRefreshPending || wasSaved) refreshPage();
}

async function submitComment(text) {
  if (!commentDraft || commentDraft.isSaving) return;
  if (!text.trim()) { endComment(); return; }
  commentDraft.isSaving = true;
  const anchor = commentDraft.isAboutMoment
    ? {kind: 'moment', timeSeconds: commentDraft.momentSeconds} : {kind: 'episode'};
  const result = await callApi('POST', `/api/video/${EPISODE_ID}/comments`, {anchor, text});
  if (!result.isOk) {
    commentDraft.isSaving = false;
    if (result.status) showToast(translate('common.error.unknown'));
    return;
  }
  endComment(true);
}

// Comments ----------------------------------------------------------------------------------------------------------
// The moment a comment is about, or null for a comment about the whole episode.
function findMomentSeconds(anchor) {
  return anchor.kind === 'moment' ? anchor.timeSeconds : null;
}

async function patchComment(commentId, body) {
  const result = await callApi('PATCH', `/api/video/${EPISODE_ID}/comments/${encodeURIComponent(commentId)}`, body);
  if (result.isOk) await refreshPage(); else if (result.status) showToast(translate('common.error.unknown'));
}

function startEditing(comment) {
  editingCommentId = comment.id;
  showComments();
  const input = nodes.comments.querySelector('.text-edit');
  if (input) { input.focus(); input.setSelectionRange(input.value.length, input.value.length); growTextarea(input); }
}

function buildDeleteButton(comment) {
  const button = buildElement('button', {class: 'hb-icon-btn', type: 'button', title: translate('video.comment.delete'),
    'aria-label': translate('video.comment.delete')}, buildIcon('trash'));
  let disarmTimerId = null;
  const disarm = () => {
    clearTimeout(disarmTimerId);
    disarmTimerId = null;
    button.classList.remove('confirm');
    button.replaceChildren(buildIcon('trash'));
  };
  button.addEventListener('click', async (event) => {
    event.stopPropagation();
    if (!disarmTimerId) {
      button.classList.add('confirm');
      button.replaceChildren(translate('video.comment.confirmDelete'));
      disarmTimerId = setTimeout(disarm, 4000);
      return;
    }
    disarm();
    const result = await callApi('DELETE', `/api/video/${EPISODE_ID}/comments/${encodeURIComponent(comment.id)}`);
    if (result.isOk) refreshPage();
  });
  button.addEventListener('blur', disarm);
  button.addEventListener('keydown', (event) => { if (event.key === 'Escape') disarm(); });
  return button;
}

function buildComment(comment) {
  const momentSeconds = findMomentSeconds(comment.anchor);
  const isPlayable = !comment.isOnOlderVideo && momentSeconds !== null && !!video;
  const commentNode = buildElement('li', {class: 'comment' + (editingCommentId === comment.id ? ' editing' : ''),
    dataset: {id: comment.id}});
  const timeNode = momentSeconds === null
    ? buildElement('span', {class: 'ts none'}, translate('video.comment.noTime'))
    : isPlayable
      ? buildElement('button', {class: 'ts', type: 'button', title: translate('video.comment.jump'),
        onclick: (event) => { event.stopPropagation(); jumpTo(momentSeconds); }},
        formatTime(momentSeconds))
      : buildElement('span', {class: 'ts', title: translate('video.comment.olderTime')}, formatTime(momentSeconds));
  let textNode;
  if (editingCommentId === comment.id) {
    textNode = buildElement('textarea', {class: 'text-edit', rows: 1, 'aria-label': translate('video.comment.edit')});
    textNode.value = comment.text;
    const finishEditing = async (shouldSave) => {
      if (editingCommentId !== comment.id) return;
      editingCommentId = null;
      if (shouldSave && textNode.value.trim() && textNode.value !== comment.text) {
        await patchComment(comment.id, {text: textNode.value});
      } else if (isRefreshPending) {
        refreshPage();
      } else {
        showComments();
      }
    };
    textNode.addEventListener('input', () => growTextarea(textNode));
    textNode.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' && !event.shiftKey && !checkIsImeEnter(event)) {
        event.preventDefault();
        finishEditing(true);
      }
      if (event.key === 'Escape') { event.preventDefault(); finishEditing(false); }
    });
    textNode.addEventListener('blur', () => finishEditing(true));
    textNode.addEventListener('click', (event) => event.stopPropagation());
  } else {
    textNode = buildElement('div', {class: 'text'}, comment.text);
  }
  // the origin label and the hover actions share one slot: the label shows at rest, the actions on hover
  commentNode.append(timeNode, buildElement('div', {class: 'body'}, textNode),
    buildElement('div', {class: 'trailing'},
      comment.origin === 'chat'
        ? buildElement('span', {class: 'hb-meta origin'}, translate('video.comment.fromChat')) : null,
      buildElement('div', {class: 'actions'},
        buildElement('button', {class: 'hb-icon-btn', type: 'button', title: translate('video.comment.edit'),
          'aria-label': translate('video.comment.edit'),
          onclick: (event) => { event.stopPropagation(); startEditing(comment); }}, buildIcon('edit')),
        buildDeleteButton(comment))));
  if (isPlayable) {
    commentNode.addEventListener('click', () => {
      if (editingCommentId !== comment.id) jumpTo(momentSeconds);
    });
  }
  return commentNode;
}

// Comments about the whole episode first, then by moment.
function compareByTime(left, right) {
  return (findMomentSeconds(left.anchor) ?? -1) - (findMomentSeconds(right.anchor) ?? -1);
}

function buildCommentGroup(title, comments, isOpen, rememberOpen) {
  const group = buildElement('details', {class: 'group', open: isOpen},
    buildElement('summary', {}, buildIcon('chevron'), title),
    buildElement('ol', {class: 'comments'}, comments.map(buildComment)));
  group.addEventListener('toggle', () => rememberOpen(group.open));
  return group;
}

// The current video's open comments first; its handled comments and the comments on older videos collapse below.
function showComments() {
  const currentComments = pageData.comments.filter((comment) => !comment.isOnOlderVideo);
  const openComments = currentComments.filter((comment) => !comment.isResolved).sort(compareByTime);
  const handledComments = currentComments.filter((comment) => comment.isResolved).sort(compareByTime);
  const olderVideoComments = pageData.comments.filter((comment) => comment.isOnOlderVideo).sort(compareByTime);
  nodes.commentCount.textContent = pageData.comments.length ? String(pageData.comments.length) : '';
  const children = [];
  if (openComments.length) {
    children.push(buildElement('ol', {class: 'comments'}, openComments.map(buildComment)));
  } else {
    children.push(buildElement('div', {class: 'empty'},
      translate(pageData.comments.length ? 'video.comments.allHandled' : 'video.comments.empty')));
  }
  if (handledComments.length) {
    children.push(buildCommentGroup(translate('video.comments.handled', {count: handledComments.length}),
      handledComments, isHandledOpen, (value) => { isHandledOpen = value; }));
  }
  if (olderVideoComments.length) {
    children.push(buildCommentGroup(translate('video.comments.earlier', {count: olderVideoComments.length}),
      olderVideoComments, isOlderVideosOpen, (value) => { isOlderVideosOpen = value; }));
  }
  nodes.comments.replaceChildren(...children);
}

// Survey and sharing --------------------------------------------------------------------------------------------------
// The current video's answer of `kind`, or null when the question is not answered since the latest delivery.
function findSurveyAnswerValue(kind) {
  return pageData.surveyAnswers.find((answer) => answer.kind === kind)?.value ?? null;
}

// One survey question about the current video; pressing the chosen answer again clears it.
function buildSurveyQuestion(kind) {
  const stringKey = SURVEY_QUESTION_BY_KIND_MAP[kind].stringKey;
  return buildElement('div', {class: 'segmented', role: 'group', 'aria-label': translate(`video.${stringKey}.heading`)},
    SURVEY_QUESTION_BY_KIND_MAP[kind].values.map((value) => buildElement('button', {class: 'hb-btn', type: 'button',
      'aria-pressed': String(findSurveyAnswerValue(kind) === value),
      onclick: async () => {
        const nextValue = findSurveyAnswerValue(kind) === value ? null : value;
        const result = await callApi('PUT', `/api/video/${EPISODE_ID}/survey-answers/${kind}`, {value: nextValue});
        if (result.isOk) {
          pageData.surveyAnswers = [...pageData.surveyAnswers.filter((answer) => answer.kind !== kind),
            ...(nextValue === null ? [] : [{kind, value: nextValue}])];
          showSurvey();
          refreshPage();
        }
      }}, translate(`video.${stringKey}.${value}`))));
}

function showSurvey() {
  nodes.rating.replaceChildren(buildSurveyQuestion('rating'));
  nodes.watchDepth?.replaceChildren(buildSurveyQuestion('watch_depth'));
}

function showShareButton() {
  const button = buildElement('button', {class: 'hb-btn fill', type: 'button', disabled: !pageData.hasUnsharedFeedback,
    onclick: openShareDialog}, translate('video.share.button'));
  nodes.share.replaceChildren(buildElement('div', {class: 'share-row'}, button));
}

// The dialog lists what the user wrote since the last share. A share sends the episode's whole feedback (the agent's
// resolutions and gaps too), so anything added while the dialog is open goes with it.
async function openShareDialog() {
  const result = await callApi('GET', `/api/video/${EPISODE_ID}/share`);
  if (!result.isOk) { if (result.status) showToast(translate('common.error.unknown')); return; }
  const unsharedItems = result.body;
  if (unsharedItems.isEmpty) { pageData.hasUnsharedFeedback = false; showShareButton(); return; }
  const listNodes = [];
  unsharedItems.comments.forEach((comment) => {
    const momentSeconds = findMomentSeconds(comment.anchor);
    listNodes.push(buildElement('li', {},
      buildElement('span', {class: momentSeconds === null ? 'ts none' : 'ts'},
        momentSeconds === null ? translate('video.comment.noTime') : formatTime(momentSeconds)),
      buildElement('span', {class: 'text'}, comment.text)));
  });
  unsharedItems.surveyAnswers.forEach((answer) => {
    const stringKey = SURVEY_QUESTION_BY_KIND_MAP[answer.kind].stringKey;
    listNodes.push(buildElement('li', {}, buildElement('span', {class: 'text'},
      translate(`video.share.${stringKey}`, {answer: translate(`video.${stringKey}.${answer.value}`)}))));
  });
  const errorBanner = buildElement('div', {class: 'hb-banner error', hidden: true, role: 'alert'});
  const sendButton = buildElement('button', {class: 'hb-btn fill', type: 'submit', value: 'send'},
    translate('video.share.send'));
  const form = buildElement('form', {method: 'dialog'},
    buildElement('h3', {}, translate('video.share.title')),
    buildElement('p', {class: 'lead'}, translate('video.share.consent')),
    buildElement('div', {class: 'hb-meta'}, translate('video.share.thisTime')),
    buildElement('ul', {class: 'list'}, listNodes),
    buildElement('p', {class: 'note'}, buildElement('b', {}, translate('video.share.alsoLabel')), ' ',
      translate('video.share.also')),
    buildElement('p', {class: 'note'}, buildElement('b', {}, translate('video.share.neverLabel')), ' ',
      translate('video.share.never')),
    errorBanner,
    buildElement('div', {class: 'buttons'},
      buildElement('button', {class: 'hb-btn text', type: 'button', onclick: () => nodes.dialog.close()},
        translate('common.cancel')),
      sendButton));
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    sendButton.disabled = true;
    sendButton.textContent = translate('video.share.sending');
    const sendResult = await callApi('POST', `/api/video/${EPISODE_ID}/share`);
    if (sendResult.isOk) {
      nodes.dialog.close();
      showToast(translate(sendResult.body.isSent ? 'video.share.sent' : 'video.share.nothing'));
      refreshPage();
      return;
    }
    errorBanner.hidden = false;
    errorBanner.replaceChildren(buildElement('b', {}, translate('video.share.failed')),
      buildElement('div', {}, translate('video.share.failedBody')));
    sendButton.disabled = false;
    sendButton.textContent = translate('video.share.retry');
  });
  nodes.dialog.replaceChildren(form);
  nodes.dialog.showModal();
  sendButton.focus();
}

// Dev mode: what making the episode cost. The server works it out from the agent's transcripts when asked, so it is
// fetched once with the page instead of with the polled page JSON. Agent dollars come only from the local price table.
function formatUsd(value) {
  return '$' + (value || 0).toFixed(2);
}

function formatMinutes(seconds) {
  return (seconds / 60).toFixed(seconds >= 600 ? 0 : 1);
}

function formatTokenCount(count) {
  if (count >= 1e6) return (count / 1e6).toFixed(1) + 'M';
  return count >= 1000 ? Math.round(count / 1000) + 'K' : String(count);
}

async function fetchCostReport() {
  nodes.cost.replaceChildren(buildElement('div', {class: 'hb-meta'}, translate('video.cost.loading')));
  const result = await callApi('GET', `/api/video/${EPISODE_ID}/cost-report`);
  if (result.isOk) {
    showCostReport(result.body);
  } else {
    nodes.cost.replaceChildren(buildElement('div', {class: 'hb-meta'},
      translate('video.cost.unavailable', {reason: result.body.message || ''})));
  }
}

function showCostReport(costReport) {
  if (costReport.unavailableReason) {
    nodes.cost.replaceChildren(buildElement('div', {class: 'hb-meta'},
      translate('video.cost.unavailable', {reason: costReport.unavailableReason})));
    return;
  }
  const isPriced = costReport.episode.total.agentCostUsd !== null;
  const firstDelivery = costReport.firstDelivery;
  const noteKeyByStepMap = {audience_review: 'video.cost.rounds', scenes: 'video.cost.previews',
    render: 'video.cost.renders'};
  const buildCostRow = (label, costRow, note, isTotal) => buildElement('tr', {class: isTotal ? 'total' : undefined},
    buildElement('th', {scope: 'row'}, label, note ? buildElement('span', {class: 'hb-meta'}, note) : null),
    buildElement('td', {}, translate('video.cost.minutes', {minutes: formatMinutes(costRow.workingDurationSeconds)})),
    buildElement('td', {}, String(costRow.callCount)), buildElement('td', {}, formatTokenCount(costRow.tokenCount)),
    buildElement('td', {}, costRow.narrationCostUsd ? formatUsd(costRow.narrationCostUsd) : '–'),
    ...(isPriced
      ? [buildElement('td', {}, formatUsd(costRow.agentCostUsd)),
        buildElement('td', {}, formatUsd(costRow.agentCostUsd + costRow.narrationCostUsd))]
      : []));
  const columnNames = ['step', 'time', 'calls', 'tokens', 'narration', ...(isPriced ? ['agent', 'total'] : [])];
  // Each group under its name with its steps and their total: the series' planning, then this episode up to its first
  // delivery. The work after the first delivery is left out.
  const buildCostGroup = (name, rows) => (rows.length ? buildElement('tbody', {}, buildElement('tr', {class: 'group'},
    buildElement('th', {scope: 'colgroup', colspan: columnNames.length}, translate('video.cost.group.' + name))),
  rows) : null);
  const totalNote = [
    costReport.elapsedSeconds
      ? translate('video.cost.elapsed', {minutes: Math.round(costReport.elapsedSeconds / 60)}) : null,
    firstDelivery?.durationSeconds
      ? translate('video.cost.video', {minutes: (firstDelivery.durationSeconds / 60).toFixed(1),
        sceneCount: firstDelivery.sceneCount})
      : null].filter(Boolean).join(' · ');
  const buildGroupRows = (group, note) => (group ? [...group.steps.map((step) => buildCostRow(
    translate('video.cost.step.' + step.step), step,
    noteKeyByStepMap[step.step] && step.count !== null ? translate(noteKeyByStepMap[step.step], {count: step.count})
      : null)),
  buildCostRow(translate('video.cost.total'), group.total, note, true)] : []);
  const episodeRows = buildGroupRows(costReport.episode, totalNote);
  const planningRows = buildGroupRows(costReport.planning, null);
  const unpricedModelNames = [...new Set([costReport.episode, costReport.planning]
    .filter(Boolean).flatMap((group) => group.total.unpricedModelNames))];
  nodes.cost.replaceChildren(...[
    buildElement('table', {class: 'cost-table'},
      buildElement('thead', {}, buildElement('tr', {},
        columnNames.map((name) => buildElement('th', {scope: 'col'}, translate('video.cost.' + name))))),
      buildCostGroup('series', planningRows), buildCostGroup(firstDelivery ? 'episode' : 'episodeSoFar', episodeRows)),
    costReport.priceTableProblem
      ? buildElement('p', {class: 'hb-meta'},
        translate('video.cost.priceTableProblem', {problem: costReport.priceTableProblem}))
      : isPriced ? null
        : buildElement('p', {class: 'hb-meta'}, translate('video.cost.noteUsage', {path: costReport.priceTablePath})),
    unpricedModelNames.length
      ? buildElement('p', {class: 'hb-meta'}, translate('video.cost.unpriced', {models: unpricedModelNames.join(', ')}))
      : null,
  ].filter(Boolean));
}

// Page --------------------------------------------------------------------------------------------------------------
function formatDate(date) {
  return date.toLocaleString(BOOT.languageCode, {dateStyle: 'medium', timeStyle: 'short'});
}

function showNotices() {
  const banners = [];
  const delivery = pageData.delivery;
  if (!delivery.hasFile) {
    banners.push(buildElement('div', {class: 'hb-banner warn', role: 'alert'},
      buildElement('b', {}, translate('video.missing.title')),
      buildElement('div', {}, translate('video.missing.body', {path: delivery.filePath}))));
  }
  if (nodes.newDelivery) banners.push(nodes.newDelivery);
  nodes.notices.replaceChildren(...banners);
}

function showHead() {
  const episodeLabel = EPISODE_ID.toUpperCase();
  document.title = `${episodeLabel} ${pageData.episode.title} · ${pageData.seriesTitle}`;
  nodes.eyebrow.replaceChildren(pageData.seriesTitle, buildElement('span', {class: 'hb-dot'}), episodeLabel);
  nodes.title.textContent = pageData.episode.title;
  // the version that delivered the video, when it is not the one running now (the navbar's)
  const deliveryVersion = pageData.delivery.explainerStudioVersion;
  nodes.meta.replaceChildren(...[
    buildElement('div', {},
      translate('video.delivered', {date: formatDate(new Date(pageData.delivery.deliveredAt))})),
    deliveryVersion && deliveryVersion !== pageData.explainerStudioVersion
      ? buildElement('div', {},
        translate('video.version', {version: translate('common.version', {version: deliveryVersion})}))
      : null].filter(Boolean));
  const deliveredEpisodes = pageData.episodes;
  if (deliveredEpisodes.length > 1) {
    const episodeSelect = buildElement('select', {class: 'hb-select', 'aria-label': translate('video.otherEpisodes')},
      deliveredEpisodes.map((episode) => buildElement('option', {value: episode.id, selected: episode.id === EPISODE_ID},
        `${episode.id.toUpperCase()} · ${episode.title}`)));
    episodeSelect.addEventListener('change', () => {
      window.location.href = `${BOOT.baseUrl}/video/${episodeSelect.value}`;
    });
    nodes.switcher.replaceChildren(episodeSelect);
  } else {
    nodes.switcher.replaceChildren();
  }
}

function showPage() {
  showHead();
  showNotices();
  showComments();
  showSurvey();
  showShareButton();
}

function mountPage() {
  const appNode = document.getElementById('app');
  nodes.switcher = buildElement('div', {});
  nodes.eyebrow = buildElement('div', {class: 'hb-eyebrow'});
  nodes.title = buildElement('h1', {class: 'hb-title'});
  nodes.meta = buildElement('div', {class: 'hb-meta'});
  nodes.notices = buildElement('div', {class: 'hb-section'});
  nodes.composer = buildElement('div', {class: 'composer', hidden: true});
  nodes.comments = buildElement('div', {});
  nodes.commentCount = buildElement('span', {class: 'hb-meta'});
  nodes.rating = buildElement('div', {});
  nodes.watchDepth = pageData.isDevModeOn ? buildElement('div', {}) : null;
  nodes.share = buildElement('div', {});
  nodes.cost = buildElement('div', {class: 'cost'});
  nodes.dialog = buildElement('dialog', {'aria-label': translate('video.share.title')});
  const mediaUrl = `${BOOT.baseUrl}/media/${EPISODE_ID}`;
  if (pageData.delivery.hasFile) {
    video = buildElement('video', {id: 'video', class: 'hb-video', controls: true, preload: 'metadata',
      playsinline: true, poster: pageData.delivery.hasCover ? `${mediaUrl}/cover.png` : undefined,
      src: `${mediaUrl}/video.mp4`});
    video.append(...pageData.delivery.subtitles.map((subtitles) => buildElement('track', {kind: 'subtitles',
      src: `${mediaUrl}/subtitles.${encodeURIComponent(subtitles.languageCode)}.vtt`, srclang: subtitles.languageCode,
      label: translate('video.subtitles')})));
    video.addEventListener('loadedmetadata', applySubtitles);
  }
  nodes.subtitles = video && pageData.delivery.subtitles.length
    ? buildElement('button', {class: 'hb-btn outline', type: 'button', 'aria-pressed': String(isShowingSubtitles),
      onclick: toggleSubtitles}, translate('video.subtitles'), buildElement('kbd', {}, 'C'))
    : null;
  nodes.theaterMode = video
    ? buildElement('button', {class: 'hb-btn outline', type: 'button', 'aria-pressed': String(isTheaterModeOn),
      onclick: toggleTheaterMode}, translate('video.theaterMode'), buildElement('kbd', {}, 'T'))
    : null;
  const keyHints = video && buildElement('div', {class: 'keys hb-meta'},
    buildElement('span', {}, buildElement('kbd', {}, translate('video.keys.space')), translate('video.keys.play')),
    buildElement('span', {}, buildElement('kbd', {}, '←'), buildElement('kbd', {}, '→'),
      translate('video.keys.seek', {seconds: SEEK_SECONDS})));
  appNode.replaceChildren(...[
    buildElement('div', {class: 'topnav'},
      buildElement('a', {class: 'hb-btn text small', href: `${BOOT.baseUrl}/plan`}, buildIcon('back'),
        translate('video.backToPlan')),
      nodes.switcher),
    buildElement('div', {class: 'hb-head'}, nodes.eyebrow, nodes.title, nodes.meta),
    nodes.notices,
    video,
    buildElement('div', {class: 'toolbar'},
      buildElement('button', {class: 'hb-btn fill', type: 'button', onclick: startComment}, buildIcon('plus'),
        translate('video.addComment'), buildElement('kbd', {}, 'M')),
      nodes.subtitles, nodes.theaterMode, keyHints),
    nodes.composer,
    buildElement('section', {class: 'hb-section'},
      buildElement('h2', {}, translate('video.comments.heading'), nodes.commentCount),
      buildElement('p', {class: 'hb-lead'}, translate('video.comments.lead')), nodes.comments),
    buildElement('section', {class: 'hb-section'}, buildElement('h2', {}, translate('video.rating.heading')),
      nodes.rating),
    nodes.watchDepth && buildElement('section', {class: 'hb-section'},
      buildElement('h2', {}, translate('video.watchDepth.heading')), nodes.watchDepth),
    pageData.isDevModeOn
      ? buildElement('section', {class: 'hb-section'}, buildElement('h2', {}, translate('video.cost.heading')),
        nodes.cost)
      : null,
    buildElement('section', {class: 'hb-section'}, buildElement('h2', {}, translate('video.share.heading')),
      buildElement('p', {class: 'hb-lead'}, translate('video.share.lead')), nodes.share),
    nodes.dialog].filter(Boolean));  // no video element when the file is missing, no dev mode sections without it
  showPage();
  applySubtitles();
  applyTheaterMode();
  if (pageData.isDevModeOn) fetchCostReport();
}

async function refreshPage() {
  if (commentDraft || editingCommentId) { isRefreshPending = true; return; }
  isRefreshPending = false;
  const nextPageJson = await fetchPageJson();
  if (!nextPageJson) return;
  if (nextPageJson.languageCode !== BOOT.languageCode) { window.location.reload(); return; }
  const isRedelivered = pageData && nextPageJson.delivery.deliveredAt !== pageData.delivery.deliveredAt;
  pageData = nextPageJson;
  pageDigest = nextPageJson.pageDigest;
  if (isRedelivered) {
    if (!video || video.paused || video.ended) { window.location.reload(); return; }
    nodes.newDelivery = buildElement('div', {class: 'hb-banner ok'},
      buildElement('b', {}, translate('video.redelivered.title')),
      buildElement('div', {class: 'actions'}, buildElement('button', {class: 'hb-btn outline small', type: 'button',
        onclick: () => window.location.reload()}, translate('video.redelivered.reload'))));
  }
  showPage();
}

window.addEventListener('keydown', (event) => {
  if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.altKey || !pageData) return;
  if (checkIsTyping(event.target) || (nodes.dialog && nodes.dialog.open)) return;
  const key = event.key.length === 1 ? event.key.toLowerCase() : event.key;
  if (key === ' ') togglePlay();
  else if (key === 'ArrowLeft') seekBy(-SEEK_SECONDS);
  else if (key === 'ArrowRight') seekBy(SEEK_SECONDS);
  else if (key === 'm') startComment();
  else if (key === 'c') toggleSubtitles();
  else if (key === 't') toggleTheaterMode();
  else return;
  event.preventDefault();
  event.stopPropagation();
}, true);

(async () => {
  pageData = await fetchPageJson();
  if (!pageData) return;
  pageDigest = pageData.pageDigest;
  mountPage();
  watchPageDigest(`?episodeId=${encodeURIComponent(EPISODE_ID)}`, () => pageDigest, () => refreshPage());
})();
