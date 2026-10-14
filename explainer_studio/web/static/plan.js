// The plan page: the series plan as a document to read, top to bottom in the design's order. Only the production
// settings (narration provider, voice, budget, music, end credits) can be changed here; everything else is changed by
// asking the agent.
// A settings save is refused when plan.yaml changed after the page loaded it; the page then shows the latest plan.
'use strict';

let pageData = null;
let planVersion = null;
let pageDigest = null;
let notice = null;
let isDescriptionOpen = false;
let isRefreshWaiting = false;
let isEditable = true;

async function refreshPage() {
  const result = await callApi('GET', '/api/plan');
  if (!result.isOk) return;
  if (result.body.languageCode !== BOOT.languageCode) { window.location.reload(); return; }
  pageData = result.body;
  planVersion = pageData.planVersion;
  pageDigest = pageData.pageDigest;
  isEditable = !pageData.error && !pageData.problems.length;
  showPage();
}

function refreshWhenIdle(nextPageDigest) {
  if (nextPageDigest === pageDigest) return;
  const focused = document.activeElement;
  if (focused && focused.classList && focused.classList.contains('field')) { isRefreshWaiting = true; return; }
  refreshPage();
}

// The budget field ---------------------------------------------------------------------------------------------------
function parseBudget(text) {
  if (!text.trim()) return {value: null};
  const amount = Number(text.trim().replace(/^\$/, ''));
  if (!Number.isFinite(amount)) return {error: 'not_a_number'};
  if (amount < 0) return {error: 'negative'};
  return {value: amount};
}

function formatFieldId(fieldPath) { return 'f-' + fieldPath.join('-'); }

function setFieldError(fieldNode, errorCode) {
  fieldNode.classList.toggle('invalid', !!errorCode);
  const anchor = fieldNode.closest('.with-unit') || fieldNode;  // the message goes under the budget's box
  const next = anchor.nextElementSibling;
  if (next && next.classList.contains('field-error')) next.remove();
  if (errorCode) {
    anchor.after(buildElement('div', {class: 'field-error', role: 'alert'}, translate('plan.error.' + errorCode)));
  }
}

async function writePlanField(fieldNode, fieldPath, value) {
  const result = await callApi('POST', '/api/plan', {fieldPath, value, planVersion});
  if (result.isOk) {
    planVersion = result.body.planVersion;
    pageDigest = result.body.pageDigest;
    fieldNode.dataset.saved = fieldNode.value;
    setFieldError(fieldNode, null);
    if (isRefreshWaiting) { isRefreshWaiting = false; refreshPage(); }
    return true;
  }
  if (result.status === 409) {
    notice = {kind: 'conflict', text: fieldNode.value};
    await refreshPage();
    window.scrollTo({top: 0, behavior: 'smooth'});
  } else if (result.status === 422) {
    setFieldError(fieldNode, result.body.code || 'invalid');
    fieldNode.focus();
  } else if (result.status) {
    showToast(translate('common.error.unknown'));
  }
  return false;
}

// Enter or leaving the field saves; Esc puts the saved value back.
function buildBudgetField(plan) {
  // an omitted budget is the default; null (an empty field) is no limit
  const budgetUsd = plan.narration_budget_usd === undefined
    ? pageData.defaultNarrationBudgetUsd : plan.narration_budget_usd;
  const budgetText = budgetUsd === null ? '' : String(budgetUsd);
  const fieldPath = ['narration_budget_usd'];
  const input = buildElement('input', {class: 'field', id: formatFieldId(fieldPath), type: 'text', inputmode: 'decimal',
    value: budgetText, placeholder: translate('plan.budget.none'), 'aria-label': translate('plan.production.budget')});
  input.dataset.saved = budgetText;
  input.readOnly = !isEditable;
  input.addEventListener('input', () => setFieldError(input, null));
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      event.preventDefault();
      input.value = input.dataset.saved;
      setFieldError(input, null);
      input.blur();
    } else if (event.key === 'Enter' && !checkIsImeEnter(event)) {
      event.preventDefault();
      input.blur();
    }
  });
  input.addEventListener('blur', async () => {
    if (!isEditable || input.value === input.dataset.saved) {
      if (isRefreshWaiting) { isRefreshWaiting = false; refreshPage(); }
      return;
    }
    const parsed = parseBudget(input.value);
    if (parsed.error) { setFieldError(input, parsed.error); return; }
    await writePlanField(input, fieldPath, parsed.value);
  });
  return input;
}

