// The video page: the latest delivery of one episode, its comments, the survey (a rating, and the watch depth in dev
// mode) and sharing with the team.
// Keys: Space plays or pauses, the arrows move 5 s, M adds a comment (the video pauses; Enter saves and plays on,
// Esc cancels), C turns subtitles on or off, T turns theater mode on or off, N the chapters view and W the whiteboard. The video element is made once;
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
  if (isTheaterModeOn && chapterModeName) setChapterMode(chapterModeName);
  applyTheaterMode();
  if (isTheaterModeOn) video.scrollIntoView({block: 'start'});
}

// Chapters and whiteboard -------------------------------------------------------------------------------------------
// Two views of notes.yaml, next to theater mode in the toolbar (one of the three at a time):
// - chapters: each part a large key frame (the player while the part plays) beside its segments, each a key frame, a
//   title and the segment's core idea; choosing one plays it, and each opens into its handout;
// - whiteboard: every episode's cards on one whiteboard for the series, a section per episode holding a section per
//   part, opening on this episode and filling the page under the toolbar; with no video in view, the comment and
//   subtitle buttons are off and the rest of the page is hidden.
// A segment's handout is cards, one claim each: the claim as the title, then numbered points with their key phrases
// highlighted. A card is drawn the way a Heptabase card draws what was pasted into it, so what the reader sees is what
// a copy gives.
const CHAPTER_MODE_NAMES = ['chapters', 'whiteboard'];
let chapterModeName = (() => {
  try {
    const savedName = localStorage.getItem('chapterMode');
    return CHAPTER_MODE_NAMES.includes(savedName) ? savedName : null;
  } catch (error) { return null; }
})();
let chaptersJson = null;
let activeScreen = null;  // the part frame the video plays in, in the chapters view
const openHandoutSegmentIds = new Set();
// isMoved: the viewer has panned or zoomed since the board was last fitted, so it stays where they put it;
// fitsAll: the last fit showed the whole series rather than this episode
const board = {x: 0, y: 0, scale: 1, isFitted: false, isMoved: false, fitsAll: false, openCardId: null};
const SECTION_COLOR_NAMES = ['blue', 'yellow', 'green', 'purple', 'orange', 'red'];
function getMediaUrl(name, episodeId = EPISODE_ID) {
  return `${BOOT.baseUrl}/media/${episodeId}/${name}`;
}

function getFrameUrl(beatId, episodeId = EPISODE_ID) {
  return getMediaUrl(`frames/${encodeURIComponent(beatId)}.jpg`, episodeId);
}

function getHandoutImageUrl(assetFilePath, episodeId = EPISODE_ID) {
  return getMediaUrl(`handout-images/${assetFilePath.split('/').map(encodeURIComponent).join('/')}`, episodeId);
}

// whether a view has something to show: the chapters view this episode's cards, the whiteboard the series' cards
function checkIsChapterModeAvailable(name) {
  return name === 'chapters' ? Boolean(pageData.chapters) : name === 'whiteboard' && Boolean(pageData.board);
}

// **bold** and ==highlight== in a card's text, as text nodes, <strong> and <mark>; nothing else in the text is markup
function buildInlineText(text) {
  return text.split(/(\*\*[^*]+\*\*|==[^=]+==)/).filter(Boolean).map((piece) => {
    if (piece.startsWith('**') && piece.endsWith('**')) return buildElement('strong', {}, piece.slice(2, -2));
    if (piece.startsWith('==') && piece.endsWith('==')) return buildElement('mark', {}, piece.slice(2, -2));
    return piece;
  });
}

function findBeatStartSeconds(beatId) {
  for (const part of pageData.chapters.parts) {
    for (const segment of part.segments) {
      const beat = segment.beats.find((candidate) => candidate.id === beatId);
      if (beat) return beat.startSeconds;
    }
  }
  return null;
}

// A point's number at its depth, as the app writes it: 1. at the top, then a., then i.
function formatPointNumber(depth, number) {
  if (depth % 3 === 1) {
    let letters = '';
    for (let value = number; value > 0; value = Math.floor((value - 1) / 26)) {
      letters = String.fromCharCode(97 + (value - 1) % 26) + letters;
    }
    return `${letters}.`;
  }
  if (depth % 3 === 2) {
    const romanNumerals = [[10, 'x'], [9, 'ix'], [5, 'v'], [4, 'iv'], [1, 'i']];
    let roman = '', value = number;
    for (const [amount, numeral] of romanNumerals) while (value >= amount) { roman += numeral; value -= amount; }
    return `${roman}.`;
  }
  return `${number}.`;
}

