// The video page: the latest delivery of one episode, its comments, the survey (a rating, and the watch depth in dev
// mode) and sharing with the team.
// Keys: Space plays or pauses, the arrows move 5 s, M adds a comment (the video pauses; Enter saves and plays on,
// Esc cancels), C turns subtitles on or off, and T, N and W turn theater mode, the chapters view and the whiteboard on
// or off; a letter key works whatever the keyboard layout or input method types with it (resolveShortcutKey). The video
// element is made once; everything else is shown again from the server's JSON whenever feedback.json or the delivery
// changes, so the agent's changes show up without a reload.
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

// Whether a setting remembered for the next page is on.
function loadIsOn(name) {
  try { return localStorage.getItem(name) === 'on'; } catch (error) { return false; }
}

function saveIsOn(name, isOn) {
  try { localStorage.setItem(name, isOn ? 'on' : 'off'); } catch (error) { /* private window */ }
}

let isShowingSubtitles = loadIsOn('subtitles');
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

// A button with only an icon, named by its tooltip, as the app's.
function buildIconButton(iconName, label, attributes) {
  return buildElement('button', {class: 'hb-icon-btn', type: 'button', 'aria-label': label, 'data-tooltip': label,
    ...attributes}, buildIcon(iconName));
}

// Player ------------------------------------------------------------------------------------------------------------
function applySubtitles() {
  if (video && video.textTracks.length) video.textTracks[0].mode = isShowingSubtitles ? 'showing' : 'hidden';
  if (nodes.subtitles) nodes.subtitles.setAttribute('aria-pressed', String(isShowingSubtitles));
}

function toggleSubtitles() {
  if (!pageData.delivery.subtitles.length) return;
  isShowingSubtitles = !isShowingSubtitles;
  saveIsOn('subtitles', isShowingSubtitles);
  applySubtitles();
}

// Theater mode, the chapters view and the whiteboard ----------------------------------------------------------------
// Three modes in the toolbar, one at a time: turning one on turns the other off.
// - theater mode: the video as large as the window allows, on a black band across the page, with the toolbar still
//   in view under it;
// - the chapters view: the episode to read from top to bottom (notes.yaml), each chapter a large frame beside its
//   scenes, each scene a key frame, a title, where it starts and its core idea. Choosing a scene plays it in its
//   chapter's frame: the page's one video element moves there, follows the video into the next chapter as it plays on,
//   and goes back under the title when the view closes;
// - the whiteboard: the series' whiteboard (below) in place of the video, filling the page under the toolbar; with no
//   video in view, the comment and subtitle buttons are off and the rest of the page is hidden.
// The mode on is in the page's address (`?mode=chapters`), so a reload, Back and Forward, and the same address in
// another tab or browser show the same screen, and switching episodes keeps it; a page opened without it (from the plan
// page, or by `video open`) shows the video with none on. Showing or hiding the whiteboard changes what the page shows,
// as going to another page does, so it adds a history entry that Back returns from; theater mode and the chapters view
// only change the layout and update the current entry. Subtitles are a preference for every video, remembered in the
// browser.
const MODE_QUERY_NAME = 'mode';
const MODE_NAMES = ['theater', 'chapters', 'whiteboard'];  // in the toolbar's order
let modeName = null;  // the mode on, or null; it shows once it is available (resolveShownModeName)

// The mode the page's address turns on; a name it does not know is ignored.
function setModeFromUrl() {
  const urlModeName = new URLSearchParams(window.location.search).get(MODE_QUERY_NAME);
  modeName = MODE_NAMES.includes(urlModeName) ? urlModeName : null;
}

// `?mode=...` with the mode on now, or '' with none.
function buildModeQuery() {
  return modeName ? `?${MODE_QUERY_NAME}=${modeName}` : '';
}

// The page's address with the mode on now, and the rest of its query but the sign-in's id, which is read once.
function buildPageUrl() {
  const pageUrl = new URL(window.location.href);
  pageUrl.searchParams.delete(MODE_QUERY_NAME);
  pageUrl.searchParams.delete(SIGN_IN_QUERY_NAME);
  if (modeName) pageUrl.searchParams.set(MODE_QUERY_NAME, modeName);
  return pageUrl.pathname + pageUrl.search + pageUrl.hash;
}

// Puts the mode on now in the page's address: in a new history entry when the whiteboard showed or hid
// (`wasWhiteboardShown` is whether it showed before the change), else in the current one.
function recordModeInUrl(wasWhiteboardShown) {
  const nextUrl = buildPageUrl();
  if (nextUrl === window.location.pathname + window.location.search + window.location.hash) return;
  if (checkIsWhiteboardModeShown() !== wasWhiteboardShown) history.pushState(null, '', nextUrl);
  else history.replaceState(history.state, '', nextUrl);
}

setModeFromUrl();

// Back and Forward between this page's history entries: the mode in their addresses.
window.addEventListener('popstate', () => {
  setModeFromUrl();
  applyMode();
});

// Whether a mode can show: every mode needs the video, the chapters view chapters that fit it, and the whiteboard what
// the page server holds for it.
function checkIsModeAvailable(name) {
  if (!video) return false;
  if (name === 'chapters') return Boolean(pageData.chapters);
  if (name === 'whiteboard') return Boolean(whiteboard.page);
  return true;
}

// The mode the page shows: the one on, once it is available; null for none.
function resolveShownModeName() {
  return modeName && checkIsModeAvailable(modeName) ? modeName : null;
}

function checkIsChaptersModeShown() {
  return resolveShownModeName() === 'chapters';
}

function checkIsWhiteboardModeShown() {
  return resolveShownModeName() === 'whiteboard';
}

function applyMode() {
  const shownModeName = resolveShownModeName();
  for (const name of MODE_NAMES) document.body.classList.toggle(`${name}-mode`, shownModeName === name);
  for (const [name, button] of [['theater', nodes.theaterMode], ['chapters', nodes.chaptersMode],
    ['whiteboard', nodes.whiteboardMode]]) {
    if (!button) continue;
    button.setAttribute('aria-pressed', String(shownModeName === name));
    button.hidden = !checkIsModeAvailable(name);
  }
  const isWhiteboardShown = shownModeName === 'whiteboard';
  if (isWhiteboardShown && video && !video.paused) video.pause();
  for (const button of [nodes.addComment, nodes.subtitles]) if (button) button.disabled = isWhiteboardShown;
  // the whiteboard is the whole page and does not scroll, and a reload opens on it, not where the page was
  history.scrollRestoration = isWhiteboardShown ? 'manual' : 'auto';
  if (isWhiteboardShown) { window.scrollTo(0, 0); mountWhiteboard(); }
  placeVideo();
  showChapterProgress();
}

// Turns a mode on, or off when it shows, and brings into view what changed under the toolbar: the video in theater
// mode, the chapter the video is in when the chapters view opens (the page's top before the video has started), and the
// video when the chapters view closes.
function toggleMode(name) {
  if (!checkIsModeAvailable(name)) return;
  const wasWhiteboardShown = checkIsWhiteboardModeShown();
  const wasChaptersShown = checkIsChaptersModeShown();
  modeName = resolveShownModeName() === name ? null : name;
  recordModeInUrl(wasWhiteboardShown);
  applyMode();
  if (modeName === 'theater') video.scrollIntoView({block: 'start'});
  else if (modeName === 'chapters' && !checkIsVideoHome()) video.closest('.chapter').scrollIntoView({block: 'start'});
  else if (modeName === 'chapters') window.scrollTo(0, 0);
  else if (wasChaptersShown && !modeName) video.scrollIntoView({block: 'nearest'});
}

function openWhiteboardMode() {
  if (!checkIsWhiteboardModeShown()) toggleMode('whiteboard');
}

let chaptersJson = null;

function getMediaUrl(name) {
  return `${BOOT.baseUrl}/media/${EPISODE_ID}/${name}`;
}

function getFrameUrl(beatId) {
  return getMediaUrl(`frames/${encodeURIComponent(beatId)}.jpg`);
}

function checkIsVideoHome() {
  return nodes.videoHome.contains(video);
}

// Whether the video has started, so that the chapters view plays it in a chapter rather than showing key frames.
function checkHasVideoStarted() {
  return video.currentTime > 0 || !video.paused || video.played.length > 0;
}

