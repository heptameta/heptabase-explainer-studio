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
  // the Heptabase app's note card, copy and whiteboard icons
  card: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 10h1c.2652 0 .5196-.10536.7071-.29289.1875-.18754.2929-.44189.2929-.70711s-.1054-.51957-.2929-.70711c-.1875-.18753-.4419-.29289-.7071-.29289h-1c-.26522 0-.51957.10536-.70711.29289-.18753.18754-.29289.44189-.29289.70711s.10536.51957.29289.70711c.18754.18753.44189.29289.70711.29289zm0 2c-.26522 0-.51957.1054-.70711.2929-.18753.1875-.29289.4419-.29289.7071s.10536.5196.29289.7071c.18754.1875.44189.2929.70711.2929h6c.2652 0 .5196-.1054.7071-.2929s.2929-.4419.2929-.7071-.1054-.5196-.2929-.7071-.4419-.2929-.7071-.2929zm11-3.06c-.0104-.09187-.0305-.18237-.06-.27v-.09c-.0481-.10282-.1122-.19733-.19-.28l-6-6c-.0827-.07778-.1772-.14192-.28-.19-.0298-.00424-.0601-.00424-.09 0-.1016-.05826-.2138-.09566-.33-.11h-6.05c-.79565 0-1.55871.31607-2.12132.87868s-.87868 1.32567-.87868 2.12132v14c0 .7956.31607 1.5587.87868 2.1213s1.32567.8787 2.12132.8787h10c.7956 0 1.5587-.3161 2.1213-.8787s.8787-1.3257.8787-2.1213v-10s0 0 0-.06zm-6-3.53 2.59 2.59h-1.59c-.2652 0-.5196-.10536-.7071-.29289-.1875-.18754-.2929-.44189-.2929-.70711zm4 13.59c0 .2652-.1054.5196-.2929.7071s-.4419.2929-.7071.2929h-10c-.26522 0-.51957-.1054-.70711-.2929-.18753-.1875-.29289-.4419-.29289-.7071v-14c0-.26522.10536-.51957.29289-.70711.18754-.18753.44189-.29289.70711-.29289h5v3c0 .79565.3161 1.55871.8787 2.12132s1.3257.87868 2.1213.87868h3zm-3-3h-6c-.26522 0-.51957.1054-.70711.2929-.18753.1875-.29289.4419-.29289.7071s.10536.5196.29289.7071c.18754.1875.44189.2929.70711.2929h6c.2652 0 .5196-.1054.7071-.2929s.2929-.4419.2929-.7071-.1054-.5196-.2929-.7071-.4419-.2929-.7071-.2929z"/></svg>',
  copy: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m10 12c0-.2652.1054-.5196.2929-.7071s.4419-.2929.7071-.2929h6c.2652 0 .5196.1054.7071.2929s.2929.4419.2929.7071-.1054.5196-.2929.7071-.4419.2929-.7071.2929h-6c-.2652 0-.5196-.1054-.7071-.2929s-.2929-.4419-.2929-.7071z"/><path d="m10 16c0-.2652.1054-.5196.2929-.7071s.4419-.2929.7071-.2929h6c.2652 0 .5196.1054.7071.2929s.2929.4419.2929.7071-.1054.5196-.2929.7071-.4419.2929-.7071.2929h-6c-.2652 0-.5196-.1054-.7071-.2929s-.2929-.4419-.2929-.7071z"/><path clip-rule="evenodd" d="m7 17v1c0 .7956.31607 1.5587.87868 2.1213s1.32567.8787 2.12132.8787h8c.7956 0 1.5587-.3161 2.1213-.8787s.8787-1.3257.8787-2.1213v-8c0-.79565-.3161-1.55871-.8787-2.12132s-1.3257-.87868-2.1213-.87868h-1v-1c0-.79565-.3161-1.55871-.8787-2.12132s-1.3257-.87868-2.1213-.87868h-8c-.79565 0-1.55871.31607-2.12132.87868s-.87868 1.32567-.87868 2.12132v8c0 .7956.31607 1.5587.87868 2.1213s1.32567.8787 2.12132.8787zm11.7071 1.7071c.1875-.1875.2929-.4419.2929-.7071v-8c0-.26522-.1054-.51957-.2929-.70711-.1875-.18753-.4419-.29289-.7071-.29289h-8c-.26522 0-.51957.10536-.70711.29289-.18753.18754-.29289.44189-.29289.70711v8c0 .2652.10536.5196.29289.7071.18754.1875.44189.2929.70711.2929h8c.2652 0 .5196-.1054.7071-.2929zm-8.7071-11.7071h5v-1c0-.26522-.1054-.51957-.2929-.70711-.1875-.18753-.4419-.29289-.7071-.29289h-8c-.26522 0-.51957.10536-.70711.29289-.18753.18754-.29289.44189-.29289.70711v8c0 .2652.10536.5196.29289.7071.18754.1875.44189.2929.70711.2929h1v-5c0-.79565.31607-1.55871.87868-2.12132s1.32567-.87868 2.12132-.87868z" fill-rule="evenodd"/></svg>',
  whiteboard: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m21.32 5.04999-6-2h-.07c-.0465-.00467-.0934-.00467-.14 0h-.23-.13-.07l-5.68 1.95-5.68-1.95c-.15038-.04958-.31039-.06275-.46686-.03841s-.30492.08549-.43314.17841c-.12924.09202-.23473.21347-.30776.35431s-.1115.29704-.11224.45569v14.00001c-.00054.2096.06482.4141.18685.5846.12202.1705.29453.2983.49315.3654l6 2c.20145.0657.41856.0657.62 0l5.7-1.9 5.68 1.95c.1062.0144.2138.0144.32 0 .2091.0029.4132-.0639.58-.19.1292-.092.2347-.2135.3078-.3543.073-.1409.1115-.2971.1122-.4557v-14.00001c.0005-.20964-.0648-.41415-.1868-.58463-.1221-.17047-.2946-.29828-.4932-.36537zm-13.32 13.56001-4-1.33v-11.89001l4 1.33zm6-1.33-4 1.33v-11.89001l4-1.33zm6 1.33-4-1.33v-11.89001l4 1.33z"/></svg>',
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
