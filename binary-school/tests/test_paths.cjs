const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const root=path.join(__dirname,'..','site');let source=fs.readFileSync(path.join(root,'app.js'),'utf8');source=source.slice(0,source.lastIndexOf("fetch('curriculum.json')"));
const els={},buttons=[{dataset:{path:'foundation'}},{dataset:{path:'revision'}}],saved={};let renders=0;
const element=()=>({value:'',textContent:'',innerHTML:'',style:{},classList:{toggle(){}},setAttribute(){}});
const ctx={location:{hash:'#paths'},window:{addEventListener(){}},localStorage:{getItem:()=>null,setItem:(k,v)=>saved[k]=v},document:{querySelector:s=>els[s]??(els[s]=element()),querySelectorAll:s=>s==='[data-path]'?buttons:[]},setTimeout:()=>0};
vm.createContext(ctx);vm.runInContext(source,ctx);const db=JSON.parse(fs.readFileSync(path.join(root,'curriculum.json'),'utf8'));vm.runInContext('db='+JSON.stringify(db),ctx);ctx.rendered=()=>renders++;vm.runInContext('render=()=>rendered()',ctx);
const run=s=>vm.runInContext(s,ctx),plain=s=>JSON.parse(JSON.stringify(run(s)));
for(const week of db.studyPlan.weeks){assert(week.lessons.includes(week.target));for(const id of week.lessons)assert(db.lessons.some(l=>l.id===id));assert(week.prerequisite&&week.deliverable&&week.effort);}
assert(run('studyPaths()').includes('does not establish debugger competence'));run('bindStudyPaths()');buttons[1].onclick();assert.equal(run('state.learningPath'),'revision');assert.equal(renders,1);
const revision=plain('activeStudyLessons().map(l=>l.id)');assert.equal(revision[0],0);assert(revision.length<db.lessons.filter(l=>l.course!=='secure').length);assert.equal(revision.at(-1),94);
ctx.location.hash='#lesson/0';assert.equal(run('following(0).id'),129);
ctx.location.hash='#lesson/26';assert.equal(run('following(26).id'),27); // outside selected route, continue the local teaching sequence
ctx.location.hash='#paths';run('state.done=[0,129]');assert.equal(run('next().id'),8);
buttons[0].onclick();assert.equal(run('activeStudyLessons().length'),db.lessons.filter(l=>l.course!=='secure').length);assert.deepEqual(plain('state.done'),[0,129]);
run('bindStudyPaths()');db.studyPlan.diagnostic.forEach((q,i)=>(els['#diagnostic'+i]??=element()).value=q.answer.split('|')[0]);els['#diagnosticform'].onsubmit({preventDefault(){}});assert.equal(run('state.diagnostic.length'),6);assert.deepEqual(plain('state.done'),[0,129]);assert(els['#diagnosticfeedback'].innerHTML.includes('revision route'));
els['#diagnostic0'].value='wrong';els['#diagnosticform'].onsubmit({preventDefault(){}});assert.equal(run('state.diagnostic.length'),5);assert(els['#diagnosticfeedback'].innerHTML.includes('foundation route'));
assert(run('searchResults("Artifact checklist")').includes('#lesson/129'));assert(run('searchResults("competing runtime hypotheses")').includes('#lesson/116'));
assert(!run('searchableLesson(db.lessons.find(l=>l.id===119))').includes('bs{workshop_')); // do not index worked flag answers
for(const l of db.lessons.filter(l=>l.practical&&l.id!==117&&l.id!==94))assert(!l.practical.start.includes('no Linux ELF equivalent'));
assert(run('syllabus()').includes('instructor permission'));assert(run('syllabus()').includes('substantive use'));assert(run('syllabus()').includes('Four outcomes, concrete evidence'));
const backup=plain('normalizeBackup(state)');assert.equal(backup.learningPath,'foundation');assert.equal(backup.diagnostic.length,5);
const merged=plain('mergeBackups(state,{done:[],notes:{},learningPath:"revision",diagnostic:["c"]})');assert.equal(merged.learningPath,'foundation');assert(merged.diagnostic.includes('c'));
console.log('Passed: prerequisite feedback without lesson credit, both study routes/navigation, expanded search, platform wording, outcome/policy coverage and backup compatibility.');