// The chapter a moment of the video is in, by its index; the last one after the last scene.
function findChapterIndex(seconds) {
  const chapterIndex = pageData.chapters.findIndex((chapter) => seconds < chapter.scenes.at(-1).endSeconds);
  return chapterIndex === -1 ? pageData.chapters.length - 1 : chapterIndex;
}

// Puts the page's one video element where it plays: in the chapters view, once it has started, in the frame of the
// chapter it is in, with the composer under it; otherwise under the title, with the composer under the toolbar. It
// stays where it is in full screen and picture in picture, which moving it would end.
function placeVideo() {
  if (!video || document.fullscreenElement === video || document.pictureInPictureElement === video) return;
  const chapterSection = checkIsChaptersModeShown() && checkHasVideoStarted()
    ? nodes.chapterSections[findChapterIndex(video.currentTime)] : null;
  const videoParent = chapterSection ? chapterSection.frame : nodes.videoHome;
  if (video.parentNode !== videoParent) {
    videoParent.replaceChildren(video);
    for (const {frame, cover} of nodes.chapterSections || []) if (!frame.firstChild) frame.append(cover);
  }
  const composerPrevious = chapterSection ? chapterSection.frame : nodes.toolbar;
  if (nodes.composer.previousElementSibling !== composerPrevious) composerPrevious.after(nodes.composer);
}

// Whether a part of the page is on the screen, under the page's header.
function checkIsInView(node) {
  const rect = node.getBoundingClientRect();
  const middle = rect.top + rect.height / 2;
  return rect.height > 0 && middle > 48 && middle < window.innerHeight;
}

// As the video plays into another chapter, or the keys move it there, it moves to that chapter's frame, and a viewer
// who was watching it is taken down the page with it. Dragged along its own timeline, it moves once it plays again
// (Chrome pauses it for the drag), since moving it would end the drag. Out of the chapters view, a video kept in a
// frame by full screen goes back.
function followVideo() {
  if (!checkIsChaptersModeShown()) { placeVideo(); return; }
  const previousParent = video.parentNode;
  const wasInView = checkIsInView(previousParent);
  placeVideo();
  if (video.parentNode === previousParent || checkIsVideoHome()) return;
  if (previousParent === nodes.videoHome) showVideo();
  else if (wasInView) video.closest('.chapter').scrollIntoView({behavior: 'smooth', block: 'start'});
}

// The video in view, in its chapter's frame in the chapters view.
function showVideo() {
  (checkIsVideoHome() ? video : video.parentNode).scrollIntoView({behavior: 'smooth', block: 'nearest'});
}

// Plays from a scene's or a chapter's start, in view.
function playFrom(seconds) {
  if (!video) return;
  video.currentTime = seconds;
  video.play();
  placeVideo();
  showVideo();
}

// The scene the video is in, with how far into it, while it plays in the chapters view.
function showChapterProgress() {
  if (!nodes.sceneRows) return;
  const isInChapter = Boolean(video) && checkIsChaptersModeShown() && !checkIsVideoHome();
  const seconds = video ? video.currentTime : 0;
  for (const {scene, row, bar} of nodes.sceneRows) {
    const isCurrent = isInChapter && seconds >= scene.startSeconds && seconds < scene.endSeconds;
    row.classList.toggle('current', isCurrent);
    bar.style.width = isCurrent
      ? `${(100 * (seconds - scene.startSeconds) / (scene.endSeconds - scene.startSeconds)).toFixed(1)}%` : '0';
  }
}

function buildChapters(chapters) {
  nodes.sceneRows = [];
  nodes.chapterWhiteboardButtons = [];
  nodes.chapterSections = chapters.map((chapter, chapterIndex) => {
    const first = chapter.scenes[0], last = chapter.scenes.at(-1);
    const minutes = Math.max(1, Math.round((last.endSeconds - first.startSeconds) / 60));
    // the chapter's frame before the video plays in it: its first scene's key frame, which plays the chapter
    const playLabel = translate('chapters.playFrom', {time: formatTime(first.startSeconds)});
    const cover = buildElement('button', {class: 'cover', type: 'button', 'aria-label': playLabel,
      onclick: () => playFrom(first.startSeconds)},
    buildElement('img', {src: getFrameUrl(first.keyFrame), alt: ''}),
    buildElement('span', {class: 'play'}, buildIcon('play'), playLabel));
    const frame = buildElement('div', {class: 'frame'}, cover);
    const rows = chapter.scenes.map((scene) => {
      const bar = buildElement('i', {});
      const row = buildElement('div', {class: 'scene', role: 'button', tabindex: '0',
        onclick: () => playFrom(scene.startSeconds),
        onkeydown: (event) => {
          if (event.key === 'Enter') { event.preventDefault(); playFrom(scene.startSeconds); }
        }},
      buildElement('div', {class: 'thumb'}, buildElement('img', {src: getFrameUrl(scene.keyFrame), alt: '',
        loading: 'lazy'}), buildElement('span', {class: 'bar'}, bar)),
      buildElement('div', {class: 'body'},
        buildElement('div', {class: 'title'}, buildElement('b', {}, scene.title),
          buildElement('span', {class: 'hb-meta'}, formatTime(scene.startSeconds))),
        buildElement('p', {}, scene.summary)));
      nodes.sceneRows.push({scene, row, bar});
      return row;
    });
    const whiteboardButton = buildIconButton('whiteboard', translate('chapters.viewOnWhiteboard'),
      {hidden: true, onclick: () => showChapterOnWhiteboard(chapter.id)});
    nodes.chapterWhiteboardButtons.push(whiteboardButton);
    const section = buildElement('section', {class: 'chapter'},
      buildElement('div', {class: 'chapter-head'},
        buildElement('h3', {},
          buildElement('span', {class: 'number'}, translate('chapters.chapter', {number: chapterIndex + 1})),
          chapter.title),
        buildElement('span', {class: 'hb-meta'}, translate('chapters.minutes', {minutes})),
        whiteboardButton),
      buildElement('div', {class: 'chapter-body'}, buildElement('div', {class: 'player'}, frame),
        buildElement('div', {class: 'scenes'}, rows)));
    return {section, frame, cover};
  });
  nodes.chapters.replaceChildren(...nodes.chapterSections.map(({section}) => section));
  showChapterWhiteboardButtons();
}

// The chapters as the agent last wrote them; the video and the composer go back under the title first, and back
// into a chapter by applyMode.
function showChapters() {
  const json = JSON.stringify(pageData.chapters);
  if (json === chaptersJson) return;
  chaptersJson = json;
  if (video && !checkIsVideoHome()) nodes.videoHome.replaceChildren(video);
  nodes.toolbar.after(nodes.composer);
  if (pageData.chapters) {
    buildChapters(pageData.chapters);
  } else {
    nodes.sceneRows = null;
    nodes.chapterSections = null;
    nodes.chapters.replaceChildren();
  }
  applyMode();
}

// Series whiteboard ------------------------------------------------------------------------------------------------
// The series' whiteboard is the Heptabase web app's embedded whiteboard page in an iframe. Studio lays the
// cards out and Heptabase draws them: the embedded page measures the cards (only Heptabase's renderer knows how tall
// a card is), this page lays them out by the rules below, and the embedded page shows them. Until the user saves, that
// preview stays on this computer.
// Saving takes this tab to Heptabase's sign-in when needed and back (`SIGN_IN_QUERY_NAME` names the sign-in; the same
// tab, not a new one, because some browsers, the Claude app's, would open a new window in the same tab), and the save
// goes on by itself. The page server then puts every episode on a new whiteboard in the user's Heptabase. Once saved,
// the embedded page reads the whiteboard itself, with an access token; when the page opens, the episodes delivered
// since are laid out under everything on the whiteboard and added, the iframe loading in the background for that.
// Heptabase draws what it holds from then on, including what the user changed there.
const SIGN_IN_QUERY_NAME = 'heptabaseSignIn';
// The layout rules (Studio's, and expected to change): episodes one under the next; in an episode, its chapters side
// by side, coloured in turn; in a chapter, a column per scene; in a column, a card one row below the cards of the
// column that lead to it, each row centred. Heptabase draws a section's title above its box, so a section needs no
// room inside for it.
const WHITEBOARD_LAYOUT = {cardWidth: 520, episodeGap: 360, episodePadding: 40, chapterGap: 120, chapterPadding: 40,
  sceneGap: 64, rowGap: 64};