// A point's picture; a frame of this episode's video plays from its beat when chosen.
function buildPicture(point, partIndex, episodeId) {
  const isFrame = Boolean(point.frame);
  const startSeconds = isFrame && episodeId === EPISODE_ID ? findBeatStartSeconds(point.frame) : null;
  const image = buildElement('img', {src: isFrame ? getFrameUrl(point.frame, episodeId)
    : getHandoutImageUrl(point.image, episodeId),
    alt: point.caption || '', onload: (event) => rememberImageDataUrl(event.target)});  // not lazy: the whiteboard's
  // cards are drawn scaled, where the browser may never decide to load them
  return [
    buildElement('div', {class: 'image'}, isFrame && startSeconds !== null
      ? buildElement('button', {type: 'button', title: translate('chapters.playFromHere'),
        onclick: (event) => { event.stopPropagation(); playChapters(partIndex, startSeconds); }}, image)
      : image),
    point.caption ? buildElement('p', {}, buildElement('em', {}, point.caption)) : null,
  ];
}

// Numbered points; a point's sub-points and picture are nested under its text.
function buildPoints(points, depth, partIndex, episodeId) {
  return buildElement('div', {class: 'numbered'}, points.map((point, index) => buildElement('div', {class: 'item'},
    buildElement('span', {class: 'number'}, formatPointNumber(depth, index + 1)),
    buildElement('div', {class: 'nested'},
      buildElement('p', {}, buildInlineText(point.text)),
      point.points && point.points.length ? buildPoints(point.points, depth + 1, partIndex, episodeId) : null,
      point.frame || point.image ? buildPicture(point, partIndex, episodeId) : null))));
}

// A card's content: its claim as the first heading, then its points.
function buildCardContent(card, partIndex) {
  return buildElement('div', {class: 'card-content'}, buildElement('h1', {}, buildInlineText(card.title)),
    buildPoints(card.points, 0, partIndex, card.episodeId));
}

// A card in a side panel: a header with its segment, copy, and a way to the card on the whiteboard, above the content.
function buildPanelCard(card, segment, partIndex) {
  return buildElement('article', {class: 'hb-panel-card'},
    buildElement('div', {class: 'panel-card-head'},
      buildElement('span', {class: 'icon'}, buildIcon('card')),
      buildElement('span', {class: 'label'}, segment.title),
      buildElement('button', {class: 'hb-icon-btn', type: 'button', title: translate('chapters.copyCard'),
        'aria-label': translate('chapters.copyCard'), onclick: () => copyCard(card)}, buildIcon('copy')),
      buildElement('button', {class: 'hb-icon-btn', type: 'button', title: translate('chapters.locateCard'),
        'aria-label': translate('chapters.locateCard'), onclick: () => locateBoardCard(card.id)}, buildIcon('whiteboard'))),
    buildCardContent(card, partIndex));
}

// How many cards, in words: 兩張卡片, 五張卡片, 5 cards.
function formatCardCount(count) {
  if (count === 1) return translate('chapters.oneCard');
  if (!document.documentElement.lang.startsWith('zh') || count > 99) return translate('chapters.cards', {count});
  const digits = '〇一兩三四五六七八九', tens = Math.floor(count / 10), ones = count % 10;
  const words = count < 10 ? digits[count]
    : `${tens > 1 ? '〇一二三四五六七八九'[tens] : ''}十${ones ? '〇一二三四五六七八九'[ones] : ''}`;
  return translate('chapters.cards', {count: words});
}

// Playing: the one video element moves into the chosen part's frame, and back under the title when the view closes.
function placeVideo(screen) {
  if (!video || activeScreen === screen) return;
  if (activeScreen) activeScreen.showKeyFrame();
  activeScreen = screen;
  if (screen) screen.replaceChildren(video); else nodes.videoHome.replaceChildren(video);
}

function playChapters(partIndex, startSeconds) {
  if (!video) return;
  if (chapterModeName !== 'chapters') setChapterMode('chapters');
  placeVideo(nodes.chapterScreens[partIndex]);
  video.currentTime = startSeconds;
  video.play();
  nodes.chapterScreens[partIndex].scrollIntoView({behavior: 'smooth', block: 'nearest'});
}

function showChapterProgress() {
  if (!nodes.chapterRows) return;
  const seconds = video ? video.currentTime : 0;
  for (const {segment, row, bar} of nodes.chapterRows) {
    const isPlaying = chapterModeName === 'chapters' && !!activeScreen && seconds >= segment.startSeconds
      && seconds < segment.endSeconds;
    row.classList.toggle('playing', isPlaying);
    bar.style.width = isPlaying
      ? `${(100 * (seconds - segment.startSeconds) / (segment.endSeconds - segment.startSeconds)).toFixed(1)}%` : '0';
  }
}

