// Optional UI/data checks for maintainers. Node.js is NOT needed to run the site.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const root=path.join(__dirname,'..','site')+path.sep;
let src=fs.readFileSync(root+'app.js','utf8');src=src.slice(0,src.lastIndexOf("fetch('curriculum.json')"));
let saved={},els={},storageFails=false;const events={};const element=()=>({value:'',innerHTML:'',textContent:'',className:'',dataset:{},style:{},classList:{toggle(){}},setAttribute(){}});
const ctx={window:{addEventListener(name,fn){events[name]=fn},scrollTo(){}},location:{hash:'#home'},crypto:require('crypto').webcrypto,TextEncoder,Uint8Array,localStorage:{getItem:()=>JSON.stringify({done:[0,25,26],notes:{0:'retained'},exam:false,name:''}),setItem:(k,v)=>{if(storageFails)throw Error('quota');saved[k]=v}},document:{querySelector:s=>els[s]??(els[s]=element()),querySelectorAll:()=>[]},setTimeout:()=>0};
vm.createContext(ctx);vm.runInContext(src,ctx);const db=JSON.parse(fs.readFileSync(root+'curriculum.json','utf8'));vm.runInContext('db='+JSON.stringify(db)+';initializeProgress()',ctx);
async function test(){
 assert.equal(db.courses.length,13);assert.equal(db.lessons.length,137);assert.equal(new Set(db.lessons.map(l=>l.id)).size,137);
 for(const l of db.lessons){let html=vm.runInContext(`lesson(${l.id})`,ctx);assert(html.includes('id="answerform"'));if(l.id>=42)assert(html.includes('Worked solution'));if(l.flagDigest){assert(html.includes('Guided Linux x64 executable'));assert(html.includes('case-sensitive'));}}
 for(const c of db.courses){let l=db.lessons.find(l=>l.id===db.courseLabs[c[0]]);assert(l&&l.flagDigest);assert(vm.runInContext(`course(${JSON.stringify(c[0])})`,ctx).includes('Open interactive lab'));let flag=l.solution.match(/BS\{[^}]+\}/)[0];
  vm.runInContext(`bind('lesson',${l.id})`,ctx);(els['#answer']??=element()).value='BS{wrong}';await els['#answerform'].onsubmit({preventDefault(){}});assert(els['#feedback'].textContent.includes('does not match'));
  els['#answer'].value=flag.toLowerCase();await els['#answerform'].onsubmit({preventDefault(){}});assert(els['#feedback'].textContent.includes('does not match'));
  els['#answer'].value=flag;await els['#answerform'].onsubmit({preventDefault(){}});assert(els['#feedback'].textContent.includes('Flag found!'));assert(vm.runInContext(`done(${l.id})`,ctx));
 }
 assert.equal(JSON.parse(saved['binary-school-v1']).flagsSolved.length,13);assert.equal(vm.runInContext('state.notes[0]',ctx),'retained');assert(vm.runInContext('searchResults("stack arguments")',ctx).includes('Stack arguments without push'));

 // Regression: note input autosaves, and route/page lifecycle preserve unsaved DOM text.
 vm.runInContext("bind('lesson',0)",ctx);
 els['#notes'].value='typed without pressing Save';els['#notes'].oninput();
 assert.equal(JSON.parse(saved['binary-school-v1']).notes[0],'typed without pressing Save');
 els['#notes'].value='last keystroke before route';ctx.location.hash='#course/assembly';
 vm.runInContext('render()',ctx);
 assert.equal(JSON.parse(saved['binary-school-v1']).notes[0],'last keystroke before route');
 vm.runInContext("bind('lesson',26)",ctx);els['#notes'].value='tab closing draft';events.pagehide();
 assert.equal(JSON.parse(saved['binary-school-v1']).notes[26],'tab closing draft');
 storageFails=true;els['#notes'].value='quota error still held in memory';els['#notes'].oninput();
 assert(els['#notestatus'].textContent.includes('Could not save'));
 assert.equal(vm.runInContext('state.notes[26]',ctx),'quota error still held in memory');
 let prevented=false;events.beforeunload({preventDefault(){prevented=true}});assert(prevented);storageFails=false;
 // Successful optional checkpoint does not claim the whole practical is evaluated.
 vm.runInContext("bind('lesson',94)",ctx);els['#answer'].value='file';await els['#answerform'].onsubmit({preventDefault(){}});
 assert(vm.runInContext('state.checkpoints.includes(94)',ctx));assert(!vm.runInContext('done(94)',ctx));
 // Practical predictions preserve/report evidence separately from study completion.
 vm.runInContext("bind('lesson',119)",ctx);
 const practical=db.lessons.find(l=>l.id===119).practical;
 practical.checks.forEach((r,i)=>{(els['#practice'+i]??=element()).value=r[1]});els['#checkpractical'].onclick();
 assert(vm.runInContext('state.practicalChecks.includes(119)',ctx));
 els['#practicalevidence'].value='My independently recorded branch and struct evidence';els['#practicalevidence'].oninput();
 assert(vm.runInContext('state.evidence[119].includes("branch")',ctx));
 assert(vm.runInContext('readiness()',ctx).includes('recorded (ungraded)'));
 // File checker accepts the fresh exact data repair; rejects original, wrong build, unrelated edits.
 const manifest=JSON.parse(fs.readFileSync(root+'labs/readiness/repair-manifest.json','utf8'));
 ctx.fetch=async()=>({ok:true,json:async()=>manifest});
 const target='final-cedar-guided-linux-x64';(els['#repairtarget']??=element()).value=target;
 let bytes=fs.readFileSync(root+'labs/readiness/'+target);
 const upload=async b=>{await vm.runInContext('checkHoldoutRepair',ctx)({target:{files:[{size:b.length,arrayBuffer:async()=>b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength)}]}})};
 await upload(bytes);assert(els['#repairfeedback'].textContent.includes('unchanged original'));
 bytes=Buffer.from(bytes);bytes.writeInt32LE(9,manifest[target].offset);await upload(bytes);
 assert(els['#repairfeedback'].textContent.includes('Validated:'));
 assert(vm.runInContext(`state.holdout['${target}']`,ctx));
 bytes[0]^=1;await upload(bytes);assert(els['#repairfeedback'].textContent.includes('Does not match'));
 assert.equal(db.lessons[0].id,0);assert(vm.runInContext('lesson(94)',ctx).includes('mock-final-challenges.zip'));
 console.log('Passed: 137 lessons, 13 flag labs, notebook input/navigation/pagehide/quota regressions, separate practical evidence/checkpoints, and fresh final file validation.');
}
test().catch(e=>{console.error(e);process.exitCode=1});