function buildProperty(label, control, forFieldPath, ...hints) {
  return buildElement('div', {class: 'prop'},
    forFieldPath
      ? buildElement('label', {class: 'prop-k', for: formatFieldId(forFieldPath)}, label)
      : buildElement('div', {class: 'prop-k'}, label),
    buildElement('div', {class: 'prop-v'}, control,
      hints.filter(Boolean).map((hint) => buildElement('div', {class: 'hint'}, hint))));
}

function buildSection(title, meta, ...children) {
  return buildElement('section', {class: 'hb-section'},
    buildElement('h2', {}, title, meta ? buildElement('span', {class: 'hb-meta'}, meta) : null), ...children);
}

// Sections ----------------------------------------------------------------------------------------------------------
function buildNotices() {
  const banners = [];
  if (notice && notice.kind === 'conflict') {
    banners.push(buildElement('div', {class: 'hb-banner warn', role: 'alert'},
      buildElement('b', {}, translate('plan.conflict.title')),
      buildElement('div', {}, translate('plan.conflict.body')),
      notice.text
        ? buildElement('div', {class: 'hint'}, translate('plan.conflict.yours'), ' ', buildElement('i', {}, notice.text))
        : null,
      buildElement('div', {class: 'actions'}, buildElement('button', {class: 'hb-btn outline small', type: 'button',
        onclick: () => { notice = null; showPage(); }}, translate('common.dismiss')))));
  }
  if (pageData.error || pageData.problems.length) {
    banners.push(buildElement('div', {class: 'hb-banner error', role: 'alert'},
      buildElement('b', {}, translate('plan.problems.title')),
      buildElement('div', {}, translate('plan.problems.body')),
      buildElement('ul', {}, (pageData.error ? [pageData.error] : pageData.problems)
        .map((problem) => buildElement('li', {}, problem)))));
  }
  return banners;
}

function buildText(value, className = 'static') {
  return buildElement('div', {class: className},
    value === null || value === undefined || value === '' ? translate('plan.none') : String(value));
}

function buildTermList(values) {
  const terms = Array.isArray(values) ? values.filter(Boolean) : [];
  return terms.length
    ? buildElement('div', {class: 'static terms'}, terms.map((term) => buildElement('span', {class: 'hb-chip'}, term)))
    : buildText(null);
}

// "中文（台灣）" rather than "zh-TW", in the page's language; the code itself when the browser cannot name it
function formatLanguageName(languageCode) {
  if (!languageCode) return languageCode;
  try {
    return new Intl.DisplayNames([BOOT.languageCode], {type: 'language'}).of(languageCode) || languageCode;
  } catch (error) {
    return languageCode;
  }
}

function buildSeriesSection(plan) {
  const sources = Array.isArray(plan.sources) ? plan.sources : [];
  return buildSection(translate('plan.series.heading'), null, buildElement('div', {class: 'hb-card props'},
    buildProperty(translate('plan.series.sources'), sources.length
      ? buildElement('ul', {class: 'bullets sources'}, sources.map((source) => buildElement('li', {}, source)))
      : buildText(null)),
    buildProperty(translate('plan.series.language'), buildText(formatLanguageName(plan.language_code)), null,
      translate('plan.series.languageHint'))));
}