function buildChaptersView(chapters) {
  nodes.chapterScreens = [];
  nodes.chapterRows = [];
  const parts = chapters.parts.map((part, partIndex) => {
    const first = part.segments[0], last = part.segments[part.segments.length - 1];
    const minutes = Math.max(1, Math.round((last.endSeconds - first.startSeconds) / 60));
    const screen = buildElement('div', {class: 'screen'});
    screen.showKeyFrame = () => screen.replaceChildren(
      buildElement('img', {src: getFrameUrl(first.keyFrame), alt: ''}),
      buildElement('button', {class: 'play', type: 'button', onclick: () => playChapters(partIndex, first.startSeconds)},
        buildElement('span', {}, translate('chapters.playFrom', {time: formatTime(first.startSeconds)}))));
    screen.showKeyFrame();
    nodes.chapterScreens.push(screen);
    const rows = part.segments.map((segment) => {
      const bar = buildElement('i', {});
      const handoutButton = buildElement('button', {class: 'hb-btn text small', type: 'button'}, '');
      const row = buildElement('div', {class: 'segment', role: 'button', tabindex: '0',
        onclick: () => playChapters(partIndex, segment.startSeconds),
        onkeydown: (event) => {
          if (event.key === 'Enter') { event.preventDefault(); playChapters(partIndex, segment.startSeconds); }
        }},
        buildElement('div', {class: 'thumb'}, buildElement('img', {src: getFrameUrl(segment.keyFrame), alt: '',
          loading: 'lazy'}), buildElement('span', {class: 'bar'}, bar)),
        buildElement('div', {class: 'body'},
          buildElement('div', {class: 'title'}, buildElement('b', {}, segment.title),
            buildElement('span', {class: 'hb-meta'}, `${formatTime(segment.startSeconds)} · ${translate(
              'chapters.seconds', {seconds: Math.round(segment.endSeconds - segment.startSeconds)})}`)),
          buildElement('p', {}, segment.summary),
          handoutButton));
      const slot = buildElement('div', {class: 'handout-slot'});
      const showHandout = () => {
        const isOpen = openHandoutSegmentIds.has(segment.id);
        handoutButton.setAttribute('aria-expanded', String(isOpen));
        handoutButton.textContent = isOpen ? translate('chapters.closeCards') : formatCardCount(segment.cards.length);
        slot.replaceChildren(...(isOpen ? segment.cards.map((card) => buildPanelCard(card, segment, partIndex)) : []));
      };
      handoutButton.addEventListener('click', (event) => {
        event.stopPropagation();
        if (openHandoutSegmentIds.has(segment.id)) openHandoutSegmentIds.delete(segment.id);
        else openHandoutSegmentIds.add(segment.id);
        showHandout();
      });
      showHandout();
      nodes.chapterRows.push({segment, row, bar});
      return [row, slot];
    });
    return buildElement('section', {class: 'part'},
      buildElement('h3', {}, buildElement('span', {class: 'number'}, translate('chapters.part', {number: partIndex + 1})),
        part.title, buildElement('span', {class: 'hb-meta'}, translate('chapters.minutes', {minutes}))),
      buildElement('div', {class: 'part-grid'}, screen, buildElement('div', {class: 'segments'}, rows.flat())));
  });
  nodes.chapters.replaceChildren(...parts);
}

// The whiteboard: sections in a row, one per part; in a section, a column per segment, its cards in rows by the arrows
// between them (a card below the cards that lead to it); the arrows drawn between the cards. It pans by dragging or
// scrolling and zooms with the buttons or a pinch (Ctrl or Cmd with the wheel), around the pointer. A section's title
// keeps its size on the screen at any zoom, as in the app. A click opens a card: it is selected, its text can be
// selected, and its content scrolls when it is longer than the card; a click on the board or Esc closes it.
const BOARD_MIN_SCALE = 0.1, BOARD_MAX_SCALE = 2;
const BOARD_CLICK_PIXELS = 4;  // a press that moves less than this is a click, not a drag

function applyBoardTransform(isAnimated) {
  nodes.boardCanvas.classList.toggle('animated', Boolean(isAnimated));
  nodes.boardCanvas.style.transform = `translate(${board.x}px, ${board.y}px) scale(${board.scale})`;
  nodes.boardCanvas.style.setProperty('--wb-scale', String(board.scale));
  nodes.boardZoomLabel.textContent = `${Math.round(board.scale * 100)}%`;
}

function zoomBoard(factor, centerX, centerY) {
  const viewportRect = nodes.boardViewport.getBoundingClientRect();
  const originX = centerX ?? viewportRect.width / 2, originY = centerY ?? viewportRect.height / 2;
  const nextScale = Math.min(BOARD_MAX_SCALE, Math.max(BOARD_MIN_SCALE, board.scale * factor));
  board.x = originX - (originX - board.x) * nextScale / board.scale;
  board.y = originY - (originY - board.y) * nextScale / board.scale;
  board.scale = nextScale;
  board.isMoved = true;
  applyBoardTransform(centerX === undefined);
}

// The episode's section in view (or the whole series' board), as large as it fits, with room above for the
// sections' titles (which keep their size on the screen) and below for the tools.
const BOARD_FIT_MARGINS = {top: 48, right: 24, bottom: 56, left: 24};

