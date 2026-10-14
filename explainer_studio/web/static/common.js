// Shared by both pages: text in the series language, calls to the page server, page digest polling, small UI pieces.
'use strict';

const BOOT = window.BOOT;
// back, out, chevron, edit and trash are Unicons icons (https://github.com/Iconscout/unicons), under the Apache License
// 2.0 as released up to Unicons 4.0.0: see NOTICE.
const ICON_SVG_BY_NAME_MAP = {
  back: '<svg viewBox="0 0 12 13" aria-hidden="true"><path d="M8.5 5.775H4.703l1.65-1.645a.502.502 0 00-.71-.71l-2.5 2.5a.5.5 0 00-.105.165.5.5 0 000 .38.5.5 0 00.105.165l2.5 2.5a.5.5 0 00.82-.163.5.5 0 00-.11-.547l-1.65-1.645H8.5a.5.5 0 100-1z"/></svg>',
  out: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M11.947 4.413A.667.667 0 0011.333 4H4.667a.667.667 0 000 1.333h5.06L4.193 10.86a.667.667 0 00.217 1.093.668.668 0 00.73-.146l5.527-5.534v5.06a.667.667 0 001.333 0V4.667a.667.667 0 00-.053-.254z"/></svg>',
  chevron: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15.54 11.29-5.66-5.65a1 1 0 0 0-1.42 1.41l4.95 5-4.95 4.95a1 1 0 0 0 1.42 1.41l5.66-5.65a1 1 0 0 0 0-1.47z"/></svg>',
  edit: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 18.08h4.24a1 1 0 0 0 .71-.29l6.92-6.93L19.71 8a1 1 0 0 0 0-1.42l-4.24-4.29a1 1 0 0 0-1.42 0l-2.82 2.83-6.94 6.93a1 1 0 0 0-.29.71V17a1 1 0 0 0 1 1.08zm9.76-13.67 2.83 2.83-1.42 1.42-2.83-2.83zM6 12.17l5.94-5.94 2.83 2.83L8.83 15H6zM21 20H3a1 1 0 0 0 0 2h18a1 1 0 0 0 0-2z"/></svg>',
  trash: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 18a1 1 0 0 0 1-1v-6a1 1 0 0 0-2 0v6a1 1 0 0 0 1 1zm10-12h-4V5a3 3 0 0 0-3-3h-2a3 3 0 0 0-3 3v1H4a1 1 0 0 0 0 2h1v11a3 3 0 0 0 3 3h8a3 3 0 0 0 3-3V8h1a1 1 0 0 0 0-2zM10 5a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1v1h-4zm7 14a1 1 0 0 1-1 1H8a1 1 0 0 1-1-1V8h10zm-3-1a1 1 0 0 0 1-1v-6a1 1 0 0 0-2 0v6a1 1 0 0 0 1 1z"/></svg>',
  plus: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M8 2.5a.75.75 0 0 1 .75.75v4h4a.75.75 0 0 1 0 1.5h-4v4a.75.75 0 0 1-1.5 0v-4h-4a.75.75 0 0 1 0-1.5h4v-4A.75.75 0 0 1 8 2.5z"/></svg>',
};

function translate(key, params) {
  let text = BOOT.strings[key];
  if (text === undefined) text = key;
  if (params) {
    text = text.replace(/\{(\w+)\}/g, (match, name) => (params[name] !== undefined ? String(params[name]) : match));
  }
  return text;
}

// buildElement('div', {class: 'x', onclick: fn}, child, 'text', ...)
function buildElement(tag, attributes, ...children) {
  const node = document.createElement(tag);
  for (const [name, value] of Object.entries(attributes || {})) {
    if (value === undefined || value === null || value === false) continue;
    if (name.startsWith('on')) node.addEventListener(name.slice(2), value);
    else if (name === 'html') node.innerHTML = value;
    else if (name === 'dataset') Object.assign(node.dataset, value);
    else if (value === true) node.setAttribute(name, '');
    else node.setAttribute(name, value);
  }
  for (const child of children.flat()) {
    if (child === undefined || child === null || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

function buildIcon(name) {
  const span = document.createElement('span');
  span.innerHTML = ICON_SVG_BY_NAME_MAP[name];
  return span.firstChild;
}

function formatTime(seconds) {
  if (seconds === null || seconds === undefined) return '';
  const wholeSeconds = Math.max(0, Math.floor(seconds));
  const hours = Math.floor(wholeSeconds / 3600), minutes = Math.floor((wholeSeconds % 3600) / 60);
  const restSeconds = wholeSeconds % 60;
  const tail = String(restSeconds).padStart(2, '0');
  return hours ? `${hours}:${String(minutes).padStart(2, '0')}:${tail}` : `${minutes}:${tail}`;
}

// Calls to the page server. Resolves to {isOk, status, body}; a dead server shows the stopped banner once.
let isServerGone = false;
async function callApi(method, path, body) {
  try {
    const response = await fetch(BOOT.baseUrl + path, {
      method,
      headers: body === undefined ? {} : {'Content-Type': 'application/json'},
      body: body === undefined ? undefined : JSON.stringify(body),
      cache: 'no-store',
    });
    let responseBody = null;
    try { responseBody = await response.json(); } catch (error) { responseBody = null; }
    if (isServerGone) { isServerGone = false; document.getElementById('stopped')?.remove(); }
    return {isOk: response.ok, status: response.status, body: responseBody || {}};
  } catch (error) {
    showStoppedBanner();
    return {isOk: false, status: 0, body: {}};
  }
}

function showStoppedBanner() {
  if (isServerGone) return;
  isServerGone = true;
  const command = BOOT.pageName === 'plan'
    ? 'explainer-studio plan open' : `explainer-studio video open ${BOOT.episodeId}`;
  const banner = buildElement('div', {id: 'stopped', class: 'hb-banner error', role: 'alert'},
    buildElement('b', {}, translate('common.stopped.title')),
    buildElement('div', {html: translate('common.stopped.body', {command: `<code>${command}</code>`})}));
  document.getElementById('app').prepend(banner);
}

let toastTimerId = null;
function showToast(text) {
  const node = document.getElementById('toast');
  node.textContent = text;
  node.hidden = false;
  clearTimeout(toastTimerId);
  toastTimerId = setTimeout(() => { node.hidden = true; }, 4000);
}

function growTextarea(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = textarea.scrollHeight + 2 + 'px';
}

// Ask the server every 2 s (only while the tab is visible) whether the page's files changed.
function watchPageDigest(query, getCurrentDigest, onChange) {
  let isBusy = false;
  async function pollPageDigest() {
    if (isBusy || document.visibilityState !== 'visible') return;
    isBusy = true;
    const result = await callApi('GET', '/api/page-digest' + query);
    isBusy = false;
    const nextPageDigest = result.body.pageDigest;
    if (result.isOk && nextPageDigest && nextPageDigest !== getCurrentDigest()) onChange(nextPageDigest);
  }
  setInterval(pollPageDigest, 2000);
  document.addEventListener('visibilitychange', pollPageDigest);
}

// Enter that confirms an input method's candidate (Chinese, Japanese) is not a save.
function checkIsImeEnter(event) {
  return event.isComposing || event.keyCode === 229;
}

function checkIsTyping(target) {
  const node = target || document.activeElement;
  return !!node && (node.tagName === 'TEXTAREA' || node.tagName === 'SELECT' || node.isContentEditable
    || (node.tagName === 'INPUT' && !['button', 'checkbox', 'radio'].includes(node.type)));
}
