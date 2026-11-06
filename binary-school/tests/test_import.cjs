// Optional maintainer regressions for non-destructive progress import.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const site=path.join(__dirname,'..','site');
let source=fs.readFileSync(path.join(site,'app.js'),'utf8');source=source.slice(0,source.lastIndexOf("fetch('curriculum.json')"));
let elements={},disk={},failKey=null,downloads=[],downloadFails=false,renders=0;
const element=()=>({value:'',checked:false,innerHTML:'',textContent:'',style:{},classList:{toggle(){}},setAttribute(){}});
const context={window:{addEventListener(){}},document:{querySelector:key=>elements[key]??(elements[key]=element()),querySelectorAll:()=>[]},localStorage:{getItem:key=>disk[key]||null,setItem:(key,value)=>{if(failKey===key)throw Error('quota');disk[key]=value}},setTimeout:()=>0};
vm.createContext(context);vm.runInContext(source,context);
vm.runInContext('db='+fs.readFileSync(path.join(site,'curriculum.json'),'utf8'),context);
context.captureDownload=(name,bytes)=>{if(downloadFails)throw Error('blocked');downloads.push({name,bytes});};context.captureRender=()=>renders++;
vm.runInContext('download=(name,bytes)=>captureDownload(name,bytes);render=()=>captureRender()',context);
const evaluate=code=>vm.runInContext(code,context);
const plain=code=>JSON.parse(JSON.stringify(evaluate(code)));
const current={done:[0,26],notes:{0:'Current notes',26:'Keep me',final:'My patch reasoning'},evidence:{119:'Current report'},name:'Current Name',exam:true,checkpoints:[0],practicalChecks:[119],flagsSolved:[108],readiness:{static:true},reviews:{119:{0:true,1:false}},holdout:{'final-cedar-guided-linux-x64':true}};
const incoming={done:[26,27,27,999],notes:{0:'Imported notes',27:'New notes'},evidence:{119:'Imported report'},name:'Backup Name',exam:false,checkpoints:[27],practicalChecks:[113],flagsSolved:[109,0],readiness:{debug:true},reviews:{119:{0:false,1:true}},holdout:{'final-quartz-independent-linux-x64':true}};
function reset(){elements={};disk={'binary-school-v1':JSON.stringify(current)};failKey=null;downloads=[];renders=0;downloadFails=false;evaluate('state='+JSON.stringify(current)+';pendingImport=null');}
async function preview(data=incoming,name='backup.json'){context.file={name,size:100,text:async()=>JSON.stringify(data)};await evaluate('previewImport(file)');}
async function test(){
 reset();const normalized=plain('normalizeBackup('+JSON.stringify(incoming)+')');assert.deepEqual(normalized.done,[26,27]);assert.deepEqual(normalized.flagsSolved,[109]);
 assert.throws(()=>evaluate('normalizeBackup({done:[],notes:[]})'));
 assert.throws(()=>evaluate('normalizeBackup({notes:{}})'));
 const legacy=plain('normalizeBackup({done:[0],notes:{0:"old",final:"patch"}})');assert.deepEqual(legacy.checkpoints,[]);assert.equal(legacy.notes.final,'patch');
 const malicious=JSON.parse('{"done":[0],"notes":{"__proto__":{"polluted":true},"0":"valid","999":"unknown"},"reviews":{"__proto__":{"0":true}}}');
 const sanitized=plain('normalizeBackup('+JSON.stringify(malicious)+')');assert.deepEqual(sanitized.notes,{'0':'valid'});assert.equal({}.polluted,undefined);
 await preview();assert.deepEqual(plain('state'),current);assert.equal(downloads.length,0);assert(elements['#importpreview'].innerHTML.includes('Selected backup:'));
 elements['#cancelimport'].onclick();assert.equal(evaluate('pendingImport'),null);assert.deepEqual(plain('state'),current);
 await preview();evaluate('applyImport("replace")');assert(elements['#importfeedback'].textContent.includes('Confirm'));assert.deepEqual(plain('state'),current);assert.equal(downloads.length,0);
 evaluate('applyImport("merge")');const merged=plain('state');assert.deepEqual(merged.done,[0,26,27]);assert(merged.notes[0].includes('Current notes\n\n--- Imported backup ---\nImported notes'));assert.equal(merged.notes[26],'Keep me');assert.equal(merged.notes[27],'New notes');assert(merged.evidence[119].includes('Imported report'));assert.deepEqual(merged.reviews[119],{'0':true,'1':true});assert.equal(merged.name,'Current Name');assert(merged.exam);assert(merged.readiness.static&&merged.readiness.debug);assert.equal(Object.keys(merged.holdout).length,2);assert.equal(downloads.length,1);assert.equal(downloads[0].name,'binary-school-progress-before-import.json');assert.deepEqual(JSON.parse(disk['binary-school-before-import-v1']),current);assert.deepEqual(JSON.parse(disk['binary-school-v1']),merged);assert.equal(renders,1);
 assert.equal(plain('mergeBackups(state,'+JSON.stringify(incoming)+')').notes[0],merged.notes[0]);
 evaluate('bindResources()');elements['#recoverimport'].onclick();assert.equal(plain('pendingImport').name,'Pre-import recovery snapshot');assert.deepEqual(plain('state'),merged);
 reset();await preview();(elements['#confirmreplace']??=element()).checked=true;evaluate('applyImport("replace")');const replaced=plain('state');assert.equal(replaced.notes[26],undefined);assert.equal(replaced.name,'Backup Name');assert.equal(replaced.exam,false);assert.deepEqual(replaced.done,[26,27]);assert.deepEqual(JSON.parse(disk['binary-school-before-import-v1']),current);
 for(const key of ['binary-school-before-import-v1','binary-school-v1']){reset();await preview();failKey=key;evaluate('applyImport("merge")');assert.deepEqual(plain('state'),current);assert.deepEqual(JSON.parse(disk['binary-school-v1']),current);assert(elements['#importfeedback'].textContent.includes('not applied'));}
 reset();await preview();downloadFails=true;evaluate('applyImport("merge")');assert.deepEqual(plain('state'),current);assert.deepEqual(JSON.parse(disk['binary-school-v1']),current);
 reset();await preview();evaluate('startupRaw="{damaged";invalidCopyStored=false;hasUnsavedProgress=true');evaluate('applyImport("merge")');assert.equal(disk['binary-school-invalid-progress-v1'],'{damaged');assert.equal(evaluate('hasUnsavedProgress'),false);
 reset();await preview();evaluate('startupRaw="{damaged";invalidCopyStored=false;hasUnsavedProgress=true');failKey='binary-school-invalid-progress-v1';evaluate('applyImport("merge")');assert.deepEqual(plain('state'),current);assert.deepEqual(JSON.parse(disk['binary-school-v1']),current);assert.equal(evaluate('hasUnsavedProgress'),true);
 reset();context.file={name:'broken.json',size:10,text:async()=>'{broken'};await evaluate('previewImport(file)');assert.equal(evaluate('pendingImport'),null);assert(elements['#importpreview'].innerHTML.includes('Invalid JSON'));assert.deepEqual(plain('state'),current);
 context.file={name:'large.json',size:5000001,text:()=>{throw Error('must not read oversized file')}};await evaluate('previewImport(file)');assert(elements['#importpreview'].innerHTML.includes('too large'));
 let resolveOld;context.file={name:'old.json',size:10,text:()=>new Promise(resolve=>resolveOld=resolve)};const old=evaluate('previewImport(file)');await preview(incoming,'new.json');resolveOld(JSON.stringify(current));await old;assert.equal(plain('pendingImport').name,'new.json');
 console.log('Passed: backup preview/cancel, legacy validation, merge conflicts, replacement confirmation, recovery/export, quota/download failures, and stale file reads.');
}
test().catch(error=>{console.error(error);process.exitCode=1});
