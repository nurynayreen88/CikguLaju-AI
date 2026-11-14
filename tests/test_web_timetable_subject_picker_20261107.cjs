"use strict";
/* No browser dependency: exercise the production subject selector DOM contract
   using a tiny test DOM, preserving original server subject labels/aliases. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source=fs.readFileSync("web_v1_static_preview/teacher-profile.js","utf8");
const between=(from,to)=>{
 const a=source.indexOf(from),b=source.indexOf(to,a+1);
 assert(a>=0 && b>a, "missing production helper: "+from);
 return source.slice(a,b);
};

class Element {
 constructor(tag){
  this.tag=tag; this.dataset={}; this.children=[]; this.listeners={};
  this.value=""; this.hidden=false; this.disabled=false; this.focused=false;
 }
 append(...items){this.children.push(...items);}
 add(item){this.children.push(item);}
 setAttribute(k,v){this[k]=v;}
 addEventListener(n,fn){this.listeners[n]=fn;}
 focus(){this.focused=true;}
}
const document={createElement:tag=>new Element(tag)};
function Option(label,value){this.label=label;this.value=value;}
const timetableMessage={textContent:""};
let rows=[];
const timetableBody={querySelectorAll:()=>rows};
const declarations=between("const teacherSubjectGroups = ","const profileForm = ");
const picker=between("function makeTimetableSubjectPicker(","function makeTimetableInput(");
const reader=between("function timetableValueRows()","function renderTeacherTimetable(");
const context={document,Option,timetableBody,timetableMessage};
vm.createContext(context);
vm.runInContext(declarations+picker+reader,context);
const OTHER=vm.runInContext("timetableOtherSubject",context);

function readSubject(select,custom){
 rows=[{querySelector(selector){
  const field=/data-field="([^"]+)"/.exec(selector)?.[1];
  if(field==="subject")return select;
  if(field==="subject_custom")return custom;
  return {value:{day:"Isnin",start:"08:00",end:"09:00",class_name:"4 Bestari"}[field]};
 }}];
 return context.timetableValueRows()[0].subject;
}

let checks=0;
for(const saved of ["Matematik","English","Bahasa Melayu","Pendidikan Islam",
                    "Pendidikan Moral","Pendidikan Jasmani","Pendidikan Kesihatan",
                    "Pendidikan Muzik","Bahasa Arab","Sejarah","Reka Bentuk dan Teknologi",
                    "RBT","PJ","Perhimpunan Rasmi","Rehat","Kokurikulum",
                    "Bahasa Inggeris"]){
 const wrap=context.makeTimetableSubjectPicker(saved,0);
 const [select,custom]=wrap.children;
 assert.equal(select.dataset.field,"subject");
 assert.equal(custom.dataset.field,"subject_custom");
 assert.equal(readSubject(select,custom),saved,"round-trip "+saved);
 assert.equal(custom.hidden,select.value!==OTHER,"visibility "+saved);
 assert.equal(custom.disabled,custom.hidden,"submission "+saved);
 assert.equal(select["aria-label"],"Pilih subjek untuk waktu 1");
 checks++;
}
const wrap=context.makeTimetableSubjectPicker("",7);
const [select,custom]=wrap.children;
assert.equal(select.value,"");
assert.equal(readSubject(select,custom),"");
select.value="Sains";
select.listeners.change();
assert.equal(readSubject(select,custom),"Sains");
assert.equal(custom.hidden,true);
select.value=OTHER;
select.listeners.change();
assert.equal(custom.hidden,false);
assert.equal(custom.disabled,false);
assert.equal(custom.focused,true);
custom.value="RPH Peralihan";
assert.equal(readSubject(select,custom),"RPH Peralihan");
assert.match(timetableMessage.textContent,/belum disimpan/);
const groups=select.children.filter(x=>x.tag==="optgroup");
assert.equal(groups.length,3);
assert(groups.some(g=>g.label==="Subjek utama"));
assert(groups.some(g=>g.label==="Waktu bukan PdP"));
assert(select.children.some(x=>x.value===OTHER));
console.log("PASS: "+checks+" existing subjects/aliases preserve exact value, custom choice, grouped options");

// Missing OCR class labels show their location and can be left out of import.
const reviewFields=new Element("div");
const reviewContext={
  document, Option, timetableReaderFields:reviewFields,
  teacherProfileState:{classAliases:{}},
  teacherDays:["Isnin","Selasa"],
  makeTimetableSelect:()=>new Element("select"),
  makeTimetableInput:()=>new Element("input"),
  timetableReview:{
    rows:[{day:"Selasa",start:"08:00",end:"08:30",class_name:"",subject:"Matematik"}],
    subjects:new Map([["MATEMATIK","Matematik"]]),
    classes:new Map(),
    times:[],
  },
};
vm.createContext(reviewContext);
vm.runInContext(declarations+picker+
  between("function timetableReviewGroup(","function renderTimetableReadReport("),reviewContext);
reviewContext.renderTimetableMappings("class_name");
let [legend,input]=reviewFields.children[0].children;
assert.equal(legend.textContent,"Kod kelas tidak dapat dibaca · Selasa · 08:00");
assert.equal(input.value,"");
reviewFields.children=[];
reviewContext.renderTimetableTimes();
let skip=reviewFields.children[0].children.at(-1).children[0];
assert.equal(skip.checked,true);
assert.equal(skip.disabled,true);
reviewContext.timetableReview.classes.set("?0","1 Amanah");
reviewFields.children=[];
reviewContext.renderTimetableTimes();
skip=reviewFields.children[0].children.at(-1).children[0];
assert.equal(skip.checked,false);
assert.equal(skip.disabled,false);
