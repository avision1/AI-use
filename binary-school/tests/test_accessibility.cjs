// Structural and focus-flow regressions; not a substitute for live assistive-technology QA.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const site=path.join(__dirname,'..','site');let src=fs.readFileSync(path.join(site,'app.js'),'utf8');src=src.slice(0,src.lastIndexOf("fetch('curriculum.json')"));
let nodes={},focuses=[],mobile=false,scrolls=0;const make=(name,natural=false)=>({value:'',innerHTML:'',textContent:'',open:true,dataset:{},attrs:{},style:{},matches:()=>natural,setAttribute(k,v){this.attrs[k]=v},getAttribute(k){return this.attrs[k]},removeAttribute(k){delete this.attrs[k]},focus(options){focuses.push({name,options})},classList:{toggle(){}}});
const nav=[make('home-link',true),make('paths-link',true)];nav[0].dataset.nav='home';nav[1].dataset.nav='paths';
const ctx={location:{hash:'#home'},window:{addEventListener(){},scrollTo(){scrolls++},matchMedia:()=>({matches:mobile})},localStorage:{getItem:()=>null,setItem(){}},document:{querySelector:key=>nodes[key]??(nodes[key]=make(key)),querySelectorAll:key=>key==='[data-nav]'?nav:[]},setTimeout:()=>0};
vm.createContext(ctx);vm.runInContext(src,ctx);const db=JSON.parse(fs.readFileSync(path.join(site,'curriculum.json'),'utf8'));vm.runInContext('db='+JSON.stringify(db),ctx);
const run=s=>vm.runInContext(s,ctx);
const html=fs.readFileSync(path.join(site,'index.html'),'utf8');assert(html.includes('id="skipcontent"'));assert(html.includes('<main id="main-content" tabindex="-1">'));
let prevented=false;nodes['#skipcontent'].onclick({preventDefault(){prevented=true}});assert(prevented);assert.equal(ctx.location.hash,'#home');assert.equal(focuses.at(-1).name,'#main-content');assert.equal(focuses.at(-1).options.preventScroll,false);
ctx.document.activeElement=nodes['#skipcontent'];
const heading=nodes['#app h1']=make('#app h1');heading.textContent=' Learn what’s underneath. ';
const beforeStartup=focuses.length;run('render()');
assert.equal(ctx.document.title,'Learn what’s underneath. | Binary School');
assert.equal(focuses.length,beforeStartup);assert.equal(scrolls,0);
ctx.document.body=make('body');ctx.document.activeElement=ctx.document.body;
run('lastRenderedHash=null');
run('render()');assert.equal(nav[0].attrs['aria-current'],'page');assert.equal(focuses.at(-1).name,'#app h1');assert.equal(nodes['#app h1'].attrs.tabindex,'-1');
const n=focuses.length,sc=scrolls;run('render()');assert.equal(focuses.length,n);assert.equal(scrolls,sc); // unrelated same-route updates do not reset focus/scroll
heading.textContent='Choose a path that fits your starting point.';
ctx.location.hash='#paths';run('render()');assert.equal(ctx.document.title,'Choose a path that fits your starting point. | Binary School');assert.equal(nav[0].attrs['aria-current'],undefined);assert.equal(nav[1].attrs['aria-current'],'page');assert.equal(focuses.length,n+1);
const menu=nodes['#workspace-menu'],sidebar=nodes['#workspace-sidebar'];
assert(html.includes('id="workspace-menu" aria-expanded="false" aria-controls="workspace-nav"'));
assert(html.includes('<nav id="workspace-nav" aria-label="Workspace">'));
menu.onclick();assert.equal(menu.getAttribute('aria-expanded'),'true');
let escapePrevented=false;
sidebar.onkeydown({key:'Escape',preventDefault(){escapePrevented=true}});
assert(!escapePrevented);assert.equal(menu.getAttribute('aria-expanded'),'true');
mobile=true;
sidebar.onkeydown({key:'Escape',preventDefault(){escapePrevented=true}});
assert(escapePrevented);assert.equal(menu.getAttribute('aria-expanded'),'false');assert.equal(focuses.at(-1).name,'#workspace-menu');
menu.onclick();
const currentLink={closest:()=>({hash:ctx.location.hash})};
sidebar.onclick({target:currentLink,ctrlKey:true});assert.equal(menu.getAttribute('aria-expanded'),'true');
sidebar.onclick({target:currentLink});assert.equal(menu.getAttribute('aria-expanded'),'false');assert.equal(focuses.at(-1).name,'#app h1');
mobile=true;ctx.location.hash='#lesson/26';run('render()');assert.equal(nodes['.lessonoutline'].open,false);
mobile=false;nodes['.lessonoutline'].open=true;ctx.location.hash='#lesson/27';run('render()');assert.equal(nodes['.lessonoutline'].open,true);
const lesson=run('lesson(27)');assert(lesson.includes('role="navigation"'));assert(lesson.includes('<details class="lessonoutline" open>'));assert(lesson.includes('aria-current="page"'));assert(lesson.includes('</div></details></div><article'));
for(const id of [91,94]){
 const markup=run('lesson('+id+')');
 assert.equal((markup.match(/data-lesson-jump="lesson-practical"/g)||[]).length,1);
 assert(markup.includes('data-lesson-jump="lesson-practical">Practical'));
 assert(markup.includes('id="lesson-practical"')&&markup.includes(' download>'));
}
assert(run('lesson(0)').includes('data-lesson-jump="lesson-downloads">Downloads'));
for(const c of db.courses)assert(run('cards()').includes(c[2]+' study completion'));
assert.equal((run('cards()').match(/<h2>/g)||[]).length,db.courses.length);
assert.equal((run('home()').match(/<h3>/g)||[]).length,db.courses.length);
assert.match(run('course("foundations")'),/<h2>Interactive binary lab/);
const syllabus=run('syllabus()');
for(const heading of ['How to study','Syllabus coverage map','Readiness checklist','Teaching and assessment boundaries'])assert(syllabus.includes('<h2>'+heading));
assert.match(syllabus,/<h2>Syllabus revision route<\/h2>[\s\S]*<h3>Week 1/);

nodes['#naturalbutton']=make('#naturalbutton',true);run("focusContent('#naturalbutton')");assert.equal(nodes['#naturalbutton'].attrs.tabindex,undefined);
let pickerClicks=0;(nodes['#import']??=make('#import')).click=()=>pickerClicks++;run('bindResources()');nodes['#chooseimport'].onclick();assert.equal(pickerClicks,1);assert(run('resources()').includes('type="button" id="chooseimport"'));
const css=fs.readFileSync(path.join(site,'style.css'),'utf8');assert(css.includes('.skiplink:focus'));assert(css.includes(':focus-visible'));assert(css.includes('.lessonnav{max-height:none;overflow:visible}'));
console.log('Passed: non-routing skip link, route-only heading focus, current-page labels, mobile workspace menu and lesson disclosure, progress names and natural control tab order.');
