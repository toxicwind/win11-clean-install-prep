import { firefox } from 'playwright';
try {
  const browser = await firefox.connectOverCDP('http://127.0.0.1:9222');
  const ctxs = browser.contexts();
  console.log('connected, contexts:', ctxs.length);
  for (const c of ctxs) {
    for (const p of c.pages()) {
      console.log('PAGE:', p.url(), '|', await p.title());
    }
  }
  await browser.close();
} catch (e) {
  console.log('ERR:', e.message);
}