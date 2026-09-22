import {test,expect} from '@playwright/test';
test('local library searches and opens a persisted report',async({page})=>{
 const doc={id:'saved-test',source_type:'video',source_name:'Saved clip.mp4',summary:'Saved concise summary.',topics:['Audio'],segments:[],chunks:[],metadata:{},is_mock:false};
 await page.route('**/api/reports',r=>r.fulfill({json:{scope:'local-shared',reports:[doc]}}));
 await page.route('**/api/jobs/saved-test',r=>r.fulfill({json:{id:doc.id,status:'complete',document:doc}}));
 await page.goto('/');await page.getByRole('button',{name:'Report library',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Local report library'})).toBeVisible();
 await page.getByLabel('Find a report by filename or topic').fill('missing');
 await expect(page.getByText('No matching reports.')).toBeVisible();
 await page.getByLabel('Find a report by filename or topic').fill('Audio');
 await page.getByRole('button',{name:'Open report',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Saved clip.mp4'})).toBeVisible();
 await expect(page.getByText('Saved concise summary.')).toBeVisible();
 await expect(page.getByText(/original media preview is not loaded/)).toBeVisible();
});