const CHAPTER_COLOR_NAMES = ['blue', 'yellow', 'green', 'purple'];
const FRAME_READY_TIMEOUT_MILLISECONDS = 30000;
const MEASURE_TIMEOUT_MILLISECONDS = 30000;
const whiteboard = {
  page: null,  // the page server's api/series-whiteboard
  frame: null,
  origin: null,
  isFrameReady: false,
  frameReadyTimerId: null,
  view: 'loading',  // what the whiteboard shows: loading | preview | saved | unreadable | empty
  unreadableReason: null,  // trashed | deleted | forbidden | signedOut | unauthorized | network | notMeasured
  previewLayout: null,
  shownWhiteboard: null,  // {title, spaceId, contentBounds} of the saved whiteboard on show
  signInStatus: null,  // how the sign-in this page came back from ended, until the next save
  isSaveRequested: false,  // back from a sign-in that a save started: save once the preview is laid out
  isSaving: false,
  saveFailure: null,
  isImporting: false,
  hasFocusedDuringImport: false,  // the user chose a section while episodes were being added
  importFailure: null,
  hasImportStarted: false,  // the episodes to add are added once per page load, then only with Retry
  // The section ({episodeId, chapterId}) the embedded page's first whiteboard opens on: this episode's, or a chapter's
  // chosen before the whiteboard showed; null once a whiteboard has shown. Later whiteboards keep the viewport, and
  // focusObject moves it.
  focusSection: {episodeId: EPISODE_ID, chapterId: null},
  hasAskedToShow: false,  // the embedded page was sent showObjects or showWhiteboard
  lastRequestNumber: 0,
  // What to do with the reply to each request sent and not answered yet, by its requestId, which the reply repeats:
  // measureCards, showWhiteboard and refreshWhiteboard. A reply to no request here is ignored.
  replyHandlerByRequestIdMap: new Map(),
  loadedImageByKeyMap: new Map(),  // {version, blob} of each picture fetched
};

async function fetchWhiteboardPage(signInId) {
  const query = signInId ? `?signInId=${encodeURIComponent(signInId)}` : '';
  const result = await callApi('GET', `/api/series-whiteboard${query}`);
  return result.isOk ? result.body : null;
}

// The page server's whiteboard data as it is now; the last one stays when it cannot be read.
async function refetchWhiteboardPage() {
  whiteboard.page = (await fetchWhiteboardPage()) || whiteboard.page;
}

function postToWhiteboard(message) {
  if (whiteboard.isFrameReady) whiteboard.frame.contentWindow.postMessage(message, whiteboard.origin);
}

// A message that gets a reply, under a new requestId; `handleReply` takes the reply. Returns the requestId, or null
// when the embedded page is not ready to take it.
function postRequestToWhiteboard(message, handleReply) {
  if (!whiteboard.isFrameReady) return null;
  whiteboard.lastRequestNumber += 1;
  const requestId = String(whiteboard.lastRequestNumber);
  whiteboard.replyHandlerByRequestIdMap.set(requestId, handleReply);
  postToWhiteboard({...message, requestId});
  return requestId;
}

// Moves the viewport to a section the user chose. Chosen while episodes are being added, it stays after they are.
function focusWhiteboardOnUserChoice(focusTarget) {
  if (whiteboard.isImporting) whiteboard.hasFocusedDuringImport = true;
  postToWhiteboard({type: 'focusObject', focusTarget});
}

// The episodes on the whiteboard: those saved, or those in the preview.
function listWhiteboardEpisodeIds() {
  const page = whiteboard.page;
  return page.savedWhiteboard ? page.savedWhiteboard.importedEpisodeIds
    : page.episodesToAdd.map((episode) => episode.id);
}

// A chapter section's whiteboard key; an episode's section has the episode's id.
function getChapterSectionKey(episodeId, chapterId) {
  return `${episodeId}/${chapterId}`;
}

// How the embedded page finds an episode's or a chapter's section: in the preview by its key, on the saved whiteboard
// by the id Heptabase has for it. A chapter the saved whiteboard has no section for (the episode's chapters changed
// after it was added) falls back to its episode; none when the whiteboard has neither.
function resolveWhiteboardFocusTarget({episodeId, chapterId}) {
  const chapterKey = chapterId ? getChapterSectionKey(episodeId, chapterId) : null;
  const savedWhiteboard = whiteboard.page.savedWhiteboard;
  if (!savedWhiteboard) return {key: chapterKey || episodeId};
  const sectionId = (chapterKey && savedWhiteboard.sectionIdByKeyMap[chapterKey])
    || savedWhiteboard.sectionIdByKeyMap[episodeId];
  return sectionId ? {objectId: sectionId} : undefined;
}

// showObjects or showWhiteboard. Until a whiteboard has shown, it opens on `focusSection`, or on the last episode when
// that section's episode is not on the whiteboard; the embedded page opens on everything when it has none of them.
// Shown means sent for showObjects, which has no answer, and whiteboardShown for showWhiteboard, so a whiteboard that
// could not be read still opens there when it is read again.
function postShowToWhiteboard(message) {
  if (!whiteboard.isFrameReady) return;
  const focusSection = whiteboard.focusSection;
  const episodeIds = listWhiteboardEpisodeIds();
  const focusTarget = !focusSection || !episodeIds.length ? undefined
    : resolveWhiteboardFocusTarget(episodeIds.includes(focusSection.episodeId) ? focusSection
      : {episodeId: episodeIds.at(-1), chapterId: null});
  whiteboard.hasAskedToShow = true;
  if (message.type === 'showObjects') {
    whiteboard.focusSection = null;
    postToWhiteboard({...message, focusTarget});
  } else {
    postRequestToWhiteboard({...message, focusTarget}, handleWhiteboardReadReply);
  }
}

// A chapter's "View on whiteboard", there only when this episode is on the whiteboard.
function showChapterWhiteboardButtons() {
  const isOnWhiteboard = Boolean(whiteboard.page) && listWhiteboardEpisodeIds().includes(EPISODE_ID);
  for (const button of nodes.chapterWhiteboardButtons || []) button.hidden = !isOnWhiteboard;
}

// The whiteboard view, on the chapter's section. Before a whiteboard has shown, the first one opens there; a
// focusObject also follows a show already sent, which the embedded page handles in order.
function showChapterOnWhiteboard(chapterId) {
  const focusSection = {episodeId: EPISODE_ID, chapterId};
  openWhiteboardMode();
  if (whiteboard.focusSection) whiteboard.focusSection = focusSection;
  if (!whiteboard.hasAskedToShow) return;
  const focusTarget = resolveWhiteboardFocusTarget(focusSection);
  if (focusTarget) focusWhiteboardOnUserChoice(focusTarget);
}

function formatEpisodeNumbers(episodes) {
  return episodes.map((episode) => episode.number)
    .join(document.documentElement.lang.startsWith('zh') ? '、' : ', ');
}

function listEpisodeCards(episodes) {
  return episodes.flatMap((episode) => episode.chapters.flatMap((chapter) =>
    chapter.scenes.flatMap((scene) => scene.cards)));
}

// The cards' pictures as Blobs, each fetched once per version.
async function loadWhiteboardImages() {
  const isLoaded = (image) => whiteboard.loadedImageByKeyMap.get(image.key)?.version === image.version;
  await Promise.all(whiteboard.page.images.filter((image) => !isLoaded(image)).map(async (image) => {
    const response = await fetch(BOOT.baseUrl + image.url, {cache: 'no-store'}).catch(() => null);
    if (response && response.ok) {
      whiteboard.loadedImageByKeyMap.set(image.key, {version: image.version, blob: await response.blob()});
    }
  }));
  return whiteboard.page.images.filter(isLoaded)
    .map((image) => ({key: image.key, blob: whiteboard.loadedImageByKeyMap.get(image.key).blob}));
}

// The cards' heights as Heptabase draws them at the layout's card width: {heights}, or {failure} when the embedded
// page did not answer (network) or could not draw a card (notMeasured).
function measureCards(episodes, images) {
  const cards = listEpisodeCards(episodes);
  return new Promise((resolve) => {
    let timerId = null;
    const requestId = postRequestToWhiteboard({type: 'measureCards', cardWidth: WHITEBOARD_LAYOUT.cardWidth,
      cards: cards.map((card) => ({key: card.key, content: card.content})), files: images}, (reply) => {
      clearTimeout(timerId);
      const heights = reply.heights || {};
      resolve(cards.every((card) => heights[card.key] > 0) ? {heights} : {failure: 'notMeasured'});
    });
    timerId = setTimeout(() => {
      whiteboard.replyHandlerByRequestIdMap.delete(requestId);
      resolve({failure: 'network'});
    }, MEASURE_TIMEOUT_MILLISECONDS);
  });
}

