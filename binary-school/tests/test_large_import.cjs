const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const site=path.join(__dirname,'..','site');let source=fs.readFileSync(path.join(site,'app.js'),'utf8');source=source.slice(0,source.lastIndexOf("fetch('curriculum.json')"));
const nodes={},disk={},downloads=[];let reads=0,quota=false;
const context={window:{addEventListener(){}},document:{querySelector:key=>nodes[key]??=({value:'',innerHTML:'',textContent:'',style:{},setAttribute(){}}),querySelectorAll:()=>[]},localStorage:{getItem:k=>disk[k]??null,setItem(k,v){if(quota)throw Error('quota');disk[k]=v}},setTimeout:()=>0};
vm.createContext(context);vm.runInContext(source,context);const run=s=>vm.runInContext(s,context);context.capture=(name,bytes)=>downloads.push({name,bytes});run('db='+fs.readFileSync(path.join(site,'curriculum.json'),'utf8')+';initializeProgress();download=(name,bytes)=>capture(name,bytes);render=()=>{}');
async function test(){
 // Use the app's own exporter so the test proves its large exports are accepted.
 run('state.notes[0]="x".repeat(5000001);bindResources()');nodes['#export'].onclick();const exported=downloads[0].bytes;assert(exported.length>5000000);
 const before=run('JSON.stringify(state)');context.file={name:'own-large-export.json',size:exported.length,text:async()=>{reads++;return exported}};
 await run('previewImport(file)');assert.equal(reads,0);assert.equal(run('pendingImport'),null);assert.equal(run('JSON.stringify(state)'),before);assert.match(nodes['#importpreview'].innerHTML,/memory and storage/);
 const staleConfirm=nodes['#readlargeimport'].onclick;nodes['#cancelimport'].onclick();await staleConfirm();assert.equal(reads,0);assert.equal(run('JSON.stringify(state)'),before);
 await run('previewImport(file)');await nodes['#readlargeimport'].onclick();assert.equal(reads,1);assert.equal(run('pendingImport.data.notes[0].length'),5000001);assert.equal(downloads.length,1);assert.equal(run('JSON.stringify(state)'),before);
 quota=true;run('applyImport("merge")');assert.match(nodes['#importfeedback'].textContent,/not applied/);assert.equal(run('JSON.stringify(state)'),before);quota=false;
 context.document.querySelector('#confirmreplace').checked=true;run('applyImport("replace")');assert.equal(JSON.parse(disk['binary-school-v1']).notes[0].length,5000001);assert.equal(downloads.length,2);
 let resolveOld;context.file={name:'slow-large.json',size:6000000,text:()=>new Promise(resolve=>resolveOld=resolve)};await run('previewImport(file)');const old=nodes['#readlargeimport'].onclick();nodes['#cancelimport'].onclick();resolveOld(exported);await old;assert.equal(run('pendingImport'),null);assert.match(nodes['#importpreview'].innerHTML,/canceled/);
 await run('previewImport(file)');const obsolete=nodes['#readlargeimport'].onclick;context.small={name:'new.json',size:20,text:async()=>'{"done":[],"notes":{"0":"new"}}'};await run('previewImport(small)');await obsolete();assert.equal(run('pendingImport.name'),'new.json');
 console.log('Passed: large own-export restore, explicit read confirmation, unchanged preview/cancel, stale confirmation/read protection and honest quota failure.');
}
test().catch(error=>{console.error(error);process.exitCode=1});