// The voice menu with a link to hear the chosen voice, and under it the voice's id, or for "Other" where to find
// one. The hint follows the menu before anything is saved.
function buildVoiceProperty(plan) {
  const label = translate('plan.production.voice');
  const fieldPath = ['narration', 'voice'];
  const narrationSettings = plan.narration && typeof plan.narration === 'object' ? plan.narration : null;
  const provider = narrationSettings
    ? pageData.narrationProviders.find((candidate) => candidate.name === narrationSettings.provider_name) : null;
  if (!provider) {
    return buildProperty(label, buildElement('select', {class: 'hb-select', id: formatFieldId(fieldPath), disabled: true},
      buildElement('option', {}, translate('plan.voice.chooseProvider'))), fieldPath);
  }
  const currentVoice = narrationSettings[provider.voiceField] ?? null;
  const voiceOptions = [];
  if (provider.hasAutomaticVoice) voiceOptions.push({id: '', displayName: translate('plan.voice.automatic')});
  voiceOptions.push(...provider.voices);
  if (currentVoice && !provider.voices.some((voice) => voice.id === currentVoice)) {
    voiceOptions.push({id: currentVoice, displayName: currentVoice});
  }
  const voiceSelect = buildElement('select',
    {class: 'hb-select', id: formatFieldId(fieldPath), disabled: !isEditable},
    voiceOptions.map((voice) => buildElement('option',
      {value: voice.id, selected: (voice.id || null) === currentVoice},
      voice.description ? translate('plan.voice.option', {name: voice.displayName, description: voice.description})
        : voice.displayName)),
    buildElement('option', {value: '__other__'}, translate('plan.voice.other')));
  const otherInput = buildElement('input', {class: 'hb-input', type: 'text', hidden: true,
    placeholder: translate('plan.voice.otherPlaceholder', {field: provider.voiceField})});
  const listenSlot = buildElement('span', {class: 'voice-listen'});  // "Listen", on the menu's row
  const hint = buildElement('div', {class: 'voice-hint'});

  function showHint() {
    fitSelectToSelection(voiceSelect);
    listenSlot.replaceChildren();
    hint.replaceChildren();
    if (voiceSelect.value === '__other__') {
      if (!provider.voicesPageUrl) return;
      hint.append(
        buildElement('span', {}, translate('plan.voice.findHint', {field: provider.voiceField})),
        buildExternalLink(provider.voicesPageUrl, translate('plan.voice.find', {name: provider.displayName})));
      return;
    }
    const voiceId = voiceSelect.value;
    if (!voiceId) return;  // macOS picks the voice itself
    const pageUrl = provider.voicePageUrlTemplate
      ? provider.voicePageUrlTemplate.replace('{voice_id}', encodeURIComponent(voiceId)) : provider.voicesPageUrl;
    // the id only when the name does not already say it (ElevenLabs ids, not OpenAI's "ash" or VoAI's "子墨")
    const voiceDisplayName = voiceOptions.find((voice) => voice.id === voiceId)?.displayName || voiceId;
    if (pageUrl) {
      listenSlot.append(buildExternalLink(pageUrl, translate('plan.voice.listen', {name: provider.displayName})));
    }
    if (voiceDisplayName.toLowerCase() !== voiceId.toLowerCase()) {
      hint.append(buildElement('span', {class: 'voice-id'},
        buildElement('span', {class: 'voice-id-field'}, provider.voiceField + ':'), buildElement('code', {}, voiceId)));
    }
  }

  async function writeOtherVoice() {
    const value = otherInput.value.trim();
    if (!value) return;
    await writePlanField(otherInput, fieldPath, value) && refreshPage();
  }
  otherInput.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' && !checkIsImeEnter(event)) { event.preventDefault(); writeOtherVoice(); }
    if (event.key === 'Escape') { otherInput.hidden = true; voiceSelect.value = currentVoice || ''; showHint(); }
  });
  otherInput.addEventListener('blur', writeOtherVoice);
  voiceSelect.addEventListener('change', async () => {
    showHint();
    if (voiceSelect.value === '__other__') { otherInput.hidden = false; otherInput.focus(); return; }
    otherInput.hidden = true;
    await writePlanField(voiceSelect, fieldPath, voiceSelect.value || null) && refreshPage();
  });
  showHint();
  return buildProperty(label, buildElement('div', {class: 'inline-controls'}, voiceSelect, otherInput, listenSlot),
    fieldPath, hint);
}

