import {test,expect} from '@playwright/test';
test('live video report and timestamp seeking',async({page})=>{
 test.skip(process.env.LIVE_AZURE_TEST!=='1','Explicit Azure test only');
 test.setTimeout(180000);
 await page.goto('/');await page.getByRole('button',{name:'Start analyzing'}).click();
 await page.getByLabel('Upload video file').setInputFiles('../.local/test-video.mp4');
 await page.getByRole('button',{name:'Analyze video',exact:true}).click();
 await page.getByRole('button',{name:'Open report',exact:true}).click({timeout:150000});
 await expect(page.getByText('Real analysis',{exact:true})).toBeVisible();
 await expect(page.locator('video')).toBeVisible();
 const stamp=page.locator('.passage .timestamp').first();await stamp.click();
 expect(await page.locator('video').evaluate((el:HTMLVideoElement)=>el.currentTime)).toBeGreaterThan(0);
 await page.screenshot({path:'test-results/live-video.png',fullPage:true});
});
