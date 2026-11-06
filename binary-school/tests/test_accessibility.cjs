// Structural and focus-flow regressions; not a substitute for live assistive-technology QA.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const site=path.join(__dirname,'..','site');let src=fs.readFileSync(path.join(site,'app.js'),'utf8');src=src.slice(0,src.lastIndexOf("fetch('curriculum.json')"));
let nodes={},focuses=[],mobile=false,scrolls=0;const make=(name,natural=false)=>({value:'',innerHTML:'',textContent:'',open:true,dataset:{},attrs:{},style:{},matches:()=>natural,setAttribute(k,v){this.attrs[k]=v},removeAttribute(k){delete this.attrs[k]},focus(options){focuses.push({name,options})},classList:{toggle(){}}});
const nav=[make('home-link',true),make('paths-link',true)];nav[0].dataset.nav='home';nav[1].dataset.nav='paths';
const ctx={location:{hash:'#home'},window:{addEventListener(){},scrollTo(){scrolls++},matchMedia:()=>({matches:mobile})},localStorage:{getItem:()=>null,setItem(){}},document:{querySelector:key=>nodes[key]??(nodes[key]=make(key)),querySelectorAll:key=>key==='[data-nav]'?nav:[]},setTimeout:()=>0};
vm.createContext(ctx);vm.runInContext(src,ctx);const db=JSON.parse(fs.readFileSync(path.join(site,'curriculum.json'),'utf8'));vm.runInContext('db='+JSON.stringify(db),ctx);
const run=s=>vm.runInContext(s,ctx);
const html=fs.readFileSync(path.join(site,'index.html'),'utf8');assert(html.includes('id="skipcontent"'));assert(html.includes('<main id="main-content" tabindex="-1">'));
let prevented=false;nodes['#skipcontent'].onclick({preventDefault(){prevented=true}});assert(prevented);assert.equal(ctx.location.hash,'#home');assert.equal(focuses.at(-1).name,'#main-content');assert.equal(focuses.at(-1).options.preventScroll,false);
run('render()');assert.equal(nav[0].attrs['aria-current'],'page');assert.equal(focuses.at(-1).name,'#app h1');assert.equal(nodes['#app h1'].attrs.tabindex,'-1');
const n=focuses.length,sc=scrolls;run('render()');assert.equal(focuses.length,n);assert.equal(scrolls,sc); // unrelated same-route updates do not reset focus/scroll
ctx.location.hash='#paths';run('render()');assert.equal(nav[0].attrs['aria-current'],undefined);assert.equal(nav[1].attrs['aria-current'],'page');assert.equal(focuses.length,n+1);
mobile=true;ctx.location.hash='#lesson/26';run('render()');assert.equal(nodes['.lessonoutline'].open,false);
mobile=false;nodes['.lessonoutline'].open=true;ctx.location.hash='#lesson/27';run('render()');assert.equal(nodes['.lessonoutline'].open,true);
const lesson=run('lesson(27)');assert(lesson.includes('role="navigation"'));assert(lesson.includes('<details class="lessonoutline" open>'));assert(lesson.includes('aria-current="page"'));assert(lesson.includes('</div></details></div><article'));
for(const c of db.courses)assert(run('cards()').includes(c[2]+' study completion'));
nodes['#naturalbutton']=make('#naturalbutton',true);run("focusContent('#naturalbutton')");assert.equal(nodes['#naturalbutton'].attrs.tabindex,undefined);
let pickerClicks=0;(nodes['#import']??=make('#import')).click=()=>pickerClicks++;run('bindResources()');nodes['#chooseimport'].onclick();assert.equal(pickerClicks,1);assert(run('resources()').includes('type="button" id="chooseimport"'));
const css=fs.readFileSync(path.join(site,'style.css'),'utf8');assert(css.includes('.skiplink:focus'));assert(css.includes(':focus-visible'));assert(css.includes('.lessonnav{max-height:none;overflow:visible}'));
console.log('Passed: non-routing skip link, route-only heading focus, current-page labels, native mobile disclosure, progress names and natural control tab order.');