// A scene's cards in rows: a card goes one row below the latest of the scene's earlier cards that lead to it, so that
// an argument reads downwards and a claim's cases sit side by side.
function findCardRows(cards) {
  const rowByKeyMap = new Map();
  for (const card of cards) {
    const sourceRows = cards.filter((source) => rowByKeyMap.has(source.key) && source.leadsTo.includes(card.key))
      .map((source) => rowByKeyMap.get(source.key));
    rowByKeyMap.set(card.key, sourceRows.length ? Math.max(...sourceRows) + 1 : 0);
  }
  const rows = [];
  for (const card of cards) (rows[rowByKeyMap.get(card.key)] ||= []).push(card);
  return rows.filter(Boolean);
}

// The episodes laid out from (originX, originY) down, by their whiteboard keys. The arrows are the cards' leadsTo
// (down a scene's column: straight when the cards line up, else an elbow; to another column: a curve from side to
// side) and continuesFrom (from another episode: a curve from bottom to top).
function layoutWhiteboardEpisodes(episodes, heights, originX, originY) {
  const rules = WHITEBOARD_LAYOUT;
  const sections = [], cards = [], connections = [];
  const sceneKeyByCardKeyMap = new Map();
  let y = originY;
  for (const episode of episodes) {
    const episodeSection = {key: episode.id, parentSectionKey: null, title: episode.sectionTitle, color: null,
      x: originX, y};
    sections.push(episodeSection);
    const chapterY = y + rules.episodePadding;
    let chapterX = originX + rules.episodePadding, tallestChapter = 0;
    episode.chapters.forEach((chapter, chapterIndex) => {
      const chapterSection = {key: getChapterSectionKey(episode.id, chapter.id), parentSectionKey: episode.id,
        title: chapter.title,
        color: CHAPTER_COLOR_NAMES[chapterIndex % CHAPTER_COLOR_NAMES.length], x: chapterX, y: chapterY};
      sections.push(chapterSection);
      let columnX = chapterX + rules.chapterPadding, tallestColumn = 0;
      for (const scene of chapter.scenes) {
        const rows = findCardRows(scene.cards);
        const findRowWidth = (row) => row.length * rules.cardWidth + (row.length - 1) * rules.sceneGap;
        const columnWidth = Math.max(...rows.map(findRowWidth));
        let rowY = chapterY + rules.chapterPadding;
        for (const row of rows) {
          let cardX = columnX + (columnWidth - findRowWidth(row)) / 2, rowHeight = 0;
          for (const card of row) {
            const height = Math.ceil(heights[card.key]);
            cards.push({key: card.key, sectionKey: chapterSection.key, color: card.color || null,
              content: card.content, x: cardX, y: rowY, width: rules.cardWidth, height});
            sceneKeyByCardKeyMap.set(card.key, `${episode.id}/${scene.id}`);
            cardX += rules.cardWidth + rules.sceneGap;
            rowHeight = Math.max(rowHeight, height);
          }
          rowY += rowHeight + rules.rowGap;
        }
        tallestColumn = Math.max(tallestColumn, rowY - rules.rowGap - (chapterY + rules.chapterPadding));
        columnX += columnWidth + rules.sceneGap;
      }
      chapterSection.width = columnX - rules.sceneGap + rules.chapterPadding - chapterX;
      chapterSection.height = tallestColumn + 2 * rules.chapterPadding;
      tallestChapter = Math.max(tallestChapter, chapterSection.height);
      chapterX += chapterSection.width + rules.chapterGap;
    });
    episodeSection.width = chapterX - rules.chapterGap + rules.episodePadding - originX;
    episodeSection.height = tallestChapter + 2 * rules.episodePadding;
    y += episodeSection.height + rules.episodeGap;
  }
  const cardByKeyMap = new Map(cards.map((card) => [card.key, card]));
  for (const card of listEpisodeCards(episodes)) {
    for (const endKey of card.leadsTo) {
      const begin = cardByKeyMap.get(card.key), end = cardByKeyMap.get(endKey);
      const isSameColumn = sceneKeyByCardKeyMap.get(card.key) === sceneKeyByCardKeyMap.get(endKey);
      connections.push({key: `${card.key}->${endKey}`, beginKey: card.key, endKey, ...(isSameColumn
        ? {type: begin.x === end.x ? 'straight' : 'elbow', beginPos: 'bottom', endPos: 'top'}
        : {type: 'curve', beginPos: 'right', endPos: 'left'})});
    }
    for (const beginKey of card.continuesFrom) {
      connections.push({key: `${beginKey}->${card.key}`, beginKey, endKey: card.key, type: 'curve',
        beginPos: 'bottom', endPos: 'top'});
    }
  }
  return {sections, cards, connections};
}

// What the page server needs to add the episodes: where each object went, by its whiteboard key, and which version of
// the cards was laid out. It reads the cards themselves from notes.yaml, and refuses a layout of other cards.
function buildImportRequest(episodes, layout) {
  return {
    episodeIds: episodes.map((episode) => episode.id),
    cardsVersion: whiteboard.page.cardsVersion,
    sections: layout.sections.map(({key, color, x, y, width, height}) => ({key, color, x, y, width, height})),
    cards: layout.cards.map(({key, x, y, width, height}) => ({key, x, y, width, height})),
    connections: layout.connections.map(({key, type, beginPos, endPos}) => ({key, type, beginPos, endPos})),
  };
}

// Why a save or an import did not go through, in the page's language; the page server's English reason goes in the
// line's tooltip, for whoever debugs it.
// The failures that have a reason of their own: those found on this computer (a card Heptabase could not draw among
// them), and the subscription.
const WHITEBOARD_FAILURE_REASON_KEY_BY_CODE_MAP = {
  not_measured: 'video.whiteboard.reason.notMeasured',
  cards_changed: 'video.whiteboard.reason.cardsChanged',
  picture_unusable: 'video.whiteboard.reason.pictureUnusable',
  busy: 'video.whiteboard.reason.busy',
  other_account: 'video.whiteboard.reason.otherAccount',
  subscription_required: 'video.whiteboard.reason.subscriptionRequired',
};

function describeWhiteboardFailure(result) {
  const code = result.body.code;
  const reasonKey = WHITEBOARD_FAILURE_REASON_KEY_BY_CODE_MAP[code];
  const reason = reasonKey ? translate(reasonKey)
    : !result.status || code === 'not_sent' ? translate('video.whiteboard.reason.notReached')
      : translate('video.whiteboard.reason.refused', {code: code || `HTTP ${result.status}`});
  return {code, reason, details: [result.body.message, ...(result.body.details || [])].filter(Boolean).join(' · ')};
}

// The preview: the episodes that can go on the whiteboard, laid out from the top left. Nothing leaves the computer.
async function showWhiteboardPreview() {
  const episodes = whiteboard.page.episodesToAdd;
  whiteboard.previewLayout = null;
  if (!episodes.length) { whiteboard.view = 'empty'; showWhiteboardToolbar(); return; }
  whiteboard.view = 'loading';
  showWhiteboardToolbar();
  const images = await loadWhiteboardImages();
  const measurement = await measureCards(episodes, images);
  if (measurement.failure) { showUnreadableWhiteboard(measurement.failure); return; }
  whiteboard.previewLayout = layoutWhiteboardEpisodes(episodes, measurement.heights, 0, 0);
  postShowToWhiteboard({type: 'showObjects', title: whiteboard.page.title, ...whiteboard.previewLayout,
    files: images});
  whiteboard.view = 'preview';
  showWhiteboardToolbar();
  if (whiteboard.isSaveRequested) saveWhiteboard();
}

// Takes this tab to Heptabase's sign-in; Heptabase sends it back to this page, where `finishSignIn` picks up.
async function signInToHeptabase() {
  const returnUrl = new URL(window.location.href);
  returnUrl.searchParams.delete(SIGN_IN_QUERY_NAME);
  const result = await callApi('POST', '/api/series-whiteboard/sign-in',
    {returnPath: returnUrl.pathname + returnUrl.search});
  if (!result.isOk) {
    whiteboard.saveFailure = describeWhiteboardFailure(result);
    showWhiteboardToolbar();
    if (whiteboard.view !== 'preview') showToast(translate('video.whiteboard.signInFailed'));
    return;
  }
  window.location.assign(result.body.authorizationUrl);
}

