import {test,expect} from '@playwright/test';
test('report refresh updates passages and displays errors',async({page})=>{
 const doc={id:'refresh-test',source_type:'image',source_name:'test.png',sample_name:'test',summary:'Initial summary',topics:['Test'],segments:[{id:'s',label:'Original',text:'Old text',start:null,end:null,region:'Image'}],metadata:{notice:'Test'},is_mock:false};
 const job={id:doc.id,source_type:'image',source_name:'test',status:'complete',stage:4,document:doc};
 await page.route('**/api/demo',r=>r.fulfill({json:job}));
 await page.goto('/');await page.getByRole('button',{name:'Start analyzing'}).click();await page.getByRole('button',{name:'Try video sample',exact:true}).click();await page.getByRole('button',{name:'Open report',exact:true}).click();
 await page.route('**/api/jobs/refresh-test',r=>r.fulfill({json:{...job,document:{...doc,summary:'Updated summary',segments:[{...doc.segments[0],text:'New passage'}]}}}));
 await page.getByRole('button',{name:'Refresh report',exact:true}).click();
 await expect(page.getByText('Updated summary',{exact:true})).toBeVisible();await expect(page.getByText('New passage',{exact:true})).toBeVisible();await expect(page.getByRole('status').filter({hasText:'Report refreshed'})).toBeVisible();
 await page.route('**/api/jobs/refresh-test',r=>r.fulfill({status:404,json:{detail:'Job not found. The local server may have restarted.'}}));
 await page.getByRole('button',{name:'Refresh report',exact:true}).click();await expect(page.getByRole('alert')).toContainText('Job not found');await expect(page.getByText('Updated summary',{exact:true})).toBeVisible();
});
