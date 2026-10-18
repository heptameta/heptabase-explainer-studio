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
  // the Heptabase app's whiteboard (its map icon; the video page holds the gradients the app fills it with in its
  // toolbar), more, refresh page, breadcrumb separator and zoom to fit icons
  whiteboard: '<svg viewBox="0 0 24 24" aria-hidden="true">'
    + '<path d="m21.32 5.04999-6-2h-.07c-.0465-.00467-.0934-.00467-.14 0h-.23-.13-.07l-5.68 1.95-5.68-1.95c-.15038-.04958-.31039-.06275-.46686-.03841s-.30492.08549-.43314.17841c-.12924.09202-.23473.21347-.30776.35431s-.1115.29704-.11224.45569v14.00001c-.00054.2096.06482.4141.18685.5846.12202.1705.29453.2983.49315.3654l6 2c.20145.0657.41856.0657.62 0l5.7-1.9 5.68 1.95c.1062.0144.2138.0144.32 0 .2091.0029.4132-.0639.58-.19.1292-.092.2347-.2135.3078-.3543.073-.1409.1115-.2971.1122-.4557v-14.00001c.0005-.20964-.0648-.41415-.1868-.58463-.1221-.17047-.2946-.29828-.4932-.36537zm-13.32 13.56001-4-1.33v-11.89001l4 1.33zm6-1.33-4 1.33v-11.89001l4-1.33zm6 1.33-4-1.33v-11.89001l4 1.33z"/></svg>',
  more: '<svg viewBox="0 0 18 18" aria-hidden="true"><circle cx="2.4" cy="9" r="2"/><circle cx="9" cy="9" r="2"/><circle cx="15.6" cy="9" r="2"/></svg>',
  refresh: '<svg viewBox="0 0 18 18" aria-hidden="true"><path d="M15.75 8.25A.75.75 0 0015 9a6.037 6.037 0 11-1.665-4.125h-1.8a.75.75 0 100 1.5h3.397a.75.75 0 00.75-.75V2.25a.75.75 0 10-1.5 0v1.328A7.5 7.5 0 1016.5 9a.75.75 0 00-.75-.75z"/></svg>',
  // the app's sign out and unlink icons
  signOut: '<svg viewBox="0 0 22 22" aria-hidden="true"><path d="m11.5415 11.9174-2.10835 2.0992c-.08592.0852-.15411.1866-.20065.2983s-.0705.2315-.0705.3525.02396.2408.0705.3525.11473.2131.20065.2983c.08522.086.1866.1542.2983.2007.11171.0465.23152.0705.35255.0705.121 0 .2408-.024.3525-.0705s.2131-.1147.2983-.2007l3.6667-3.6666c.0834-.0872.1489-.19.1925-.3025.0917-.2232.0917-.4735 0-.6967-.0436-.1125-.1091-.2153-.1925-.3025l-3.6667-3.66666c-.0855-.08547-.1869-.15326-.2986-.19952-.1117-.04625-.2313-.07006-.3522-.07006-.12089 0-.24058.02381-.35225.07006-.11167.04626-.21313.11405-.2986.19952s-.15327.18694-.19952.29861c-.04626.11167-.07006.23135-.07006.35223 0 .12087.0238.24055.07006.35222.04625.11167.11405.21314.19952.29861l2.10835 2.09919h-8.79085c-.24311 0-.47627.0966-.64818.2685s-.26849.405-.26849.6481c0 .2432.09658.4763.26849.6482s.40507.2685.64818.2685zm-.5408-10.08332c-1.71322-.00765-3.39424.46494-4.85245 1.36417-1.45822.89923-2.63525 2.18911-3.3976 3.72333-.1094.2188-.1274.4721-.05004.70418.07736.23207.24374.42391.46254.53332.2188.1094.47211.1274.70418.05004.23208-.07736.42392-.24374.53332-.46254.57951-1.17029 1.46101-2.1646 2.55342-2.88018s2.35608-1.12647 3.66043-1.1902c1.3044-.06373 2.6021.222 3.759.82768 1.157.60567 2.1312 1.50931 2.8221 2.61753.6908 1.10821 1.0732 2.38081 1.1076 3.68629.0344 1.3054-.2805 2.5964-.912 3.7395-.6315 1.143-1.5568 2.0967-2.6803 2.7624-1.1235.6658-2.4043 1.0194-3.7102 1.0245-1.36691.0059-2.70774-.3737-3.86867-1.0952-1.16092-.7215-2.09489-1.7558-2.69471-2.984-.1094-.2188-.30124-.3852-.53332-.4625-.23208-.0774-.48538-.0594-.70418.05-.21881.1094-.38519.3013-.46255.5333-.07736.2321-.05935.4854.05005.7042.72676 1.4626 1.83106 2.7044 3.19868 3.5971 1.36762.8926 2.94889 1.4037 4.5803 1.4803 1.6313.0766 3.2535-.284 4.6988-1.0445s2.6611-1.8934 3.5218-3.2814c.8606-1.388 1.3348-2.9807 1.3735-4.6134.0387-1.63271-.3595-3.24612-1.1534-4.67333s-1.9547-2.61641-3.3623-3.44458-3.0109-1.26525-4.644-1.26601z"/></svg>',
  unlink: '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.173 7.06a.672.672 0 0 0 .174-1.333l-1.174-.294a.667.667 0 1 0-.346 1.287L3 7.033a.52.52 0 0 0 .173.027Zm2.574-3.727a.667.667 0 0 0 .666.494c.058.009.116.009.174 0a.667.667 0 0 0 .466-.814L6.74 1.84a.667.667 0 1 0-1.287.347l.294 1.146ZM8.967 10A.667.667 0 0 0 8 10l-2.333 2.373a1.473 1.473 0 0 1-2.04 0 1.433 1.433 0 0 1 0-2.04L6 8a.667.667 0 1 0-.94-.94L2.667 9.387a2.79 2.79 0 1 0 3.946 3.946l2.354-2.353a.667.667 0 0 0 0-.98ZM3.453 4.393a.667.667 0 0 0 1.134-.47.667.667 0 0 0-.194-.47l-.86-.86a.667.667 0 0 0-.94.94l.86.86Zm10.72 4.887L13 8.967a.667.667 0 1 0-.333 1.286l1.173.314h.173a.672.672 0 1 0 .174-1.334l-.014.047Zm-3.92 3.387a.667.667 0 0 0-1.286.346l.313 1.174a.667.667 0 0 0 .667.493.761.761 0 0 0 .173 0 .667.667 0 0 0 .473-.82l-.34-1.193Zm2.294-1.047a.667.667 0 0 0-.94.94l.86.86a.667.667 0 0 0 .94 0 .667.667 0 0 0 0-.94l-.86-.86Zm1.586-6.953a2.772 2.772 0 0 0-4.746-2L7.033 5.04A.681.681 0 1 0 8 6l2.333-2.373a1.474 1.474 0 0 1 2.04 0 1.433 1.433 0 0 1 0 2.04L10 8a.667.667 0 0 0 0 .94.667.667 0 0 0 .94 0l2.393-2.327c.51-.52.798-1.218.8-1.946Z"/></svg>',
  slash: '<svg viewBox="0 0 4 14" aria-hidden="true"><path d="m2.90909 0h1.09091l-2.90909 14h-1.09091z"/></svg>',
  focus: '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m21 11h-1.07c-.2232-1.76002-1.0251-3.39592-2.2796-4.65041s-2.8904-2.0564-4.6504-2.27959v-1.07c0-.26522-.1054-.51957-.2929-.70711-.1875-.18753-.4419-.29289-.7071-.29289s-.5196.10536-.7071.29289c-.1875.18754-.2929.44189-.2929.70711v1.07c-1.76002.22319-3.39592 1.0251-4.65041 2.27959s-2.0564 2.89039-2.27959 4.65041h-1.07c-.26522 0-.51957.1054-.70711.2929-.18753.1875-.29289.4419-.29289.7071s.10536.5196.29289.7071c.18754.1875.44189.2929.70711.2929h1.07c.22319 1.76 1.0251 3.3959 2.27959 4.6504s2.89039 2.0564 4.65041 2.2796v1.07c0 .2652.1054.5196.2929.7071s.4419.2929.7071.2929.5196-.1054.7071-.2929.2929-.4419.2929-.7071v-1.07c1.76-.2232 3.3959-1.0251 4.6504-2.2796s2.0564-2.8904 2.2796-4.6504h1.07c.2652 0 .5196-.1054.7071-.2929s.2929-.4419.2929-.7071-.1054-.5196-.2929-.7071-.4419-.2929-.7071-.2929zm-9 7c-1.1867 0-2.34673-.3519-3.33342-1.0112-.9867-.6593-1.75573-1.5963-2.20986-2.6927-.45412-1.0964-.57294-2.3028-.34143-3.4666.23151-1.16393.80295-2.23303 1.64207-3.07214.83911-.83912 1.90821-1.41056 3.07214-1.64207 1.1638-.23151 2.3702-.11269 3.4666.34143 1.0964.45413 2.0334 1.22316 2.6927 2.20986.6593.98669 1.0112 2.14672 1.0112 3.33342 0 1.5913-.6321 3.1174-1.7574 4.2426-1.1252 1.1253-2.6513 1.7574-4.2426 1.7574zm0-9c-.5933 0-1.1734.17595-1.6667.50559-.49336.32965-.87788.79821-1.10494 1.34631-.22706.5482-.28647 1.1514-.17072 1.7334.11576.5819.40148 1.1165.82104 1.536.41952.4196.95412.7053 1.53602.8211.582.1157 1.1852.0563 1.7334-.1708.5481-.227 1.0167-.6115 1.3463-1.1049.3297-.4933.5056-1.0734.5056-1.6667 0-.7956-.3161-1.5587-.8787-2.12132-.5626-.56261-1.3257-.87868-2.1213-.87868zm0 4c-.1978 0-.3911-.0586-.5556-.1685-.1644-.1099-.2926-.2661-.3683-.4488s-.0955-.3838-.0569-.5778.1338-.3722.2737-.512c.1398-.1399.318-.2351.512-.2737s.3951-.0188.5778.0569.3389.2039.4488.3683c.1099.1645.1685.3578.1685.5556 0 .2652-.1054.5196-.2929.7071s-.4419.2929-.7071.2929z"/></svg>',
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

// A key an input method (Chinese, Japanese) takes while it composes text, such as the Enter that confirms a candidate:
// neither a save nor a shortcut.
function checkIsInputMethodKey(event) {
  return event.isComposing || event.keyCode === 229;
}

// The key a shortcut goes by: the letter the key types on a Latin layout (QWERTY, AZERTY, Dvorak), else the letter at
// its place on a US keyboard, for layouts and input methods that type something else there (Zhuyin's W types ㄊ).
// Other keys (Space, the arrows) go by their KeyboardEvent.key.
function resolveShortcutKey(event) {
  if (/^[a-z]$/i.test(event.key)) return event.key.toLowerCase();
  const letterMatch = /^Key([A-Z])$/.exec(event.code);
  if (letterMatch) return letterMatch[1].toLowerCase();
  return event.code === 'Space' ? ' ' : event.key;
}

function checkIsTyping(target) {
  const node = target || document.activeElement;
  return !!node && (node.tagName === 'TEXTAREA' || node.tagName === 'SELECT' || node.isContentEditable
    || (node.tagName === 'INPUT' && !['button', 'checkbox', 'radio'].includes(node.type)));
}