async function saveWhiteboard() {
  whiteboard.isSaveRequested = false;
  if (!whiteboard.previewLayout || whiteboard.isSaving) return;
  whiteboard.signInStatus = null;
  whiteboard.saveFailure = null;
  if (!whiteboard.page.signedInEmail) { await signInToHeptabase(); return; }
  whiteboard.isSaving = true;
  showWhiteboardToolbar();
  const result = await callApi('POST', '/api/series-whiteboard/import',
    buildImportRequest(whiteboard.page.episodesToAdd, whiteboard.previewLayout));
  whiteboard.isSaving = false;
  if (result.status === 401) { await signInToHeptabase(); return; }  // the stored sign-in is no longer accepted
  if (result.body.code === 'cards_changed') {  // the preview shows the cards as they are now; the user saves again
    await refetchWhiteboardPage();
    await showWhiteboardPreview();
  }
  if (!result.isOk) {
    whiteboard.saveFailure = describeWhiteboardFailure(result);
    showWhiteboardToolbar();
    return;
  }
  await refetchWhiteboardPage();
  await showSavedWhiteboard();
}

async function fetchWhiteboardAccessToken() {
  const result = await callApi('GET', '/api/series-whiteboard/access-token');
  if (result.isOk) return result.body.accessToken;
  showUnreadableWhiteboard(result.status === 401 ? findSignInRequiredReason(result) : 'network');
  return null;
}

// A 401 from the page server, which reads the stored sign-in at that moment: Heptabase no longer accepts it, or this
// computer is signed out.
function findSignInRequiredReason(result) {
  return result.body.code === 'sign_in_expired' ? 'unauthorized' : 'signedOut';
}

// The saved whiteboard, read by the embedded page; it answers whiteboardShown or failed.
async function showSavedWhiteboard() {
  if (!whiteboard.page.savedWhiteboard) { await showWhiteboardPreview(); return; }
  const accessToken = await fetchWhiteboardAccessToken();
  if (!accessToken) return;
  postShowToWhiteboard({type: 'showWhiteboard', whiteboardId: whiteboard.page.savedWhiteboard.whiteboardId,
    accessToken});
}

// Reads the saved whiteboard again, with a fresh access token: after an import, on the first episode added unless the
// user chose a section meanwhile, and when the page comes back to the foreground, keeping the viewport. A whiteboard
// that could not be read is tried again from the start (it may be back from the trash).
async function refreshSavedWhiteboard(focusEpisodeId) {
  if (!whiteboard.page || !whiteboard.isFrameReady || whiteboard.isSaving || whiteboard.isImporting) return;
  if (!['saved', 'unreadable'].includes(whiteboard.view)) return;
  await refetchWhiteboardPage();
  if (!whiteboard.page.savedWhiteboard) { await showWhiteboardPreview(); return; }
  if (whiteboard.view === 'unreadable') { await showSavedWhiteboard(); return; }
  const accessToken = await fetchWhiteboardAccessToken();
  if (!accessToken) return;
  postToWhiteboard({type: 'updateAccessToken', accessToken});
  const focusTarget = focusEpisodeId ? resolveWhiteboardFocusTarget({episodeId: focusEpisodeId, chapterId: null})
    : undefined;
  postRequestToWhiteboard({type: 'refreshWhiteboard', focusTarget}, handleWhiteboardReadReply);
}

// Lays out the episodes to add, as the page server has them now, under everything on the whiteboard, left-aligned
// with it, and adds them; laid out again once when the cards changed meanwhile.
async function sendNewEpisodes() {
  for (let attempt = 1; ; attempt += 1) {
    await refetchWhiteboardPage();
    const episodes = whiteboard.page.episodesToAdd;
    if (!episodes.length) return {isOk: true, status: 200, body: {}};
    const images = await loadWhiteboardImages();
    const measurement = await measureCards(episodes, images);
    if (measurement.failure) {
      return {isOk: false, status: 0,
        body: {code: measurement.failure === 'notMeasured' ? 'not_measured' : 'not_sent'}};
    }
    const bounds = whiteboard.shownWhiteboard.contentBounds;
    const result = await callApi('POST', '/api/series-whiteboard/import', buildImportRequest(episodes,
      layoutWhiteboardEpisodes(episodes, measurement.heights, bounds ? bounds.x : 0,
        bounds ? bounds.y + bounds.height + WHITEBOARD_LAYOUT.episodeGap : 0)));
    if (result.body.code !== 'cards_changed' || attempt === 2) return result;
  }
}

// Adds the episodes delivered since. The whiteboard shows what it holds while they go; they show once Heptabase has
// them.
async function importNewEpisodes() {
  if (!whiteboard.page.episodesToAdd.length || whiteboard.isImporting) return;
  whiteboard.hasImportStarted = true;
  whiteboard.isImporting = true;
  whiteboard.hasFocusedDuringImport = false;
  whiteboard.importFailure = null;
  showWhiteboardToolbar();
  const result = await sendNewEpisodes();
  const addedEpisodeId = whiteboard.page.episodesToAdd[0]?.id;  // the page sendNewEpisodes laid out last
  whiteboard.isImporting = false;
  if (result.status === 401) { showUnreadableWhiteboard(findSignInRequiredReason(result)); return; }
  if (result.body.code === 'whiteboard_trashed' || result.body.code === 'whiteboard_deleted') {
    showUnreadableWhiteboard(result.body.code === 'whiteboard_trashed' ? 'trashed' : 'deleted');
    return;
  }
  if (!result.isOk) {
    whiteboard.importFailure = describeWhiteboardFailure(result);
    showWhiteboardToolbar();
    return;
  }
  await refreshSavedWhiteboard(whiteboard.hasFocusedDuringImport ? undefined : addedEpisodeId);
}

// The cards changed on this computer (the page's digest moved): the preview lays out the cards as they are now. A
// saved whiteboard only takes in which episodes are still to add; they are added when a page opens, or with Retry.
async function refreshWhiteboardCards() {
  if (!whiteboard.frame || !whiteboard.page || whiteboard.isSaving || whiteboard.isImporting) return;
  if (!['preview', 'empty', 'saved'].includes(whiteboard.view)) return;
  const page = await fetchWhiteboardPage();
  if (!page || page.cardsVersion === whiteboard.page.cardsVersion) return;
  whiteboard.page = page;
  if (whiteboard.view === 'saved') { showWhiteboardToolbar(); return; }
  if (!page.savedWhiteboard) await showWhiteboardPreview();
}

function showUnreadableWhiteboard(reason) {
  whiteboard.view = 'unreadable';
  whiteboard.unreadableReason = reason;
  showWhiteboardToolbar();
}

async function unlinkWhiteboard() {
  const result = await callApi('POST', '/api/series-whiteboard/unlink');
  if (!result.isOk) { showToast(translate('common.error.unknown')); return; }
  await refetchWhiteboardPage();
  Object.assign(whiteboard, {shownWhiteboard: null, importFailure: null, saveFailure: null, hasImportStarted: false});
  await showWhiteboardPreview();
}

// A dialog that asks before doing something: `contents`, then Cancel and `confirmButton`, a submit button that closes
// it and calls `confirm`. Opened again while open, it shows the new contents.
function openConfirmDialog(contents, confirmButton, confirm) {
  const form = buildElement('form', {method: 'dialog'}, ...contents,
    buildElement('div', {class: 'buttons'},
      buildElement('button', {class: 'hb-btn text', type: 'button', onclick: () => nodes.dialog.close()},
        translate('common.cancel')),
      confirmButton));
  form.addEventListener('submit', (event) => {
    event.preventDefault();
    nodes.dialog.close();
    confirm();
  });
  nodes.dialog.replaceChildren(form);
  if (!nodes.dialog.open) nodes.dialog.showModal();
}

function confirmUnlinkWhiteboard() {
  openConfirmDialog([buildElement('h3', {}, translate('video.whiteboard.unlinkConfirm.title')),
    buildElement('p', {class: 'lead'}, translate('video.whiteboard.unlinkConfirm.body'))],
  buildElement('button', {class: 'hb-btn fill danger', type: 'submit'}, translate('video.whiteboard.unlink')),
  unlinkWhiteboard);
}