// A native menu is as wide as its longest option; size it to the option it shows, so a short choice ("Other…")
// does not sit in a box made for the longest voice.
const SELECT_CHROME_WIDTH_PIXELS = 9 + 28 + 2;  // left padding, the arrow's padding, the border
function fitSelectToSelection(select) {
  const context = (fitSelectToSelection.canvas ||= document.createElement('canvas')).getContext('2d');
  context.font = getComputedStyle(document.body).font;
  const text = select.options[select.selectedIndex]?.textContent || '';
  select.style.width = Math.ceil(context.measureText(text).width + SELECT_CHROME_WIDTH_PIXELS) + 'px';
}

function buildExternalLink(url, text) {
  return buildElement('a', {href: url, target: '_blank', rel: 'noopener'}, text + ' ↗');
}

function buildProductionSection(plan) {
  const narrationSettings = plan.narration && typeof plan.narration === 'object' ? plan.narration : null;
  const providerSelect = buildElement('select',
    {class: 'hb-select', id: formatFieldId(['narration', 'provider_name']), disabled: !isEditable},
    buildElement('option', {value: '', selected: !narrationSettings}, translate('plan.provider.none')),
    pageData.narrationProviders.map((provider) => buildElement('option',
      {value: provider.name, selected: narrationSettings && narrationSettings.provider_name === provider.name},
      provider.isPaid ? provider.displayName : translate('plan.provider.free', {name: provider.displayName}))));
  providerSelect.addEventListener('change', async () => {
    await writePlanField(providerSelect, ['narration', 'provider_name'], providerSelect.value || null) && refreshPage();
  });
  const budgetControl = buildElement('div', {class: 'with-unit'},
    buildElement('span', {class: 'unit'}, '$'),
    buildBudgetField(plan),
    buildElement('span', {class: 'unit'}, 'USD'));
  // the amount stands out from the sentence around it
  const [spentBefore, spentAfter] = translate('plan.budget.spent', {amount: '\u0000'}).split('\u0000');
  const spentText = buildElement('span', {class: 'budget-spent'}, spentBefore,
    buildElement('span', {class: 'amount'}, '$' + pageData.spentUsd.toFixed(2)), spentAfter);
  const musicProviderName = plan.background_music && typeof plan.background_music === 'object'
    ? plan.background_music.provider_name : 'synthesized-piano';
  const musicSelect = buildElement('select',
    {class: 'hb-select', id: formatFieldId(['background_music', 'provider_name']), disabled: !isEditable},
    pageData.musicProviderNames.map((providerName) => buildElement('option',
      {value: providerName, selected: providerName === musicProviderName}, translate('plan.music.' + providerName))));
  musicSelect.addEventListener('change', async () => {
    await writePlanField(musicSelect, ['background_music', 'provider_name'], musicSelect.value) && refreshPage();
  });
  const hasEndCredits = plan.has_end_credits !== false;  // an omitted switch is on
  const endCreditsSelect = buildElement('select',
    {class: 'hb-select', id: formatFieldId(['has_end_credits']), disabled: !isEditable},
    [true, false].map((value) => buildElement('option', {value: String(value), selected: value === hasEndCredits},
      translate(value ? 'plan.endCredits.on' : 'plan.endCredits.off'))));
  endCreditsSelect.addEventListener('change', async () => {
    await writePlanField(endCreditsSelect, ['has_end_credits'], endCreditsSelect.value === 'true') && refreshPage();
  });
  return buildSection(translate('plan.production.heading'), null, buildElement('div', {class: 'hb-card props'},
    buildProperty(translate('plan.production.provider'), providerSelect, ['narration', 'provider_name'],
      narrationSettings ? null : translate('plan.provider.hint')),
    buildVoiceProperty(plan),
    buildProperty(translate('plan.production.budget'),
      buildElement('div', {class: 'inline-controls'}, budgetControl, spentText), ['narration_budget_usd'],
      translate('plan.budget.hint')),
    buildProperty(translate('plan.production.music'), musicSelect, ['background_music', 'provider_name']),
    buildProperty(translate('plan.production.endCredits'), endCreditsSelect, ['has_end_credits'])));
}

