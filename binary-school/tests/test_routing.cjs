// Exercise real startup promises and hashchange registration with absent DOM controls.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const site=path.join(__dirname,'..','site'),source=fs.readFileSync(path.join(site,'app.js'),'utf8'),db=JSON.parse(fs.readFileSync(path.join(site,'curriculum.json'),'utf8'));
function browser(hash){
 const nodes={},events={},disk={},focuses=[];
 const element=name=>({value:'',innerHTML:'',textContent:'',style:{},classList:{toggle(){}},setAttribute(){},removeAttribute(){},matches:()=>false,focus(){focuses.push(name)}});
 for(const id of ['app','crumb','toast','progressnotice'])nodes['#'+id]=element('#'+id);
 const context={location:{hash},window:{addEventListener:(name,fn)=>events[name]=fn,scrollTo(){}},document:{querySelector(selector){if(nodes[selector]&&['#app','#crumb','#toast','#progressnotice'].includes(selector))return nodes[selector];const html=nodes['#app'].innerHTML;if(selector==='#app h1')return html.includes('<h1>')?(nodes[selector]??=element(selector)):null;if(selector==='.lessonoutline')return null;if(selector.startsWith('#')&&html.includes('id="'+selector.slice(1)+'"'))return nodes[selector]??=element(selector);return null},querySelectorAll:()=>[]},localStorage:{getItem:k=>disk[k]??null,setItem:(k,v)=>disk[k]=v},fetch:async()=>({ok:true,json:async()=>db}),setTimeout:()=>0};
 vm.createContext(context);vm.runInContext(source,context);
 return {context,nodes,events,disk,focuses,run:code=>vm.runInContext(code,context),navigate(hash){context.location.hash=hash;assert.equal(typeof events.hashchange,'function');assert.doesNotThrow(()=>events.hashchange())}};
}
const settled=()=>new Promise(resolve=>setImmediate(resolve));
async function test(){
 for(const hash of ['#lesson/999','#lesson/not-a-number','#course/missing']){
  const b=browser(hash);await settled();assert.match(b.nodes['#app'].innerHTML,/<h1>(Lesson|Course) not found\./);assert(b.nodes['#app'].innerHTML.includes('href="#courses"'));assert(b.nodes['#app'].innerHTML.includes('href="#catalog"'));assert.equal(b.run('activeLessonId'),null);assert.equal(b.focuses.at(-1),'#app h1');
  b.navigate('#lesson/0');assert.equal(b.run('activeLessonId'),0);assert.equal(typeof b.nodes['#notes'].oninput,'function');assert.equal(typeof b.nodes['#answerform'].onsubmit,'function');
  b.nodes['#notes'].value='Retain the draft when a link is invalid';b.navigate('#lesson/999');assert.equal(JSON.parse(b.disk['binary-school-v1']).notes[0],'Retain the draft when a link is invalid');assert.equal(b.run('activeLessonId'),null);
  b.navigate('#courses');assert(b.nodes['#app'].innerHTML.includes('Build understanding'));b.navigate('#lesson/26');assert.equal(b.run('activeLessonId'),26);
 }
 const b=browser('#home');b.run('home=()=>{throw Error("render failure")}');await settled();assert.match(b.nodes['#app'].innerHTML,/<h1>This view could not load\./);assert(b.nodes['#app'].innerHTML.includes('href="#resources"'));b.navigate('#lesson/0');assert.equal(b.run('activeLessonId'),0);
 b.run('lesson=()=>{throw Error("later failure")}');b.navigate('#lesson/26');assert(b.nodes['#app'].innerHTML.includes('This view could not load'));assert.equal(b.run('activeLessonId'),null);b.navigate('#courses');assert(b.nodes['#app'].innerHTML.includes('Build understanding'));
 console.log('Passed: missing lesson/course entry, accessible recovery links/focus, notebook preservation, startup and later rendering failures, and hash navigation recovery.');
}
test().catch(error=>{console.error(error);process.exitCode=1});