// Signs this computer out of Heptabase, for every series. The links stay, so a saved whiteboard then needs a sign-in.
async function signOutOfHeptabase() {
  const result = await callApi('POST', '/api/series-whiteboard/sign-out');
  if (!result.isOk) {
    showToast(translate('video.whiteboard.signOutFailed', {reason: describeWhiteboardFailure(result).reason}));
    return false;
  }
  await refetchWhiteboardPage();
  if (whiteboard.page.savedWhiteboard) showUnreadableWhiteboard('signedOut'); else showWhiteboardToolbar();
  return true;
}

// Before a series' first save: what saving does, and the account it goes to. Signed out, the button signs in first
// (the save then goes on by itself when the sign-in comes back). Signing out here leaves the dialog open, asking for a
// sign-in. The page data is read again first: another series' page may have signed in or out since.
async function confirmSaveWhiteboard() {
  await refetchWhiteboardPage();
  const page = whiteboard.page;
  const email = page.signedInEmail;
  const points = ['whiteboard', 'series'].map((name) => buildElement('li', {},
    translate(`video.whiteboard.saveConfirm.points.${name}`)));
  let account = null;
  if (email) {
    const [beforeEmail, afterEmail] = translate('video.whiteboard.saveConfirm.signedIn', {email: '\u0000'})
      .split('\u0000');
    account = buildElement('p', {class: 'account'}, beforeEmail, buildElement('b', {}, email), afterEmail,
      buildElement('button', {class: 'link', type: 'button', onclick: async () => {
        if (await signOutOfHeptabase() && nodes.dialog.open) await confirmSaveWhiteboard();  // not once closed
      }}, translate('video.whiteboard.signOut')));
  }
  openConfirmDialog([buildElement('h3', {}, translate('video.whiteboard.saveConfirm.title', {title: page.title})),
    buildElement('ul', {class: 'points'}, ...points), account],
  // focused when the dialog opens, rather than the first button, Sign out
  buildElement('button', {class: 'hb-btn fill', type: 'submit', autofocus: true},
    translate(email ? 'video.whiteboard.saveConfirm.save' : 'video.whiteboard.saveConfirm.signInAndSave')),
  saveWhiteboard);
}

// The reply to showWhiteboard or refreshWhiteboard. A reason this page does not know, from a later embedded page,
// reads as one that could not reach Heptabase.
function handleWhiteboardReadReply(message) {
  if (message.type === 'whiteboardShown') {
    whiteboard.focusSection = null;
    whiteboard.view = 'saved';
    whiteboard.shownWhiteboard = {title: message.title, spaceId: message.spaceId,
      contentBounds: message.contentBounds};
    showWhiteboardToolbar();
    if (!whiteboard.hasImportStarted && whiteboard.page.episodesToAdd.length) importNewEpisodes();
  } else if (message.type === 'failed') {
    showUnreadableWhiteboard(message.reason);
  }
}

// What the embedded page says: ready, or a reply to a request, which goes to that request's handler. Messages and
// fields this page does not know are ignored.
function handleWhiteboardMessage(event) {
  if (!whiteboard.frame || event.source !== whiteboard.frame.contentWindow || event.origin !== whiteboard.origin) {
    return;
  }
  const message = event.data;
  if (!message || typeof message.type !== 'string') return;
  if (message.type === 'ready') {
    clearTimeout(whiteboard.frameReadyTimerId);
    whiteboard.isFrameReady = true;
    showSavedWhiteboard();
  } else if (['cardsMeasured', 'whiteboardShown', 'failed'].includes(message.type)) {
    const handleReply = whiteboard.replyHandlerByRequestIdMap.get(message.requestId);
    if (!handleReply) return;
    whiteboard.replyHandlerByRequestIdMap.delete(message.requestId);
    handleReply(message);
  }
}

// A button about the whiteboard: a text button as Heptabase's toolbar has, or with a variant, 'outline' or 'fill'.
function buildWhiteboardButton(textKey, onclick, variant) {
  return buildElement('button', {class: `hb-btn${variant ? ` ${variant}` : ''}`, type: 'button', onclick},
    translate(textKey));
}

// What is going on with the whiteboard, after its name, with what the user can do about it.
function buildWhiteboardStatus(text, actions, tooltip) {
  return buildElement('div', {class: 'whiteboard-status', role: 'status', title: tooltip || undefined},
    buildElement('span', {class: 'text'}, text), ...(actions || []));
}

// In place of a whiteboard that cannot be shown, as the app's full-area messages: what happened, in the middle, over
// what the user can do about it, the first action filled.
function buildWhiteboardMessage(text, actions) {
  actions.forEach((action, index) => action.classList.add(index ? 'outline' : 'fill'));
  return [buildElement('p', {class: 'text'}, text),
    ...(actions.length ? [buildElement('div', {class: 'actions'}, ...actions)] : [])];
}

// What takes the whiteboard's place: why it cannot be read, or, with nothing to show, which episodes have no cards.
function buildWhiteboardPlaceMessage() {
  if (whiteboard.view === 'unreadable') return buildUnreadableMessage();
  if (whiteboard.view === 'empty' && whiteboard.page.episodesWithoutCards.length) {
    return buildWhiteboardMessage(translate('video.whiteboard.noCards',
      {numbers: formatEpisodeNumbers(whiteboard.page.episodesWithoutCards)}), []);
  }
  return null;
}

// Reads the saved whiteboard again now, as coming back to the page does. The icon turns once to show the click.
function buildRefreshWhiteboardButton() {
  const button = buildIconButton('refresh', translate('video.whiteboard.refresh'), {
    onclick: () => { button.classList.add('turning'); refreshSavedWhiteboard(); },
    onanimationend: () => button.classList.remove('turning')});
  return button;
}

// Brings this episode's section back into view, as the whiteboard opened on it. There only when the episode is on
// the saved whiteboard, which has a section for each episode on it.
function buildFocusEpisodeButton() {
  const focusTarget = resolveWhiteboardFocusTarget({episodeId: EPISODE_ID, chapterId: null});
  if (!focusTarget) return null;
  return buildIconButton('focus', translate('video.whiteboard.focusEpisode'),
    {onclick: () => focusWhiteboardOnUserChoice(focusTarget)});
}

function buildWhiteboardMenuItem(iconName, textKey, onclick, isDanger) {
  return buildElement('button', {class: `item${isDanger ? ' danger' : ''}`, type: 'button', role: 'menuitem',
    onclick: (event) => { event.currentTarget.closest('.whiteboard-menu').hidden = true; onclick(); }},
  buildIcon(iconName), translate(textKey));
}

// The ⋯ menu at the end of the saved whiteboard's toolbar: the account this computer is signed in with and Sign out,
// then Unlink.
function buildWhiteboardMenu() {
  const email = whiteboard.page.signedInEmail;
  const menu = buildElement('div', {class: 'whiteboard-menu', role: 'menu', hidden: true},
    email ? buildElement('div', {class: 'item-group'}, buildElement('div', {class: 'label', title: email}, email),
      buildWhiteboardMenuItem('signOut', 'video.whiteboard.signOut', signOutOfHeptabase)) : null,
    buildElement('div', {class: 'item-group'},
      buildWhiteboardMenuItem('unlink', 'video.whiteboard.unlink', confirmUnlinkWhiteboard, true)));
  const button = buildElement('button', {class: 'hb-icon-btn', type: 'button', 'aria-haspopup': 'menu',
    'aria-label': translate('video.whiteboard.more'), title: translate('video.whiteboard.more'),
    onclick: (event) => { event.stopPropagation(); menu.hidden = !menu.hidden; }}, buildIcon('more'));
  return buildElement('div', {class: 'whiteboard-menu-anchor'}, button, menu);
}

