import {test,expect} from '@playwright/test';

for(const viewport of [{width:1280,height:720},{width:390,height:700}]){
 test(`multiple questions keep composer accessible at ${viewport.width}px`,async({page})=>{
  await page.setViewportSize(viewport);
  const segment={id:'p1',label:'Product details',text:'Supporting passage. '.repeat(150),start:12,end:20,region:null};
  const document={id:'scroll-test',source_type:'video',source_name:'Panel test',sample_name:'',summary:'Test report',topics:['Product'],extracted_text:'',segments:[segment],chunks:[segment],visual_information:[],metadata:{},is_mock:false};
  await page.route('**/api/demo',r=>r.fulfill({json:{id:document.id,source_type:'video',source_name:document.source_name,status:'complete',stage:4,document}}));
  await page.route('**/api/jobs/scroll-test/questions',r=>{const body=r.request().postDataJSON();expect(body.history.length).toBeLessThanOrEqual(4);return r.fulfill({json:{...(body.allow_web?{web_answer:'External information [Source](https://example.com/specs)',web_sources:[{url:'https://example.com/specs',title:'Product specifications'}]}:{}),answer:'A detailed answer about the media. '.repeat(30),citations:[segment],retrieved_context:[segment],answer_kind:'grounded_answer',notice:''}});});
  await page.goto('/');await page.getByRole('button',{name:'Start analyzing'}).click();
  await page.getByRole('button',{name:'Try video sample',exact:true}).click();await page.getByRole('button',{name:'Open report',exact:true}).click();
  const panel=page.getByRole('complementary',{name:'Media questions'});
  await panel.scrollIntoViewIfNeeded();
  for(let i=0;i<3;i++){
   if(i===2)await page.getByLabel('Search the web if media has no answer').check();
   await page.getByLabel('Your question').fill(`Question ${i}`);
   const ask=page.getByRole('button',{name:'Ask',exact:true});
   await expect(ask).toBeInViewport();await ask.click();
   await expect(panel.locator('.exchange')).toHaveCount(i+1);
   await expect(ask).toBeInViewport();
  }
  await expect(panel.getByText('FROM THE WEB · NOT VIDEO EVIDENCE')).toBeVisible();
  await expect(panel.getByRole('link',{name:'Product specifications'})).toHaveAttribute('href','https://example.com/specs');
  const history=page.getByRole('region',{name:'Question and answer history'});
  expect(await history.evaluate(el=>el.scrollHeight>el.clientHeight)).toBe(true);
  await history.hover();await page.mouse.wheel(0,-10000);
  await expect.poll(()=>history.evaluate(el=>el.scrollTop)).toBe(0);
  await panel.getByText('View supporting passages').first().click();
  await expect(page.getByRole('button',{name:'Ask',exact:true})).toBeInViewport();
  await panel.screenshot({path:`test-results/chat-panel-${viewport.width}.png`});
 });
}