// Where nodes on the board are, together, in the board's own units.
function findBoardBox(boxNodes) {
  const canvasRect = nodes.boardCanvas.getBoundingClientRect();
  const rects = boxNodes.map((node) => node.getBoundingClientRect());
  const left = Math.min(...rects.map((rect) => rect.left)), top = Math.min(...rects.map((rect) => rect.top));
  const right = Math.max(...rects.map((rect) => rect.right)), bottom = Math.max(...rects.map((rect) => rect.bottom));
  return {left: (left - canvasRect.left) / board.scale, top: (top - canvasRect.top) / board.scale,
    width: (right - left) / board.scale, height: (bottom - top) / board.scale};
}

function fitBoard(fitsAll) {
  const viewportRect = nodes.boardViewport.getBoundingClientRect();
  if (!viewportRect.width) return;
  const episodeNodes = [...nodes.boardCanvas.querySelectorAll('.wb-episode')];
  const currentNode = nodes.boardCanvas.querySelector('.wb-episode.current');
  const box = findBoardBox(fitsAll || !currentNode ? episodeNodes : [currentNode]);
  const {top, right, bottom, left} = BOARD_FIT_MARGINS;
  const width = viewportRect.width - left - right, height = viewportRect.height - top - bottom;
  board.scale = Math.min(1, width / box.width, height / box.height);
  board.x = left + (width - box.width * board.scale) / 2 - box.left * board.scale;
  board.y = top + (height - box.height * board.scale) / 2 - box.top * board.scale;
  board.isFitted = true;
  board.isMoved = false;
  board.fitsAll = Boolean(fitsAll);
  applyBoardTransform(false);
}

// A segment's cards in rows: a card goes one row below the latest of the segment's earlier cards that lead to it, so
// that an argument reads downwards and a claim's cases sit side by side.
function findCardRows(cards) {
  const rowById = new Map();
  for (const card of cards) {
    const sourceRows = cards.filter((source) => rowById.has(source.id) && source.leadsTo.includes(card.id))
      .map((source) => rowById.get(source.id));
    rowById.set(card.id, sourceRows.length ? Math.max(...sourceRows) + 1 : 0);
  }
  const rows = [];
  for (const card of cards) (rows[rowById.get(card.id)] ||= []).push(card);
  return rows.filter(Boolean);
}

// The arrows of the cards' leads_to, shaped the way the app shapes its connectors. Down a segment's column: straight
// when the two cards line up, and an elbow (down, across, down) when a card leads to cases side by side or cases lead
// to one card. Between columns: a curve from side to side, its ends leaving the cards straight for a third of the way,
// less the nearer the two ends are to level or to one above the other, so that it straightens into a line.
const ARROW_GAP = 8, ARROW_MAX_SLOPE = 2.5;

function getCurveHandleLength(start, end) {
  const dx = end[0] - start[0], dy = end[1] - start[1];
  const slope = Math.abs(dy / dx);
  let length = Math.hypot(dx, dy) / 2;
  if (slope > ARROW_MAX_SLOPE) length /= slope / ARROW_MAX_SLOPE;
  else if (1 / slope > ARROW_MAX_SLOPE) length /= (1 / slope) / ARROW_MAX_SLOPE;
  return length * 2 / 3;
}

function buildArrowPath(from, to) {
  if (from.episode !== to.episode) {  // to another episode's section, above or below: a curve from end to end
    const isDown = to.top >= from.top, side = isDown ? 1 : -1;
    const start = [from.left + from.width / 2, isDown ? from.top + from.height + ARROW_GAP : from.top - ARROW_GAP];
    const end = [to.left + to.width / 2, isDown ? to.top - ARROW_GAP : to.top + to.height + ARROW_GAP];
    const handle = getCurveHandleLength(start, end);
    return `M${start[0]} ${start[1]} C${start[0]} ${start[1] + side * handle} ${end[0]} ${end[1] - side * handle} `
      + `${end[0]} ${end[1]}`;
  }
  if (from.column === to.column) {
    const isDown = to.top >= from.top;
    const startX = from.left + from.width / 2, endX = to.left + to.width / 2;
    const startY = isDown ? from.top + from.height + ARROW_GAP : from.top - ARROW_GAP;
    const endY = isDown ? to.top - ARROW_GAP : to.top + to.height + ARROW_GAP;
    if (Math.abs(startX - endX) < 1) return `M${startX} ${startY} L${endX} ${endY}`;
    const middleY = (startY + endY) / 2;
    return `M${startX} ${startY} L${startX} ${middleY} L${endX} ${middleY} L${endX} ${endY}`;
  }
  const isRight = to.left >= from.left, side = isRight ? 1 : -1;
  const start = [isRight ? from.left + from.width + ARROW_GAP : from.left - ARROW_GAP, from.top + from.height / 2];
  const end = [isRight ? to.left - ARROW_GAP : to.left + to.width + ARROW_GAP, to.top + to.height / 2];
  const handle = getCurveHandleLength(start, end);
  return `M${start[0]} ${start[1]} C${start[0] + side * handle} ${start[1]} ${end[0] - side * handle} ${end[1]} `
    + `${end[0]} ${end[1]}`;
}