function buildUnreadableMessage() {
  const reason = whiteboard.unreadableReason;
  const episodes = whiteboard.page.episodesToAdd;
  // with the delivered episodes still to add, which wait for the whiteboard to be read again
  const translateWithEpisodes = (textKey) => (episodes.length
    ? translate(`${textKey}WithEpisodes`, {numbers: formatEpisodeNumbers(episodes)}) : translate(textKey));
  const unlink = buildWhiteboardButton('video.whiteboard.unlink', confirmUnlinkWhiteboard);
  const signInAgain = buildWhiteboardButton('video.whiteboard.signInAgain', signInToHeptabase);
  if (reason === 'notMeasured') {  // the preview: a card Heptabase could not draw
    return buildWhiteboardMessage(translate('video.whiteboard.unreadable.notMeasured'),
      [buildWhiteboardButton('video.whiteboard.retry', async () => {
        await refetchWhiteboardPage();
        await showWhiteboardPreview();
      })]);
  }
  if (!whiteboard.page.savedWhiteboard) {  // the embedded page did not answer before the save
    return buildWhiteboardMessage(translate('video.whiteboard.unreadable.network'),
      [buildWhiteboardButton('video.whiteboard.retry', reloadWhiteboardFrame)]);
  }
  if (reason === 'trashed') {
    return buildWhiteboardMessage(translate('video.whiteboard.unreadable.trashed'), [
      buildElement('a', {class: 'hb-btn', href: whiteboard.page.appUrl, target: '_blank', rel: 'noopener'},
        translate('video.whiteboard.restore'), buildIcon('out')), unlink]);
  }
  if (reason === 'deleted') return buildWhiteboardMessage(translate('video.whiteboard.unreadable.deleted'), [unlink]);
  if (reason === 'forbidden') {
    return buildWhiteboardMessage(translate('video.whiteboard.unreadable.forbidden'), [signInAgain, unlink]);
  }
  if (reason === 'signedOut') {
    return buildWhiteboardMessage(translateWithEpisodes('video.whiteboard.unreadable.signedOut'),
      [buildWhiteboardButton('video.whiteboard.signIn', signInToHeptabase), unlink]);
  }
  if (reason === 'unauthorized') {
    return buildWhiteboardMessage(translateWithEpisodes('video.whiteboard.unreadable.unauthorized'),
      [signInAgain, unlink]);
  }
  return buildWhiteboardMessage(translate('video.whiteboard.unreadable.network'),
    [buildWhiteboardButton('video.whiteboard.retry', () => {
      if (whiteboard.isFrameReady) showSavedWhiteboard(); else reloadWhiteboardFrame();
    })]);
}

// The whiteboard's toolbar, drawn as Heptabase draws the one above a whiteboard. On the left, the map icon and the
// whiteboard's name, as the app's breadcrumb shows them (the icon only shows, it opens nothing), and, only when there
// is something to say, what is going on: a whiteboard that cannot be read, a save or an import under way or failed,
// delivered episodes without cards. On the right, what the user does with the whiteboard. What saving means is the
// save dialog's to explain, and loading is the embedded page's to show.
function showWhiteboardToolbar() {
  showChapterWhiteboardButtons();
  if (!nodes.whiteboardToolbar) return;
  const page = whiteboard.page;
  const statuses = [];
  const actions = [];
  if (whiteboard.view === 'saved') {
    const spaceId = whiteboard.shownWhiteboard.spaceId;
    const whiteboardUrl = `${page.appUrl}/${spaceId}/whiteboard/${page.savedWhiteboard.whiteboardId}`;
    actions.push(
      buildElement('a', {class: 'hb-btn outline', href: whiteboardUrl, target: '_blank', rel: 'noopener'},
        translate('video.whiteboard.open'), buildIcon('out')),
      buildFocusEpisodeButton(),
      buildRefreshWhiteboardButton(),
      buildWhiteboardMenu());
    const episodes = page.episodesToAdd;
    if (whiteboard.isImporting) {
      statuses.push(buildWhiteboardStatus(translate('video.whiteboard.importing',
        {numbers: formatEpisodeNumbers(episodes)})));
    } else if (whiteboard.importFailure) {
      // another account: sign in with the one that saved it; no subscription: nothing to retry
      const code = whiteboard.importFailure.code;
      const importActions = code === 'other_account'
        ? [buildWhiteboardButton('video.whiteboard.signInAgain', signInToHeptabase)]
        : code === 'subscription_required' ? []
          : [buildWhiteboardButton('video.whiteboard.retry', importNewEpisodes)];
      statuses.push(buildWhiteboardStatus(translate('video.whiteboard.importFailed', {
        numbers: formatEpisodeNumbers(episodes), reason: whiteboard.importFailure.reason}), importActions,
      whiteboard.importFailure.details));
    }
  } else if (whiteboard.view === 'preview' || (whiteboard.view === 'loading' && !page.savedWhiteboard)) {
    const save = buildWhiteboardButton(whiteboard.isSaving ? 'video.whiteboard.saving' : 'video.whiteboard.save',
      confirmSaveWhiteboard, 'fill');
    save.disabled = !whiteboard.previewLayout || whiteboard.isSaving;
    actions.push(save);
    const noticeKey = whiteboard.saveFailure ? null : {canceled: 'video.whiteboard.signInCanceled',
      failed: 'video.whiteboard.signInFailed'}[whiteboard.signInStatus];
    if (whiteboard.saveFailure) {
      // no subscription: the save button stays, for after the user subscribes
      const text = whiteboard.saveFailure.code === 'subscription_required'
        ? translate('video.whiteboard.saveNeedsSubscription')
        : translate('video.whiteboard.saveFailed', {reason: whiteboard.saveFailure.reason});
      statuses.push(buildWhiteboardStatus(text, null, whiteboard.saveFailure.details));
    } else if (noticeKey) {
      statuses.push(buildWhiteboardStatus(translate(noticeKey)));
    }
  }
  if (page.episodesWithoutCards.length && whiteboard.view !== 'empty') {  // empty: the message in the middle says it
    statuses.push(buildWhiteboardStatus(translate('video.whiteboard.noCards',
      {numbers: formatEpisodeNumbers(page.episodesWithoutCards)})));
  }
  // the saved whiteboard's name in Heptabase once it has shown, the series' name until then
  const title = page.savedWhiteboard && whiteboard.shownWhiteboard ? whiteboard.shownWhiteboard.title : page.title;
  const isMenuOpen = Boolean(nodes.whiteboardToolbar.querySelector('.whiteboard-menu:not([hidden])'));
  nodes.whiteboardToolbar.replaceChildren(
    buildElement('div', {class: 'start'},
      buildElement('div', {class: 'breadcrumb'}, buildElement('span', {class: 'map'}, buildIcon('whiteboard')),
        buildElement('span', {class: 'slash'}, buildIcon('slash')),
        buildElement('span', {class: 'title', title}, title)),
      ...statuses),
    buildElement('div', {class: 'end'}, ...actions));
  const menu = nodes.whiteboardToolbar.querySelector('.whiteboard-menu');
  if (menu && isMenuOpen) menu.hidden = false;  // an update while the menu is open keeps it open
  // the iframe only when it shows something: not while a whiteboard cannot be read, nor with nothing to show, where
  // the message takes its place
  whiteboard.frame.hidden = whiteboard.view === 'unreadable' || whiteboard.view === 'empty';
  const message = buildWhiteboardPlaceMessage();
  nodes.whiteboardMessage.replaceChildren(...(message || []));
  nodes.whiteboardMessage.hidden = !message;
}

function reloadWhiteboardFrame() {
  whiteboard.isFrameReady = false;
  whiteboard.hasAskedToShow = false;
  whiteboard.view = 'loading';
  showWhiteboardToolbar();
  whiteboard.frame.src = whiteboard.page.embeddedWhiteboardUrl;
  watchWhiteboardFrameReady();
}

// An embedded page that never says it is ready (Heptabase could not be reached) shows as a whiteboard that could not
// be read, with Retry.
function watchWhiteboardFrameReady() {
  clearTimeout(whiteboard.frameReadyTimerId);
  whiteboard.frameReadyTimerId = setTimeout(() => {
    if (!whiteboard.isFrameReady) showUnreadableWhiteboard('network');
  }, FRAME_READY_TIMEOUT_MILLISECONDS);
}