function buildChevronIcon() {
  const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
  svg.setAttribute('viewBox', '0 0 16 16');
  svg.setAttribute('aria-hidden', 'true');
  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  path.setAttribute('d', 'M3.5 6l4.5 4.5L12.5 6');
  svg.append(path);
  return svg;
}

// A paragraph of the agent's Markdown-like text: lines starting with "- " or "* " become a bulleted list, and the other
// lines are joined as in Markdown, since the agent wraps long lines by hand.
const CJK_CHARACTER_PATTERN = /[　-〿぀-ヿ㐀-鿿＀-￯]/;
function joinWrappedLine(text, line) {
  if (!text) return line;
  // Chinese and Japanese put no space where a line was wrapped
  const isCjkJoin = CJK_CHARACTER_PATTERN.test(text.slice(-1)) || CJK_CHARACTER_PATTERN.test(line[0]);
  return text + (isCjkJoin ? '' : ' ') + line;
}

function buildParagraph(paragraph) {
  const blocks = [];
  for (const rawLine of paragraph.split('\n')) {
    const line = rawLine.trim();
    if (!line) continue;
    const bulletMatch = line.match(/^[-*]\s+(.*)$/);
    const lastBlock = blocks[blocks.length - 1];
    if (bulletMatch) {
      if (!lastBlock || lastBlock.kind !== 'list') blocks.push({kind: 'list', items: []});
      blocks[blocks.length - 1].items.push(bulletMatch[1]);
    } else if (lastBlock && lastBlock.kind === 'list') {
      lastBlock.items[lastBlock.items.length - 1] = joinWrappedLine(lastBlock.items[lastBlock.items.length - 1], line);
    } else if (lastBlock && lastBlock.kind === 'text') {
      lastBlock.text = joinWrappedLine(lastBlock.text, line);
    } else {
      blocks.push({kind: 'text', text: line});
    }
  }
  return blocks.map((block) => (block.kind === 'list'
    ? buildElement('ul', {class: 'bullets'}, block.items.map((item) => buildElement('li', {}, item)))
    : buildElement('p', {}, block.text)));
}

function buildAudienceSection(plan) {
  const audience = plan.audience && typeof plan.audience === 'object' ? plan.audience : {};
  const paragraphs = String(audience.description || '').trim().split(/\n\s*\n/).filter(Boolean);
  const shownParagraphs = isDescriptionOpen ? paragraphs : paragraphs.slice(0, 1);
  const prose = buildElement('div', {class: 'static prose'}, shownParagraphs.flatMap(buildParagraph));
  const toggleKey = isDescriptionOpen ? 'plan.audience.showLess' : 'plan.audience.showAll';
  const description = paragraphs.length > 1
    ? buildElement('div', {class: 'expandable'}, prose, buildElement('button', {class: 'hb-icon-btn chevron',
      type: 'button', 'aria-expanded': String(isDescriptionOpen), 'aria-label': translate(toggleKey),
      title: translate(toggleKey),
      onclick: () => { isDescriptionOpen = !isDescriptionOpen; showPage(); }}, buildChevronIcon()))
    : prose;
  const misconceptions = Array.isArray(audience.misconceptions) ? audience.misconceptions : [];
  return buildSection(translate('plan.audience.heading'), null, buildElement('div', {class: 'hb-card props'},
    buildProperty(translate('plan.audience.description'), description),
    buildProperty(translate('plan.audience.terms'), buildTermList(audience.unfamiliar_terms)),
    buildProperty(translate('plan.audience.misconceptions'), misconceptions.length
      ? buildElement('ul', {class: 'static misconceptions'}, misconceptions.map((misconception) => buildElement('li', {},
        buildElement('div', {}, misconception.belief),
        buildElement('div', {class: 'hb-meta'}, translate('plan.misconception.evidence'), ': ',
          misconception.evidence))))
      : buildText(null))));
}

