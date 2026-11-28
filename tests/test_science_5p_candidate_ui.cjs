// Exercise the exact candidate browser functions extracted from the HTML.
// Node-only isolated test; no actual user account, browser or network.
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const html=fs.readFileSync("web_v1_static_preview/index.html","utf8");
const start=html.indexOf("function science5pSelection(){");
const end=html.indexOf("async function populateMaterialList(){",start);
assert(start>=0&&end>start);
let clicks=0, requests=0, balance=null, fetchImpl, params, key="selected", allowed=true;
const fakeLink={click(){clicks++},remove(){}};
const ctx=vm.createContext({
 curriculum:{value:"kssr"},subject:{value:"SCIENCE"},year:{value:"5"},lesson:{value:"SK27-SCI-Y5-PDP-001"},
 currentRphParams:()=>params,currentRphLessonKey:()=>key,canGenerateRph:()=>allowed,
 rphDownloadBusy:false,teacherReflectionMode:{value:"auto"},teacherReflection:{value:""},
 document:{getElementById:()=>({textContent:""}),createElement:()=>fakeLink,body:{append(){}}},
 fetch:async (...args)=>{requests++;return fetchImpl(...args)},
 updateRphTrialFromDenial(){},applyRphAccount(a){balance=a.rph_trial_remaining;if(balance===0)allowed=false;},
 showRphAction(){},URL:{createObjectURL:()=>"blob:test",revokeObjectURL(){}},setTimeout(){},
});
vm.runInContext(html.slice(start,end),ctx);
const select=()=>vm.runInContext("science5pSelection()",ctx);
const download=()=>vm.runInContext('downloadScience5pReviewed("word")',ctx);
const token="v"+"a".repeat(24);
params=new URLSearchParams({unit:token,teacher_class:"5 Bestari"});
assert.equal(select().unit,token);
ctx.year.value="4";assert.equal(select(),null);
ctx.year.value="6";assert.equal(select(),null);
ctx.year.value="5";ctx.subject.value="SCIENCE_DLP";assert.equal(select(),null);
ctx.subject.value="SCIENCE";
params.set("unit","u"+"a".repeat(24));assert.equal(select(),null);
params.set("unit",token);
function response(remaining="0"){
 return {ok:true,headers:{get(k){return {"X-RPH-Trial-Remaining":remaining,"X-RPH-QA-Status":"INTERNAL-REVIEWED","content-type":"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}[k]}},blob:async()=>({size:2000})};
}
(async()=>{
 fetchImpl=async(url,opts)=>{
  assert.equal(url,"/api/kssr/sk/science/5p/download");
  const p=JSON.parse(opts.body);assert.equal(p.unit,token);assert.equal(p.rph_variant,"5p");
  return response();
 };
 await download();assert.equal(clicks,1);assert.equal(balance,0);
 allowed=true;
 fetchImpl=async()=>{ctx.teacherReflection.value="changed";return response("8")};
 await download();assert.equal(clicks,1);assert.equal(balance,8);
 assert.equal(requests,2);
 assert(html.includes('data.status==="INTERNAL-REVIEWED"'));
 console.log("Science 5P isolated UI selection, last-credit delivery and stale reflection checks passed");
})().catch(e=>{console.error(e);process.exitCode=1});
