import {test,expect} from '@playwright/test';
test('continues checking video jobs after one minute',async({page})=>{
 await page.clock.install();let polls=0;
 await page.route('**/api/demo',r=>r.fulfill({json:{id:'slow-test',source_type:'video',source_name:'Slow test',status:'processing',stage:3,document:null}}));
 await page.route('**/api/jobs/slow-test',r=>{polls++;return r.fulfill({json:{id:'slow-test',source_type:'video',source_name:'Slow test',status:'processing',stage:3,document:null}});});
 await page.goto('/');await page.getByRole('button',{name:'Start analyzing'}).click();await page.getByRole('button',{name:'Try video sample',exact:true}).click();
 await page.clock.fastForward(65000);await expect.poll(()=>polls).toBeGreaterThan(0);
 const previous=polls;await page.clock.fastForward(3000);await expect.poll(()=>polls).toBeGreaterThan(previous);
 await expect(page.getByRole('button',{name:'Check status again'})).toHaveCount(0);
});
