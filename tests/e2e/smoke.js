// Browser smoke test. Run through tests/test_e2e_smoke.py, or by hand with
// APP_URL and LM_URL pointing at a running app and fake_lm_studio.py.
const { chromium } = require('playwright');

const APP = process.env.APP_URL || 'http://127.0.0.1:8501';
const LM = process.env.LM_URL || 'http://127.0.0.1:1234';
const problems = [];
const check = (ok, label) => { console.log((ok ? 'ok   ' : 'FAIL ') + label); if (!ok) problems.push(label); };

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1400, height: 900 } });
  const page = await context.newPage();
  const pageErrors = [];
  let allowFailures = false;
  page.on('pageerror', e => pageErrors.push('pageerror: ' + e.message));
  page.on('response', r => { if (r.status() >= 400 && r.url().startsWith(APP) && !allowFailures) pageErrors.push(`HTTP ${r.status()} ${r.url().slice(APP.length)}`); });
  const dialogs = [];
  page.on('dialog', d => { dialogs.push(d.message()); d.accept(); });
  context.on('page', () => pageErrors.push('a new tab was opened'));
  // Keep the run offline: nothing outside the app under test.
  await page.route(url => !url.href.startsWith(APP), route => route.abort());
  // Help pictures are generated on demand and need an image service; this run is offline.
  await page.route('**/api/help/picture', route => route.abort());

  const layout = () => page.evaluate(() => ({
    game: !document.querySelector('#gameArea').hidden,
    hub: !document.querySelector('#playHub').hidden,
    sidebar: getComputedStyle(document.querySelector('.app-sidebar')).display !== 'none',
  }));
  const visible = sel => page.locator(sel).first().isVisible();
  const setLmFailing = fail => page.request.post(LM + '/__fail', { data: { fail } });

  // --- start a new game, in the same tab
  await page.goto(APP);
  await page.waitForLoadState('networkidle');
  await page.locator('.side-nav button', { hasText: 'Play' }).click();
  await page.locator('button', { hasText: 'New Game' }).first().click();
  await page.locator('#playHub button', { hasText: '▶ Play' }).first().click();
  await page.locator('#playerCharForm input[name=charName]').fill('Smoke Tester');
  await page.locator('#playerCharForm input[name=charProfession]').fill('Ranger');
  await page.locator('button', { hasText: 'Start Adventure' }).click();
  await page.waitForFunction(() => !document.querySelector('#gameArea').hidden && document.querySelector('#partyCount')?.textContent.trim().startsWith('1'), null, { timeout: 30000 });
  let l = await layout();
  check(l.game && !l.hub, 'game opens in the same tab');
  check(!l.sidebar, 'sidebar is hidden during play');
  check((await page.locator('#partyCount').textContent()).trim() === '1 / 6', 'party has only the new character');
  check((await page.locator('#partyList').textContent()).includes('Smoke Tester'), 'party shows the new character');

  // --- the Character panel shows the selected character
  const panelName = () => page.locator('#detailContent .character-hero h2').textContent();
  check((await panelName()) === 'Smoke Tester', "the Character panel shows the story's character");
  const companion = await (await page.request.post(`${APP}/api/characters`, { data: { name: 'Kael Companion', profession: 'Fighter' } })).json();
  // a newer saved character exists: after a reload the panel must still show this story's character
  await page.reload();
  await page.waitForFunction(() => !document.querySelector('#gameArea').hidden && document.querySelector('#partyCount')?.textContent.trim().startsWith('1'), null, { timeout: 30000 });
  await page.waitForTimeout(500);
  check((await panelName()) === 'Smoke Tester', 'the panel is not replaced by the newest saved character');
  check((await page.locator('#partyList').textContent()).includes('Smoke Tester'), 'the party bar and the panel agree');

  await page.locator('.add-member').click();
  await page.locator(`[data-recruit-id="${companion.id}"]`).click();
  await page.keyboard.press('Escape');
  await page.locator('#partyList .party-card', { hasText: 'Kael Companion' }).click();
  await page.waitForFunction(() => document.querySelector('#detailContent .character-hero h2')?.textContent === 'Kael Companion', null, { timeout: 8000 });
  check(true, 'selecting a party member shows their sheet');
  check(await page.locator('#detailContent .panel-note').count() === 1, 'the panel says whose sheet it is showing');
  check(await page.locator('#detailContent button', { hasText: 'Level Up' }).count() === 0, "a companion's sheet cannot be levelled from here");
  await page.locator('#partyList .party-card', { hasText: 'Kael Companion' }).click();
  await page.waitForFunction(() => document.querySelector('#detailContent .character-hero h2')?.textContent === 'Smoke Tester', null, { timeout: 8000 });
  check(await page.locator('#detailContent button', { hasText: 'Level Up' }).count() === 1, 'deselecting returns to your own sheet');

  // --- the selected party member's name shows in the chat
  await page.locator('#partyList .party-card', { hasText: 'Kael Companion' }).click();
  await page.locator('#chatLog .chat-note', { hasText: 'Now speaking as Kael Companion' }).waitFor({ timeout: 8000 });
  check(true, 'selecting a party member adds a note to the chat');
  await page.locator('#chatInput').fill('I take first watch.');
  await page.locator('#chatForm button', { hasText: /^Send$/ }).click();
  await page.waitForFunction(() => document.querySelector('#chatLog .chat-msg.gm:last-child')?.textContent.includes('sealed scroll'), null, { timeout: 20000 });
  const labels = await page.evaluate(() => {
    const lastPlayer = [...document.querySelectorAll('#chatLog .chat-msg.player')].pop();
    const lastReply = [...document.querySelectorAll('#chatLog .chat-msg.gm')].pop();
    return [lastPlayer?.querySelector('b')?.textContent, lastReply?.querySelector('b')?.textContent];
  });
  check(labels[0] === 'Kael Companion', 'your message is labelled with the selected member, not YOU');
  check(labels[1] === 'Kael Companion', 'the reply is labelled with the selected member');
  await page.locator('#partyList .party-card', { hasText: 'Kael Companion' }).click();
  await page.waitForFunction(() => document.querySelector('#chatLog .chat-note:last-child')?.textContent.includes('Back to the narrator'), null, { timeout: 8000 });
  check(true, 'releasing the member says so in the chat');

  // --- menu toggle and Escape
  await page.locator('#sidebarToggleBtn').click();
  check((await layout()).sidebar, 'Menu button shows the sidebar');
  await page.keyboard.press('Escape');
  check(!(await layout()).sidebar, 'Escape hides the sidebar again');

  // --- map tabs stay inside their column
  await page.locator('.map-tabs button', { hasText: 'Universe' }).click();
  check(await page.evaluate(() => document.querySelector('.map-column').scrollLeft === 0), 'map column does not shift when switching tabs');
  await page.locator('.map-tabs button', { hasText: 'Local' }).click();

  // --- chat
  const send = async text => { await page.locator('#chatInput').fill(text); await page.locator('#chatForm button', { hasText: /^Send$/ }).click(); };
  await send('I climb to the rooftop.');
  await page.waitForFunction(() => document.querySelector('#chatLog').textContent.includes('sealed scroll'), null, { timeout: 20000 });
  const connected = await page.waitForFunction(() => document.querySelector('#aiStatus').textContent === 'LM Studio connected', null, { timeout: 10000 }).then(() => true, () => false);
  check(connected, 'status shows connected after a reply');

  // --- failed reply: friendly message, Retry, no duplicate player line
  allowFailures = true;
  await setLmFailing(true);
  await send('I open the scroll.');
  await page.locator('.llm-retry').waitFor({ timeout: 20000 });
  const errorText = await page.locator('.llm-error').first().textContent();
  check(!/HTTPConnectionPool|Traceback|Expecting value/.test(errorText), 'error message is plain language');
  check((await page.locator('#aiStatus').textContent()) === 'Start LM Studio on port 1234', 'status reports the failure');
  await setLmFailing(false);
  allowFailures = false;
  await page.locator('.llm-retry').click();
  await page.waitForFunction(() => !document.querySelector('.llm-retry') && [...document.querySelectorAll('#chatLog .chat-msg.gm')].pop()?.textContent.includes('sealed scroll'), null, { timeout: 20000 });
  check(await page.evaluate(() => [...document.querySelectorAll('#chatLog .chat-msg.player')].filter(m => m.textContent.includes('I open the scroll.')).length === 1), 'Retry does not repeat the player message');

  // --- quest generation
  await page.locator('#genQuestBtn').click();
  await page.waitForFunction(() => document.querySelector('#gameArea').textContent.includes('The Sealed Scroll'), null, { timeout: 20000 });
  check(true, 'generated quest appears');

  // --- dialogs close with Escape
  await page.locator('.add-member').click();
  await page.locator('#recruitModal').waitFor({ state: 'visible' });
  await page.keyboard.press('Escape');
  check(!(await visible('#recruitModal')), 'Escape closes the Recruit dialog');
  await page.locator('#saveBtn').click();
  if (await visible('#saveLoadModal')) { await page.keyboard.press('Escape'); check(!(await visible('#saveLoadModal')), 'Escape closes the Save dialog'); }

  // --- zip export
  const zip = await page.request.get(`${APP}/api/chat/export/zip?session_id=default`);
  check(zip.status() === 200 && (zip.headers()['content-type'] || '').includes('zip'), 'zip export downloads');

  // --- hub and back
  await page.locator('#gameCloseBtn').click();
  l = await layout();
  check(l.hub && l.sidebar, 'Close returns to the hub with the sidebar');
  await page.locator('#hubCloseBtn').click();
  l = await layout();
  check(l.game && !l.sidebar, '"Back to game" resumes the game');

  // --- other views stay reachable mid-game
  await page.locator('#sidebarToggleBtn').click();
  await page.locator('.side-nav button', { hasText: 'Characters' }).click();
  check((await layout()).sidebar && await visible('#view-characters'), 'Characters view is reachable from a running game');
  await page.locator('.side-nav button', { hasText: 'Play' }).click();
  l = await layout();
  check(l.game && !l.sidebar, 'Play returns to the running game');

  // --- help
  await page.locator('#gameHelpBtn').click();
  await page.locator('.help-section').first().waitFor({ timeout: 10000 });
  check(await visible('#view-help') && (await layout()).sidebar, 'Help opens from a running game');
  check(await page.locator('.help-section').count() >= 15, 'Help lists its topics');
  await page.locator('#helpSearch').fill('fireball');
  check((await page.locator('.help-entry h3').allTextContents()).some(t => t.includes('Fireball')), 'Help search finds a spell');
  await page.locator('#helpSearch').fill('zzzz-no-such-thing');
  check(await page.locator('.help-entry').count() === 0, 'Help search reports no matches');
  await page.locator('.side-nav button', { hasText: 'Play' }).click();
  check((await layout()).game, 'Play returns from Help to the game');

  // --- journal
  const drawerOpen = () => page.evaluate(() => !document.querySelector('#journalDrawer').hidden);
  const tab = async name => { await page.locator(`#journalTabs [data-jtab="${name}"]`).click(); await page.waitForTimeout(250); };
  await page.locator('#journalBtn').click();
  check(await drawerOpen(), 'Journal opens from the top bar');
  check(await page.locator('#journalTabs button').count() === 5, 'Journal has five tabs');

  // quests
  await page.locator('.jcard', { hasText: 'The Sealed Scroll' }).waitFor({ timeout: 10000 });
  await page.locator('[data-jact="q-progress"]').first().click();
  await page.waitForFunction(() => document.querySelector('.jcard .jprogress')?.title === '25% complete', null, { timeout: 5000 });
  check(true, 'quest progress can be advanced from the Journal');

  // notes
  await tab('notes');
  await page.locator('[data-jform="note"] [name=title]').fill('Smuggler cove');
  await page.locator('[data-jform="note"] [name=body]').fill('Meet Corvin at midnight by the old pier');
  await page.locator('[data-jform="note"] [name=tags]').fill('clue, Corvin');
  await page.locator('[data-jform="note"] button.gold').click();
  await page.locator('.jcard', { hasText: 'Smuggler cove' }).waitFor();
  check(await page.locator('.jtag', { hasText: '#corvin' }).count() === 1, 'a note is saved with tags');
  await page.locator('[data-jact="note-pin"]').first().click();
  await page.locator('.jcard-pinned', { hasText: 'Smuggler cove' }).waitFor();
  check(true, 'a note can be pinned');
  await page.locator('#journalSearch').fill('zzz-nothing');
  await page.waitForFunction(() => document.querySelector('#journalBody .journal-empty'), null, { timeout: 5000 });
  await page.locator('#journalSearch').fill('midnight');
  await page.locator('.jcard', { hasText: 'Smuggler cove' }).waitFor();
  check(true, 'notes can be searched');
  await page.locator('#journalSearch').fill('');
  await page.locator('[data-jact="recap"]').click();
  await page.locator('.jchip', { hasText: 'recap' }).first().waitFor({ timeout: 20000 });
  check(true, 'a recap of the story is written into the notes');

  // memory
  await tab('memory');
  await page.locator('[data-jform="memory"] [name=fact]').fill('Marta owes the player a favour');
  await page.locator('[data-jform="memory"] [name=pinned]').check();
  await page.locator('[data-jform="memory"] button.gold').click();
  await page.locator('.jmem', { hasText: 'Marta owes' }).waitFor();
  check(await page.locator('.jmem.jcard-pinned .jstar.on').count() === 1, 'a pinned memory is saved');
  await page.locator('[data-jpreview]').fill('I ask Marta about the favour');
  await page.locator('[data-jact="mem-preview"]').click();
  await page.waitForFunction(() => document.querySelector('.jpreview')?.textContent.includes('Marta owes'), null, { timeout: 5000 });
  check(true, 'the preview shows what the storyteller will recall');
  await page.locator('[data-jact="mem-edit"]').first().click();
  await page.locator('[data-jform="memory"][data-id] [name=fact]').fill('Marta forgave the player');
  await page.locator('[data-jform="memory"][data-id] button.gold').click();
  await page.locator('.jmem', { hasText: 'Marta forgave' }).waitFor();
  check(true, 'a memory can be edited');
  await page.locator('[data-jact="mem-delete"]').first().click();
  await page.waitForFunction(() => ![...document.querySelectorAll('.jmem')].some(m => m.textContent.includes('Marta forgave')), null, { timeout: 5000 });
  check(true, 'a memory can be forgotten');

  // people
  await tab('people');
  const personCard = page.locator('#journalBody .jcard').first();
  await personCard.waitFor({ timeout: 10000 });
  await personCard.locator('[name=fact]').fill('Speaks in riddles');
  await personCard.locator('button').click();
  await page.locator('.jlist li', { hasText: 'Speaks in riddles' }).waitFor();
  check(true, 'people show trust and what you know about them');

  // Escape and the J key
  await page.keyboard.press('Escape');
  check(!(await drawerOpen()), 'Escape closes the Journal');
  await page.locator('#chatInput').blur();
  await page.keyboard.press('j');
  check(await drawerOpen(), 'the J key opens the Journal');
  await page.keyboard.press('j');

  // key moments, from a message saved in the history
  await page.reload();
  await page.waitForFunction(() => !document.querySelector('#gameArea').hidden && document.querySelector('#chatLog .chat-msg.gm[data-mid]'), null, { timeout: 30000 });
  await page.evaluate(() => document.querySelector('#chatLog .chat-msg.gm[data-mid] [data-act="moment"]').click());
  await page.waitForFunction(() => document.querySelector('#chatLog .ma-on'), null, { timeout: 5000 });
  await page.locator('#journalBtn').click();
  await tab('moments');
  await page.locator('#journalBody .jcard').first().waitFor();
  check(true, 'a starred message appears under Moments');
  await page.locator('[data-jact="moment-unstar"]').first().click();
  await page.waitForFunction(() => document.querySelector('#journalBody .journal-empty'), null, { timeout: 5000 });
  check(true, 'a moment can be removed');
  await page.keyboard.press('Escape');

  // --- a second story with the same character name gets its own character
  const namesakes = async () => (await (await page.request.get(`${APP}/api/characters`)).json()).filter(c => c.name === 'Smoke Tester');
  const firstId = (await namesakes())[0].id;
  dialogs.length = 0;
  await page.locator('#gameBackBtn').click();
  await page.locator('#playHub button', { hasText: '▶ Play' }).nth(1).click();
  await page.locator('#playerCharForm input[name=charName]').fill('Smoke Tester');
  await page.locator('button', { hasText: 'Start Adventure' }).click();
  await page.waitForFunction(() => !document.querySelector('#gameArea').hidden && document.querySelector('#partyCount')?.textContent.trim().startsWith('1') && !document.querySelector('#chatLog').textContent.includes('I climb to the rooftop.'), null, { timeout: 30000 });
  const twins = await namesakes();
  check(dialogs.length === 0, 'reusing a name does not prompt');
  check(twins.length === 2, 'the second story creates its own character');
  const secondId = Math.max(...twins.map(c => c.id));
  const questsOf = async id => (await (await page.request.get(`${APP}/api/quests/active?character_name=Smoke%20Tester&character_id=${id}`)).json()).length;
  check(await questsOf(firstId) === 1 && await questsOf(secondId) === 0, 'quests stay with the first story\'s character');
  check(!(await page.locator('#gameArea').textContent()).includes('The Sealed Scroll'), 'the new story starts without the old quest');

  // --- combat
  await page.locator('#gameArea button', { hasText: 'Engage Enemies' }).click();
  await page.locator('.combat-overlay.open').waitFor({ timeout: 20000 });
  check(await visible('#combatEndTurnBtn'), 'tactical combat opens');

  for (const e of pageErrors) check(false, e);
  await browser.close();
  if (problems.length) { console.log(`\n${problems.length} problem(s)`); process.exit(1); }
  console.log('\nall checks passed');
})().catch(e => { console.error(e); process.exit(1); });
