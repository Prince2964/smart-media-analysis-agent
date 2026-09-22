import {test,expect} from '@playwright/test';
test('compact real report with topics and Hinglish',async({page,request})=>{
 const response=await request.get('http://127.0.0.1:8000/api/jobs/4772d654-3de6-4a13-9d5e-f1f7e16c21d4');
 test.skip(!response.ok(),'Saved report not available');const job=await response.json();
 await page.route('**/api/demo',r=>r.fulfill({json:job}));
 await page.goto('/');await page.getByRole('button',{name:'Start analyzing'}).click();await page.getByRole('button',{name:'Try video sample',exact:true}).click();await page.getByRole('button',{name:'Open report',exact:true}).click();
 await expect(page.getByText('ANC on base variant',{exact:true})).toBeVisible();
 await page.getByText('Transcript · Hinglish',{exact:true}).first().click();
 await expect(page.getByText('Separate topic extraction is not available from this analyzer.')).toHaveCount(0);
 await page.screenshot({path:'test-results/compact-report.png',fullPage:true});
});
