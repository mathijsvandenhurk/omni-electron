// Check if localStorage has command history
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  // Navigate to app
  await page.goto('http://localhost:5173');
  
  // Check localStorage
  const history = await page.evaluate(() => {
    return localStorage.getItem('omni-command-history');
  });
  
  console.log('Command History:', history);
  
  await browser.close();
})();