function drawBoardArrows() {
  const canvasRect = nodes.boardCanvas.getBoundingClientRect();
  const boxById = new Map([...nodes.boardCanvas.querySelectorAll('.wb-card')].map((cardNode) => {
    const rect = cardNode.getBoundingClientRect();
    return [cardNode.dataset.cardId, {left: (rect.left - canvasRect.left) / board.scale,
      top: (rect.top - canvasRect.top) / board.scale, width: rect.width / board.scale, height: rect.height / board.scale,
      column: cardNode.closest('.wb-segment'), episode: cardNode.closest('.wb-episode')}];
  }));
  const paths = [];
  for (const card of listBoardCards()) {
    for (const targetId of card.leadsTo) {
      const from = boxById.get(card.id), to = boxById.get(targetId);
      if (from && to) paths.push(buildArrowPath(from, to));
    }
  }
  nodes.boardArrows.setAttribute('width', nodes.boardCanvas.offsetWidth);
  nodes.boardArrows.setAttribute('height', nodes.boardCanvas.offsetHeight);
  nodes.boardArrows.innerHTML = '<defs><marker id="wb-arrowhead" viewBox="-2 0 14 12" refX="10" refY="6" '
    + 'markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0 L12 6 L0 12 Z"/></marker></defs>'
    + paths.map((path) => `<path d="${path}" marker-end="url(#wb-arrowhead)"/>`).join('');
}

// Opens the card (or closes the open one, given null); a closed card shows its top again.
function openBoardCard(cardId) {
  board.openCardId = cardId;
  for (const cardNode of nodes.boardCanvas.querySelectorAll('.wb-card')) {
    const isOpen = cardNode.dataset.cardId === cardId;
    if (!isOpen && cardNode.classList.contains('open')) cardNode.querySelector('.card-content').scrollTop = 0;
    cardNode.classList.toggle('open', isOpen);
  }
  nodes.boardCopyCard.hidden = !cardId;
}

// The whiteboard, centred on the card at the largest zoom that shows all of it (at most 100%), with the card open.
function locateBoardCard(cardId) {
  if (chapterModeName !== 'whiteboard') setChapterMode('whiteboard');
  // the whiteboard lays itself out and fits in the next frame; the card is found after that
  requestAnimationFrame(() => requestAnimationFrame(() => {
    const cardNode = nodes.boardCanvas.querySelector(`.wb-card[data-card-id="${CSS.escape(cardId)}"]`);
    const viewportRect = nodes.boardViewport.getBoundingClientRect();
    const {left, top, width, height} = findBoardBox([cardNode]);
    board.scale = Math.min(1, (viewportRect.width - 48) / width, (viewportRect.height - 80) / height);
    board.x = (viewportRect.width - width * board.scale) / 2 - left * board.scale;
    board.y = (viewportRect.height - height * board.scale) / 2 - top * board.scale;
    board.isMoved = true;
    applyBoardTransform(true);
    openBoardCard(cardId);
  }));
}

function listBoardCards() {
  return pageData.board.episodes.flatMap((episode) => episode.parts.flatMap((part) =>
    part.segments.flatMap((segment) => segment.cards)));
}

function findCard(cardId) {
  return listBoardCards().find((card) => card.id === cardId);
}

function buildPartSection(part, partIndex) {
  return buildElement('div', {class: `wb-section ${SECTION_COLOR_NAMES[partIndex % SECTION_COLOR_NAMES.length]}`},
    buildElement('div', {class: 'wb-section-title', title: part.title}, buildElement('span', {}, part.title)),
    part.segments.map((segment) => buildElement('div', {class: 'wb-segment'},
      findCardRows(segment.cards).map((cards) => buildElement('div', {class: 'wb-card-row'}, cards.map((card) =>
        buildElement('div', {class: `wb-card ${card.color || ''}`, dataset: {cardId: card.id}, tabindex: '0',
          'aria-label': card.title, onkeydown: (event) => { if (event.key === 'Enter') openBoardCard(card.id); }},
        buildCardContent(card, partIndex))))))));
}

