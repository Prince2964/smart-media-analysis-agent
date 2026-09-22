import {test,expect} from '@playwright/test';
test('sample video: report, citations, unknown answer, search and timestamp',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Start analyzing'}).click();
 await page.getByRole('button',{name:'Try video sample',exact:true}).click();
 await page.getByRole('button',{name:'Open report',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Product briefing video',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'When did they discuss pricing?',exact:true}).click();
 await page.getByRole('button',{name:'Ask',exact:true}).click();
 await expect(page.getByText('The pricing discussion starts at approximately 01:32.',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'01:32 · Pricing & plans',exact:true}).click();
 await expect(page.getByRole('slider')).toHaveValue('92');
 await page.getByRole('button',{name:'What salary was discussed?',exact:true}).click();await page.getByRole('button',{name:'Ask',exact:true}).click();
 await expect(page.getByText("I can't determine that from the provided media.",{exact:true})).toBeVisible();
 await page.getByLabel("Search this sample's passages").fill('salary');await page.getByRole('button',{name:'Search',exact:true}).click();
 await expect(page.getByText('No matching passages in this sample. Try another keyword.')).toBeVisible();
 await page.screenshot({path:'test-results/desktop-report.png',fullPage:true});
});
test('image, unsupported link and retry states',async({page})=>{
 await page.goto('/');await page.getByRole('button',{name:'Start analyzing'}).click();
 await page.getByRole('button',{name:/Upload Image Explore/}).click();await page.getByRole('button',{name:'Try image sample',exact:true}).click();await page.getByRole('button',{name:'Open report',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Important Elements',exact:true})).toBeVisible();await expect(page.getByRole('slider')).toHaveCount(0);
 await page.getByRole('button',{name:'What port is shown?',exact:true}).click();await page.getByRole('button',{name:'Ask',exact:true}).click();await expect(page.getByText('The sample diagram shows port 443 HTTPS.',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Analyze another',exact:true}).click();await page.getByRole('button',{name:/Paste Link Bring/}).click();await page.getByLabel('Media URL').fill('http://127.0.0.1/private');await page.getByRole('button',{name:'Analyze link',exact:true}).click();await expect(page.getByRole('alert')).toContainText('Unsupported link');
 await page.getByText('Demonstration controls',{exact:true}).click();await page.getByRole('button',{name:'Simulate processing failure'}).click();await expect(page.getByRole('heading',{name:'Unable to prepare the sample'})).toBeVisible();await page.getByRole('button',{name:'Retry with sample'}).click();await expect(page.getByRole('button',{name:'Open report',exact:true})).toBeVisible();
});
test('mobile layout has no horizontal overflow',async({page})=>{
 await page.setViewportSize({width:390,height:844});await page.goto('/');await page.getByRole('button',{name:'Start analyzing'}).click();await page.screenshot({path:'test-results/mobile-upload.png',fullPage:true});
 await page.getByRole('button',{name:'Try video sample',exact:true}).click();await page.getByRole('button',{name:'Open report',exact:true}).click();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();await page.screenshot({path:'test-results/mobile-report.png',fullPage:true});
});