// The iframe is made once: when the whiteboard view opens, or in the background when the page opens and there are
// episodes to add to a saved whiteboard (or the page came back from a sign-in).
function mountWhiteboard() {
  if (whiteboard.frame || !whiteboard.page) return;
  whiteboard.origin = new URL(whiteboard.page.embeddedWhiteboardUrl).origin;
  whiteboard.frame = buildElement('iframe', {class: 'whiteboard-frame', src: whiteboard.page.embeddedWhiteboardUrl,
    title: translate('video.whiteboardMode'), referrerpolicy: 'no-referrer'});
  nodes.whiteboardToolbar = buildElement('div', {class: 'whiteboard-toolbar'});
  nodes.whiteboardMessage = buildElement('div', {class: 'whiteboard-message', role: 'status', hidden: true});
  nodes.whiteboard.replaceChildren(nodes.whiteboardToolbar, whiteboard.frame, nodes.whiteboardMessage);
  // a click anywhere else closes the toolbar's ⋯ menu
  document.addEventListener('click', (event) => {
    const menu = nodes.whiteboardToolbar.querySelector('.whiteboard-menu');
    if (menu && !menu.contains(event.target)) menu.hidden = true;
  });
  whiteboard.view = 'loading';
  showWhiteboardToolbar();
  watchWhiteboardFrameReady();
}

// Back from Heptabase's sign-in: how it ended, and the save goes on when a save was what needed it (only on this
// page: the sign-in names the page that started it).
async function loadWhiteboard() {
  const signInId = new URLSearchParams(window.location.search).get(SIGN_IN_QUERY_NAME);
  if (signInId) history.replaceState(history.state, '', buildPageUrl());
  whiteboard.page = await fetchWhiteboardPage(signInId);
  if (!whiteboard.page) return;
  if (signInId) {
    const status = whiteboard.page.signInStatus || 'failed';
    whiteboard.signInStatus = status === 'signedIn' ? null : status;
    whiteboard.isSaveRequested = status === 'signedIn' && !whiteboard.page.savedWhiteboard;
    openWhiteboardMode();
  }
  applyMode();
  showChapterWhiteboardButtons();
  if (whiteboard.page.savedWhiteboard && whiteboard.page.episodesToAdd.length) mountWhiteboard();
}

// The saved whiteboard may have changed in Heptabase while the user was away: read it again when the page comes back
// to the foreground, that is, when its tab is shown and its window has the focus again. While the whiteboard's iframe
// has the focus, the page gets no focus event when the user comes back from another app, so a timer looks as well.
const FOREGROUND_CHECK_INTERVAL_MILLISECONDS = 1000;
let wasPageInForeground = document.visibilityState === 'visible' && document.hasFocus();

function refreshWhiteboardOnReturn() {
  const isPageInForeground = document.visibilityState === 'visible' && document.hasFocus();
  if (isPageInForeground && !wasPageInForeground) refreshSavedWhiteboard();
  wasPageInForeground = isPageInForeground;
}

window.addEventListener('message', handleWhiteboardMessage);
window.addEventListener('focus', refreshWhiteboardOnReturn);
document.addEventListener('visibilitychange', refreshWhiteboardOnReturn);
setInterval(refreshWhiteboardOnReturn, FOREGROUND_CHECK_INTERVAL_MILLISECONDS);

function togglePlay() {
  if (!video) return;
  if (video.paused || video.ended) video.play(); else video.pause();
}

function seekBy(seconds) {
  if (!video) return;
  video.currentTime = Math.min(Math.max(0, video.currentTime + seconds), video.duration || Infinity);
  followVideo();
}

function jumpTo(seconds) {
  if (!video || seconds === null || seconds === undefined) return;
  video.currentTime = seconds;
  placeVideo();
  showVideo();
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
    if (event.key === 'Enter' && !event.shiftKey && !checkIsInputMethodKey(event)) {
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
      if (event.key === 'Enter' && !event.shiftKey && !checkIsInputMethodKey(event)) {
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
      window.location.href = `${BOOT.baseUrl}/video/${episodeSelect.value}${buildModeQuery()}`;
    });
    nodes.switcher.replaceChildren(episodeSelect);
  } else {
    nodes.switcher.replaceChildren();
  }
}

function showPage() {
  showHead();
  showChapters();
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
  if (pageData.delivery.hasFile) {
    video = buildElement('video', {id: 'video', class: 'hb-video', controls: true, preload: 'metadata',
      playsinline: true, poster: pageData.delivery.hasCover ? getMediaUrl('cover.png') : undefined,
      src: getMediaUrl('video.mp4')});
    video.append(...pageData.delivery.subtitles.map((subtitles) => buildElement('track', {kind: 'subtitles',
      src: getMediaUrl(`subtitles.${encodeURIComponent(subtitles.languageCode)}.vtt`), srclang: subtitles.languageCode,
      label: translate('video.subtitles')})));
    video.addEventListener('loadedmetadata', applySubtitles);
  }
  // A toggle in the toolbar, with its key; applySubtitles and applyMode say whether it is on, and whether it is there.
  const buildToggleButton = (textKey, key, onclick) => buildElement('button', {class: 'hb-btn outline', type: 'button',
    onclick}, translate(textKey), buildElement('kbd', {}, key));
  nodes.subtitles = video && pageData.delivery.subtitles.length
    ? buildToggleButton('video.subtitles', 'C', toggleSubtitles) : null;
  nodes.addComment = buildElement('button', {class: 'hb-btn fill', type: 'button', onclick: startComment},
    buildIcon('plus'), translate('video.addComment'), buildElement('kbd', {}, 'M'));
  // the chapters view shows once notes.yaml fits the delivered video, which the agent may write while the page is
  // open; the whiteboard once the page server said what it holds
  nodes.theaterMode = video ? buildToggleButton('video.theaterMode', 'T', () => toggleMode('theater')) : null;
  nodes.chaptersMode = video ? buildToggleButton('video.chaptersMode', 'N', () => toggleMode('chapters')) : null;
  nodes.whiteboardMode = video ? buildToggleButton('video.whiteboardMode', 'W', () => toggleMode('whiteboard')) : null;
  nodes.videoHome = buildElement('div', {class: 'video-home'}, video);
  nodes.chapters = buildElement('section', {class: 'chapters', 'aria-label': translate('video.chaptersMode')});
  nodes.whiteboard = buildElement('section', {class: 'whiteboard', 'aria-label': translate('video.whiteboardMode')});
  if (video) {
    video.addEventListener('timeupdate', () => {
      if (!video.paused && !video.seeking) followVideo();
      showChapterProgress();
    });
    for (const eventName of ['play', 'fullscreenchange', 'leavepictureinpicture']) {
      video.addEventListener(eventName, followVideo);
    }
  }
  const keyHints = video && buildElement('div', {class: 'keys hb-meta'},
    buildElement('span', {}, buildElement('kbd', {}, translate('video.keys.space')), translate('video.keys.play')),
    buildElement('span', {}, buildElement('kbd', {}, '←'), buildElement('kbd', {}, '→'),
      translate('video.keys.seek', {seconds: SEEK_SECONDS})));
  nodes.toolbar = buildElement('div', {class: 'toolbar'}, nodes.addComment, nodes.subtitles, nodes.theaterMode,
    nodes.chaptersMode, nodes.whiteboardMode, keyHints);
  appNode.replaceChildren(...[
    buildElement('div', {class: 'topnav'},
      buildElement('a', {class: 'hb-btn text small', href: `${BOOT.baseUrl}/plan`}, buildIcon('back'),
        translate('video.backToPlan')),
      nodes.switcher),
    buildElement('div', {class: 'hb-head'}, nodes.eyebrow, nodes.title, nodes.meta),
    nodes.notices,
    video && nodes.videoHome,
    nodes.toolbar,
    nodes.composer,
    nodes.chapters,
    nodes.whiteboard,
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
  applyMode();
  if (pageData.isDevModeOn) fetchCostReport();
  loadWhiteboard();
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
  refreshWhiteboardCards();
}

window.addEventListener('keydown', (event) => {
  if (event.defaultPrevented || event.metaKey || event.ctrlKey || event.altKey || !pageData) return;
  if (checkIsTyping(event.target) || checkIsInputMethodKey(event) || (nodes.dialog && nodes.dialog.open)) return;
  const key = resolveShortcutKey(event);
  // the whiteboard shows no video: playing and commenting wait until it closes
  if (checkIsWhiteboardModeShown() && [' ', 'ArrowLeft', 'ArrowRight', 'm', 'c'].includes(key)) return;
  if (key === ' ') togglePlay();
  else if (key === 'ArrowLeft') seekBy(-SEEK_SECONDS);
  else if (key === 'ArrowRight') seekBy(SEEK_SECONDS);
  else if (key === 'm') startComment();
  else if (key === 'c') toggleSubtitles();
  else if (key === 't') toggleMode('theater');
  else if (key === 'n') toggleMode('chapters');
  else if (key === 'w') toggleMode('whiteboard');
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