function translateQuestionTypeDisplayName(pageEpisode) {
  const key = 'questionType.' + pageEpisode.questionType;
  return BOOT.strings[key] ? translate(key) : pageEpisode.questionTypeDisplayName;
}

// A delivered episode's real length; an episode not delivered yet counts with its estimate.
function resolveEpisodeDurationSeconds(planEpisode, pageEpisode) {
  return pageEpisode.isDelivered && pageEpisode.durationSeconds
    ? pageEpisode.durationSeconds : Number(planEpisode.estimated_duration_seconds) || 0;
}

function formatClockTime(seconds) {
  const wholeSeconds = Math.round(seconds);
  return `${Math.floor(wholeSeconds / 60)}:${String(wholeSeconds % 60).padStart(2, '0')}`;
}

function buildEpisodeCard(planEpisode, pageEpisode) {
  const outline = Array.isArray(planEpisode.outline) ? planEpisode.outline : [];
  const sideNode = buildElement('div', {class: 'ep-side'});
  const videoPageUrl = `${BOOT.baseUrl}/video/${planEpisode.id}`;
  if (pageEpisode.isDelivered) {
    sideNode.append(buildElement('span', {class: 'hb-chip green'}, translate('plan.episode.delivered')),
      buildElement('a', {class: 'hb-btn outline small', href: videoPageUrl}, translate('plan.episode.watch')));
  } else if (pageEpisode.isInProgress) {
    sideNode.append(buildElement('span', {class: 'hb-chip'}, translate('plan.episode.inProgress')));
  }
  const coverUrl = `${BOOT.baseUrl}/media/${planEpisode.id}/cover.png`
    + `?deliveredAt=${encodeURIComponent(pageEpisode.deliveredAt)}`;
  const coverLink = pageEpisode.hasCover
    ? buildElement('a', {class: 'ep-cover', href: videoPageUrl, title: translate('plan.episode.watch')},
      buildElement('img', {src: coverUrl, alt: '', loading: 'lazy',
        onerror: (event) => event.target.closest('.ep-cover').remove()}))
    : null;
  const estimatedMinutes = Math.round(resolveEpisodeDurationSeconds(planEpisode, pageEpisode) / 6) / 10;
  const lengthProperty = pageEpisode.isDelivered && pageEpisode.durationSeconds
    ? buildProperty(translate('plan.episode.videoLength'), buildText(formatClockTime(pageEpisode.durationSeconds)))
    : buildProperty(translate('plan.episode.length'),
      buildText(translate('plan.episode.minutes', {minutes: estimatedMinutes})));
  const presenterNode = buildElement('div', {class: 'static presenter'},
    buildElement('span', {}, pageEpisode.presenterDisplayName || '?'),
    pageEpisode.questionType
      ? buildElement('span', {class: 'hb-meta'}, buildElement('span', {class: 'hb-dot'}),
        translateQuestionTypeDisplayName(pageEpisode))
      : null,
    pageEpisode.doesUseDraftPlaybook
      ? buildElement('span', {class: 'hb-chip yellow'}, translate('plan.episode.draftPlaybook'))
      : null);
  const detailsNode = buildElement('details', {class: 'ep-details'},
    buildElement('summary', {}, buildChevronIcon(), buildElement('span', {}, translate('plan.episode.details'))),
    buildElement('div', {class: 'props'},
      buildProperty(translate('plan.episode.sourceScope'), buildText(planEpisode.source_scope)),
      buildProperty(translate('plan.episode.taughtTerms'), buildTermList(planEpisode.taught_terms)),
      buildProperty(translate('plan.episode.takeaway'), buildText(planEpisode.takeaway)),
      pageEpisode.narrationLabel
        ? buildProperty(translate('plan.episode.narration'), buildText(pageEpisode.narrationLabel), null,
          translate('plan.episode.narrationHint'))
        : null));
  const draftPlaybookHint = pageEpisode.doesUseDraftPlaybook
    ? translate('plan.episode.draftPlaybookHint',
      {presenter: pageEpisode.presenterDisplayName, questionType: translateQuestionTypeDisplayName(pageEpisode)})
    : null;
  return buildElement('section', {class: 'hb-card ep', id: `episode-${planEpisode.id}`},
    buildElement('div', {class: 'ep-head'},
      buildElement('span', {class: 'ep-number'}, String(planEpisode.id || '').toUpperCase()),
      buildElement('h3', {class: 'ep-title'}, planEpisode.title || ''),
      sideNode),
    buildElement('div', {class: 'ep-body'},
      buildElement('div', {class: 'props'},
        buildProperty(translate('plan.episode.question'), buildText(planEpisode.question)),
        buildProperty(translate('plan.episode.presenter'), presenterNode, null, draftPlaybookHint),
        lengthProperty),
      coverLink),
    // below the cover, so the outline gets the card's whole width
    buildElement('div', {class: 'props ep-outline'},
      buildProperty(translate('plan.episode.outline'), outline.length
        ? buildElement('ol', {class: 'static outline'}, outline.map((step) => buildElement('li', {}, step)))
        : buildText(null))),
    detailsNode);
}

