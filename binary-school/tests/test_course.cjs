// Optional UI/data checks for maintainers. Node.js is NOT needed to run the site.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const root=path.join(__dirname,'..','site')+path.sep;
let src=fs.readFileSync(root+'app.js','utf8');src=src.slice(0,src.lastIndexOf("fetch('curriculum.json')"));
let saved={},els={};const element=()=>({value:'',innerHTML:'',textContent:'',className:'',dataset:{},style:{},classList:{toggle(){}},setAttribute(){}});
const ctx={crypto:require('crypto').webcrypto,TextEncoder,Uint8Array,localStorage:{getItem:()=>JSON.stringify({done:[0,25,26],notes:{0:'retained'},exam:false,name:''}),setItem:(k,v)=>saved[k]=v},document:{querySelector:s=>els[s]??(els[s]=element()),querySelectorAll:()=>[]},setTimeout:()=>0};
vm.createContext(ctx);vm.runInContext(src,ctx);const db=JSON.parse(fs.readFileSync(root+'curriculum.json','utf8'));vm.runInContext('db='+JSON.stringify(db),ctx);
async function test(){
 assert.equal(db.courses.length,13);assert.equal(db.lessons.length,137);assert.equal(new Set(db.lessons.map(l=>l.id)).size,137);
 for(const l of db.lessons){let html=vm.runInContext(`lesson(${l.id})`,ctx);assert(html.includes('id="answerform"'));if(l.id>=42)assert(html.includes('Worked solution'));if(l.flagDigest){assert(html.includes('Guided Linux x64 executable'));assert(html.includes('case-sensitive'));}}
 for(const c of db.courses){let l=db.lessons.find(l=>l.id===db.courseLabs[c[0]]);assert(l&&l.flagDigest);assert(vm.runInContext(`course(${JSON.stringify(c[0])})`,ctx).includes('Open interactive lab'));let flag=l.solution.match(/BS\{[^}]+\}/)[0];
  vm.runInContext(`bind('lesson',${l.id})`,ctx);(els['#answer']??=element()).value='BS{wrong}';await els['#answerform'].onsubmit({preventDefault(){}});assert(els['#feedback'].textContent.includes('does not match'));
  els['#answer'].value=flag.toLowerCase();await els['#answerform'].onsubmit({preventDefault(){}});assert(els['#feedback'].textContent.includes('does not match'));
  els['#answer'].value=flag;await els['#answerform'].onsubmit({preventDefault(){}});assert(els['#feedback'].textContent.includes('Flag found!'));assert(vm.runInContext(`done(${l.id})`,ctx));
 }
 assert.equal(JSON.parse(saved['binary-school-v1']).flagsSolved.length,13);assert.equal(vm.runInContext('state.notes[0]',ctx),'retained');assert(vm.runInContext('searchResults("stack arguments")',ctx).includes('Stack arguments without push'));
 console.log('Passed: all 137 lessons render, all 13 courses expose flag labs, wrong/case-wrong/correct flag feedback works, and existing notes survive.');
}
test().catch(e=>{console.error(e);process.exitCode=1});
