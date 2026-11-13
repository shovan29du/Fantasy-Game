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
  check((await page.locator('.help-entry h3').allTextContents()).includes('Fireball'), 'Help search finds a spell');
  await page.locator('#helpSearch').fill('zzzz-no-such-thing');
  check(await page.locator('.help-entry').count() === 0, 'Help search reports no matches');
  await page.locator('.side-nav button', { hasText: 'Play' }).click();
  check((await layout()).game, 'Play returns from Help to the game');

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