function buildWhiteboardView(boardData) {
  nodes.boardArrows = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  nodes.boardArrows.setAttribute('class', 'wb-arrows');
  nodes.boardCanvas = buildElement('div', {class: 'wb-canvas'}, nodes.boardArrows,
    buildElement('div', {class: 'wb-board'}, boardData.episodes.map((episode) => {
      const title = `${episode.id.toUpperCase()} ${episode.title}`;
      return buildElement('div', {class: `wb-episode${episode.id === EPISODE_ID ? ' current' : ''}`,
        dataset: {episodeId: episode.id}},
      buildElement('div', {class: 'wb-section-title', title}, buildElement('span', {}, title)),
      episode.parts.map(buildPartSection));
    })));
  nodes.boardZoomLabel = buildElement('span', {class: 'label'}, '100%');
  nodes.boardCopyCard = buildElement('button', {class: 'hb-btn text small', type: 'button', hidden: true,
    onclick: () => copyCard(findCard(board.openCardId))}, translate('chapters.copyCard'));
  nodes.boardViewport = buildElement('div', {class: 'wb-viewport'}, nodes.boardCanvas,
    buildElement('div', {class: 'wb-tools'},
      nodes.boardCopyCard,
      buildElement('span', {class: 'divider'}),
      buildElement('button', {class: 'hb-icon-btn', type: 'button', 'aria-label': translate('chapters.zoomOut'),
        onclick: () => zoomBoard(1 / 1.25)}, '−'),
      nodes.boardZoomLabel,
      buildElement('button', {class: 'hb-icon-btn', type: 'button', 'aria-label': translate('chapters.zoomIn'),
        onclick: () => zoomBoard(1.25)}, '+'),
      buildElement('button', {class: 'hb-btn text small', type: 'button', onclick: () => fitBoard(true)},
        translate('chapters.fit'))));
  // a press on the board or a closed card drags the board, or is a click when it hardly moves; a press in the
  // open card is the card's own (selecting text, its scrollbar)
  let press = null;
  nodes.boardViewport.addEventListener('pointerdown', (event) => {
    if (event.target.closest('.wb-card.open, .wb-tools') || event.button !== 0) return;
    press = {startX: event.clientX, startY: event.clientY, x: event.clientX - board.x, y: event.clientY - board.y,
      card: event.target.closest('.wb-card'), isDragging: false};
    nodes.boardViewport.setPointerCapture(event.pointerId);
  });
  nodes.boardViewport.addEventListener('pointermove', (event) => {
    if (!press) return;
    if (!press.isDragging && Math.hypot(event.clientX - press.startX, event.clientY - press.startY) < BOARD_CLICK_PIXELS) {
      return;
    }
    press.isDragging = true;
    nodes.boardViewport.classList.add('dragging');
    board.x = event.clientX - press.x;
    board.y = event.clientY - press.y;
    board.isMoved = true;
    applyBoardTransform(false);
  });
  nodes.boardViewport.addEventListener('pointerup', () => {
    if (press && !press.isDragging) openBoardCard(press.card ? press.card.dataset.cardId : null);
    press = null;
    nodes.boardViewport.classList.remove('dragging');
  });
  nodes.boardViewport.addEventListener('pointercancel', () => {
    press = null;
    nodes.boardViewport.classList.remove('dragging');
  });
  nodes.boardViewport.addEventListener('wheel', (event) => {
    if (event.target.closest('.wb-tools')) return;
    if (!(event.ctrlKey || event.metaKey) && event.target.closest('.wb-card.open')) return;  // the card scrolls
    event.preventDefault();
    if (event.ctrlKey || event.metaKey) {
      const viewportRect = nodes.boardViewport.getBoundingClientRect();
      zoomBoard(Math.exp(-event.deltaY / 300), event.clientX - viewportRect.left, event.clientY - viewportRect.top);
    } else {
      board.x -= event.deltaX;
      board.y -= event.deltaY;
      board.isMoved = true;
      applyBoardTransform(false);
    }
  }, {passive: false});
  nodes.whiteboard.replaceChildren(nodes.boardViewport);
  board.isFitted = false;
  board.openCardId = null;
  applyBoardTransform(false);
  // pictures loading change the cards' heights, and the window its size: the arrows follow, and so does the fit
  // until the viewer moves the board
  nodes.boardResizeObserver?.disconnect();
  nodes.boardResizeObserver = new ResizeObserver(() => {
    if (chapterModeName !== 'whiteboard') return;
    drawBoardArrows();
    if (!board.isMoved) fitBoard(board.fitsAll);
  });
  nodes.boardResizeObserver.observe(nodes.boardViewport);
  nodes.boardResizeObserver.observe(nodes.boardCanvas);
}

function showChapters() {
  const json = JSON.stringify([pageData.chapters, pageData.board]);
  if (json === chaptersJson) return;
  chaptersJson = json;
  if (activeScreen) placeVideo(null);
  if (pageData.chapters) buildChaptersView(pageData.chapters); else nodes.chapters.replaceChildren();
  if (pageData.board) buildWhiteboardView(pageData.board); else nodes.whiteboard.replaceChildren();
  applyChapterMode();
}

function applyChapterMode() {
  const modeName = checkIsChapterModeAvailable(chapterModeName) ? chapterModeName : null;
  document.body.classList.toggle('chapters-mode', modeName === 'chapters');
  document.body.classList.toggle('whiteboard-mode', modeName === 'whiteboard');
  for (const [name, button] of [['chapters', nodes.chaptersMode], ['whiteboard', nodes.whiteboardMode]]) {
    if (!button) continue;
    button.setAttribute('aria-pressed', String(modeName === name));
    button.hidden = !checkIsChapterModeAvailable(name);
  }
  if (modeName !== 'chapters' && activeScreen) { video.pause(); placeVideo(null); }
  const isWhiteboardOn = modeName === 'whiteboard';
  if (isWhiteboardOn && video && !video.paused) video.pause();
  for (const button of [nodes.addComment, nodes.subtitles]) if (button) button.disabled = isWhiteboardOn;
  if (isWhiteboardOn) {
    requestAnimationFrame(() => {
      drawBoardArrows();
      if (!board.isFitted) fitBoard(false);
    });
  }
  showChapterProgress();
}

