const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  const page = await context.newPage();
  
  console.log('Navigating to https://share.streamlit.io...');
  await page.goto('https://share.streamlit.io');
  
  // Wait a bit for redirects
  await page.waitForTimeout(5000);
  
  const url = page.url();
  console.log('Current URL:', url);
  
  await page.screenshot({ path: 'streamlit_login_check.png' });
  
  if (url.includes('login') || page.url().includes('github.com/login')) {
    console.log('Status: NOT_LOGGED_IN');
  } else {
    console.log('Status: LOGGED_IN');
  }
  
  await browser.close();
})();