function buildEpisodesSection(plan) {
  const episodes = Array.isArray(plan.episodes) ? plan.episodes : [];
  const totalMinutes = Math.round(episodes.reduce((sum, planEpisode, index) =>
    sum + resolveEpisodeDurationSeconds(planEpisode, pageData.episodes[index] || {}), 0) / 60);
  const summaryText = translate('plan.episodes.summary', {count: episodes.length, minutes: totalMinutes});
  return buildSection(translate('plan.episodes.heading'), summaryText,
    buildElement('div', {class: 'ep-list'},
      episodes.map((planEpisode, index) => buildEpisodeCard(planEpisode, pageData.episodes[index] || {}))));
}

function buildArrangementSection(plan) {
  const excludedTopics = Array.isArray(plan.excluded_topics) ? plan.excluded_topics : [];
  if (!plan.rationale && !excludedTopics.length) return [];
  return [buildSection(translate('plan.arrangement.heading'), null, buildElement('div', {class: 'hb-card props'},
    plan.rationale
      ? buildProperty(translate('plan.rationale.label'), buildElement('div', {class: 'static prose'},
        String(plan.rationale).trim().split(/\n\s*\n/).flatMap(buildParagraph)))
      : null,
    excludedTopics.length
      ? buildProperty(translate('plan.excluded.label'), buildElement('ul', {class: 'static bullets excluded-list'},
        excludedTopics.map((excludedTopic) => buildElement('li', {},
          buildElement('div', {}, excludedTopic.topic),
          buildElement('div', {class: 'hb-meta'}, excludedTopic.reason)))))
      : null))];
}

function showPage() {
  const appNode = document.getElementById('app');
  const scrollYPixels = window.scrollY;
  const plan = pageData.plan || {};
  document.title = `${plan.title || ''} · ${translate('plan.eyebrow')}`;
  const headNode = buildElement('div', {class: 'hb-head'},
    buildElement('div', {class: 'hb-eyebrow'}, translate('plan.eyebrow')),
    buildElement('h1', {class: 'hb-title'}, plan.title || ''),
    buildElement('p', {class: 'hb-lead'}, translate('plan.lead')));
  const nodes = [headNode, ...buildNotices()];
  if (!pageData.error) {
    nodes.push(buildSeriesSection(plan), buildProductionSection(plan), buildAudienceSection(plan),
      buildSection(translate('plan.goal.heading'), null, buildElement('div', {class: 'hb-card props'},
        buildProperty(translate('plan.goal.label'), buildText(plan.goal)))),
      buildEpisodesSection(plan), ...buildArrangementSection(plan));
  }
  appNode.replaceChildren(...nodes);
  window.scrollTo(0, scrollYPixels);
}

refreshPage().then(() => watchPageDigest('', () => pageDigest, refreshWhenIdle));
