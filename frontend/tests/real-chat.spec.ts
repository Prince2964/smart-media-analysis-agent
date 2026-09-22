import {test,expect} from '@playwright/test';
test('saved video answers through Foundry with citations',async({page,request})=>{
 test.skip(process.env.LIVE_AZURE_TEST !== '1','Set LIVE_AZURE_TEST=1 to run billable Azure integration checks');
 test.setTimeout(180000);
 const response=await request.get('http://127.0.0.1:8000/api/jobs/4772d654-3de6-4a13-9d5e-f1f7e16c21d4');
 test.skip(!response.ok(),'Saved live report required');
 const job=await response.json();
 await page.route('**/api/demo',r=>r.fulfill({json:job}));
 await page.goto('/');
 await page.getByRole('button',{name:'Start analyzing'}).click();
 await page.getByRole('button',{name:'Try video sample',exact:true}).click();
 await page.getByRole('button',{name:'Open report',exact:true}).click();
 await page.getByLabel('Your question').fill('What does the video say about ANC?');
 await page.getByRole('button',{name:'Ask',exact:true}).click();
 await expect(page.getByText('View supporting passages',{exact:true})).toBeVisible({timeout:140000});
 await page.getByText('View supporting passages',{exact:true}).click();
 await expect(page.locator('.citations button').first()).toBeVisible();
 await page.screenshot({path:'test-results/real-chat.png',fullPage:true});
});
