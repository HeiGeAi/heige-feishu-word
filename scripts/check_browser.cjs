/* Optional visual QA: PLAYWRIGHT_MODULE can point at a bundled installation. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const fs=require('node:fs/promises');
const path=require('node:path');
const {pathToFileURL}=require('node:url');

(async()=>{
 const gallery=path.resolve(process.argv[2]||'build/gallery');
 const output=path.resolve(process.argv[3]||'build/browser-evidence');
 await fs.mkdir(output,{recursive:true});
 const browser=await chromium.launch({headless:true});
 const page=await browser.newPage();
 const errors=[];page.on('pageerror',e=>errors.push(e.message));
 page.on('console',message=>{if(message.type()==='error')errors.push(message.text());});
 page.on('requestfailed',r=>errors.push(r.url()+': '+r.failure().errorText));
 const slugs=['executive-brief','operating-review','project-pulse','research-digest','decision-memo','launch-story'];
 const reports=[];
 try {
  for(const slug of ['index',...slugs]){
   for(const width of [1440,390]){
    await page.setViewportSize({width,height:1000});
    const filename=slug==='index'?path.join(gallery,'index.html'):path.join(gallery,slug,'preview.html');
    const previous=errors.length;
    await page.goto(pathToFileURL(filename).href);
    await page.waitForLoadState('load');
    await page.evaluate(()=>Promise.all(document.getAnimations().filter(a=>a.effect.getTiming().iterations!==Infinity).map(a=>a.finished.catch(()=>{}))));
    const geometry=await page.evaluate(()=>({
     viewport:innerWidth,document:document.documentElement.scrollWidth,
     missingImages:[...document.images].filter(i=>!i.complete||i.naturalWidth===0).map(i=>i.src),
     svgCount:document.querySelectorAll('svg').length,
     textOverflow:[...document.querySelectorAll('svg text')].flatMap(n=>{
      const b=n.getBBox(),v=n.ownerSVGElement.viewBox.baseVal;
      return b.x< -2||b.y< -2||b.x+b.width>v.width+2||b.y+b.height>v.height+2?[{text:n.textContent,x:b.x,y:b.y,w:b.width,h:b.height}]:[];
     })
    }));
    await page.screenshot({path:path.join(output,slug+'-'+width+'.png'),fullPage:width===390});
    reports.push({slug,width,...geometry,errors:errors.slice(previous)});
   }
  }
  for(const width of [1440,390]){
  await page.setViewportSize({width,height:1000});
  await page.goto(pathToFileURL(path.join(gallery,'operating-review','preview.html')).href);
  const details=page.locator('details').first();
  if(await details.count()){
   await details.locator('summary').click();
   reports.push({interaction:'data disclosure',pass:await details.getAttribute('open')!==null});
  }
  const svgTrigger=page.locator('.diagram-open').first();
  await svgTrigger.click();
  const dialog=page.locator('#figure-dialog');
  reports.push({interaction:'open SVG dialog',pass:await dialog.isVisible()});
  reports.push({interaction:'dialog controls fit',width,pass:await dialog.locator('.dialog-controls').evaluate(n=>n.scrollWidth<=n.clientWidth)});
  const before=await dialog.locator('.dialog-art').evaluate(n=>n.getBoundingClientRect().width);
  await dialog.locator('[data-enlarge]').click();
  const enlarged=await dialog.locator('.dialog-art').evaluate(n=>n.getBoundingClientRect().width);
  reports.push({interaction:'enlarge SVG',pass:enlarged>before});
  await dialog.locator('[data-fit]').click();
  reports.push({interaction:'fit SVG',pass:await dialog.locator('.dialog-art').evaluate(n=>n.getBoundingClientRect().width)===before});
  await dialog.locator('[data-close]').click();
  reports.push({interaction:'close SVG dialog',pass:!await dialog.isVisible()});
  await svgTrigger.click();
  await page.keyboard.press('Escape');
  reports.push({interaction:'Escape closes SVG dialog',pass:!await dialog.isVisible()});
  }
  await page.emulateMedia({reducedMotion:'reduce'});
  await page.goto(pathToFileURL(path.join(gallery,'launch-story','preview.html')).href);
  reports.push({interaction:'reduced motion disables animation',pass:await page.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches&&document.getAnimations().length===0)});
  reports.push({interaction:'no console or network errors',pass:errors.length===0,errors});
  await fs.writeFile(path.join(output,'checks.json'),JSON.stringify(reports,null,2));
  const failures=reports.filter(r=>r.pass===false || (r.viewport && (r.document>r.viewport||r.errors.length||r.missingImages.length||r.textOverflow.length)));
  console.log(JSON.stringify({reports:reports.length,failures},null,2));
  if(failures.length)process.exitCode=1;
 } finally {await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