function setChapterMode(name) {
  if (!checkIsChapterModeAvailable(name) || !video) return;
  chapterModeName = chapterModeName === name ? null : name;
  try { localStorage.setItem('chapterMode', chapterModeName || 'off'); } catch (error) { /* private window */ }
  if (chapterModeName && isTheaterModeOn) toggleTheaterMode();
  applyChapterMode();
  showChapterModeTop('smooth');
}

// The chapters view opens with the toolbar just under the header, so the buttons stay in sight above it; the
// whiteboard is the whole page and does not scroll. Either way a reload opens there, not where the page was.
function showChapterModeTop(behavior) {
  history.scrollRestoration = chapterModeName ? 'manual' : 'auto';
  if (chapterModeName === 'chapters') nodes.toolbar.scrollIntoView({behavior, block: 'start'});
  else if (chapterModeName === 'whiteboard') window.scrollTo(0, 0);
}

async function fetchDataUrl(url) {
  const response = await fetch(url);
  if (!response.ok) return null;
  const blob = await response.blob();
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => resolve(null);
    reader.readAsDataURL(blob);
  });
}

function escapeHtml(text) {
  return text.replace(/[&<>"]/g, (character) => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'})[character]);
}

// Copying a card puts rich text on the clipboard, pictures inside, for notes apps, and Markdown as the plain text: its
// claim as the first heading, then its numbered points. The pictures go in as data URLs: the ones already shown are
// remembered when they load, and the rest are fetched while the clipboard waits. Where the page may
// not write the clipboard itself (some embedded browsers), the browser's own copy of a selection is used, with the
// remembered pictures and links for the rest.
const imageDataUrlByUrlMap = new Map();

function rememberImageDataUrl(image) {
  if (imageDataUrlByUrlMap.has(image.src) || !image.naturalWidth) return;
  const canvas = buildElement('canvas', {width: image.naturalWidth, height: image.naturalHeight});
  canvas.getContext('2d').drawImage(image, 0, 0);
  try { imageDataUrlByUrlMap.set(image.src, canvas.toDataURL('image/jpeg', 0.86)); } catch (error) { /* tainted */ }
}

function getPointImageUrl(point, episodeId) {
  return new URL(point.frame ? getFrameUrl(point.frame, episodeId) : getHandoutImageUrl(point.image, episodeId),
    window.location.href).href;
}

function listCardPoints(points) {
  return points.flatMap((point) => [point, ...listCardPoints(point.points || [])]);
}

function buildPointsMarkdown(points, depth, episodeId) {
  const indent = '   '.repeat(depth);
  return points.map((point, index) => [
    `${indent}${index + 1}. ${point.text}`,
    ...(point.points && point.points.length ? [buildPointsMarkdown(point.points, depth + 1, episodeId)] : []),
    ...(point.frame || point.image
      ? [`${indent}   ![${point.caption || ''}](${getPointImageUrl(point, episodeId)})`,
        ...(point.caption ? [`${indent}   *${point.caption}*`] : [])]
      : []),
  ].join('\n')).join('\n');
}

function buildCardMarkdown(card) {
  return `# ${card.title}\n\n${buildPointsMarkdown(card.points, 0, card.episodeId)}`;
}

function formatInlineHtml(text) {
  return escapeHtml(text).replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>').replace(/==([^=]+)==/g, '<mark>$1</mark>');
}

function buildPointsHtml(points, getImageSource, episodeId) {
  return `<ol>${points.map((point) => {
    const source = point.frame || point.image ? getImageSource(getPointImageUrl(point, episodeId)) : null;
    return `<li><p>${formatInlineHtml(point.text)}</p>`
      + (point.points && point.points.length ? buildPointsHtml(point.points, getImageSource, episodeId) : '')
      + (source ? `<p><img src="${escapeHtml(source)}" alt="${escapeHtml(point.caption || '')}"></p>` : '')
      + (point.caption ? `<p><em>${escapeHtml(point.caption)}</em></p>` : '') + '</li>';
  }).join('')}</ol>`;
}

function buildCardHtml(card, getImageSource) {
  return `<h1>${formatInlineHtml(card.title)}</h1>\n${buildPointsHtml(card.points, getImageSource, card.episodeId)}`;
}

async function buildCardHtmlBlob(card) {
  const urls = listCardPoints(card.points).filter((point) => point.frame || point.image)
    .map((point) => getPointImageUrl(point, card.episodeId));
  await Promise.all(urls.filter((url) => !imageDataUrlByUrlMap.has(url)).map(async (url) => {
    const dataUrl = await fetchDataUrl(url);
    if (dataUrl) imageDataUrlByUrlMap.set(url, dataUrl);
  }));
  return new Blob([buildCardHtml(card, (url) => imageDataUrlByUrlMap.get(url))], {type: 'text/html'});
}

function copySelectionOf(html) {
  const holder = buildElement('div', {contenteditable: 'true', style: 'position:fixed;left:-10000px;top:0', html});
  document.body.append(holder);
  const range = document.createRange();
  range.selectNodeContents(holder);
  const selection = window.getSelection();
  selection.removeAllRanges();
  selection.addRange(range);
  let isCopied = false;
  try { isCopied = document.execCommand('copy'); } catch (error) { isCopied = false; }
  selection.removeAllRanges();
  holder.remove();
  return isCopied;
}

async function copyCard(card) {
  const markdown = buildCardMarkdown(card);
  let isCopied = false;
  try {
    await navigator.clipboard.write([new ClipboardItem({'text/html': buildCardHtmlBlob(card),
      'text/plain': new Blob([markdown], {type: 'text/plain'})})]);
    isCopied = true;
  } catch (error) {
    isCopied = copySelectionOf(buildCardHtml(card, (url) => imageDataUrlByUrlMap.get(url) || url));
  }
  showToast(translate(isCopied ? 'chapters.copied' : 'chapters.copyFailed'));
}

function togglePlay() {
  if (!video) return;
  if (document.body.classList.contains('chapters-mode') && !activeScreen) {
    // the chapters view shows no player until a part plays: play where the video is, in that part's frame
    const parts = pageData.chapters.parts;
    const partIndex = Math.max(0, parts.findIndex((part) => video.currentTime < part.segments[part.segments.length - 1].endSeconds));
    playChapters(partIndex, video.currentTime);
    return;
  }
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
  nodes.addComment = buildElement('button', {class: 'hb-btn fill', type: 'button', onclick: startComment},
    buildIcon('plus'), translate('video.addComment'), buildElement('kbd', {}, 'M'));
  nodes.theaterMode = video
    ? buildElement('button', {class: 'hb-btn outline', type: 'button', 'aria-pressed': String(isTheaterModeOn),
      onclick: toggleTheaterMode}, translate('video.theaterMode'), buildElement('kbd', {}, 'T'))
    : null;
  // shown once notes.yaml fits the delivered video (for the whiteboard, any episode's), which the agent may write
  // while the page is open
  nodes.chaptersMode = video
    ? buildElement('button', {class: 'hb-btn outline', type: 'button', hidden: !checkIsChapterModeAvailable('chapters'),
      onclick: () => setChapterMode('chapters')}, translate('chapters.button'), buildElement('kbd', {}, 'N'))
    : null;
  nodes.whiteboardMode = video
    ? buildElement('button', {class: 'hb-btn outline', type: 'button', hidden: !checkIsChapterModeAvailable('whiteboard'),
      onclick: () => setChapterMode('whiteboard')}, translate('chapters.whiteboardButton'), buildElement('kbd', {}, 'W'))
    : null;
  if (checkIsChapterModeAvailable(chapterModeName)) isTheaterModeOn = false;  // one view at a time
  nodes.videoHome = buildElement('div', {class: 'video-home'}, video);
  nodes.chapters = buildElement('section', {class: 'chapters', 'aria-label': translate('chapters.button')});
  nodes.whiteboard = buildElement('section', {class: 'whiteboard', 'aria-label': translate('chapters.whiteboardButton')});
  if (video) video.addEventListener('timeupdate', showChapterProgress);
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
    video && nodes.videoHome,
    nodes.toolbar = buildElement('div', {class: 'toolbar'},
      nodes.addComment,
      nodes.subtitles, nodes.theaterMode, nodes.chaptersMode, nodes.whiteboardMode, keyHints),
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
  applyTheaterMode();
  if (checkIsChapterModeAvailable(chapterModeName)) requestAnimationFrame(() => showChapterModeTop('instant'));
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
  // the whiteboard shows no video: playing and commenting wait until it closes, and Esc closes its open card
  if (document.body.classList.contains('whiteboard-mode')) {
    if ([' ', 'ArrowLeft', 'ArrowRight', 'm', 'c'].includes(key)) return;
    if (key === 'Escape' && board.openCardId) {
      openBoardCard(null);
      event.preventDefault();
      return;
    }
  }
  if (key === ' ') togglePlay();
  else if (key === 'ArrowLeft') seekBy(-SEEK_SECONDS);
  else if (key === 'ArrowRight') seekBy(SEEK_SECONDS);
  else if (key === 'm') startComment();
  else if (key === 'c') toggleSubtitles();
  else if (key === 't') toggleTheaterMode();
  else if (key === 'n') setChapterMode('chapters');
  else if (key === 'w') setChapterMode('whiteboard');
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
