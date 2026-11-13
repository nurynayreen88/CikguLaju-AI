const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

class Control {
  constructor(tag = "") {
    this.tag = tag;
    this.value = "";
    this.children = [];
    this.events = {};
    this.dataset = {};
  }
  addEventListener(type, callback) { this.events[type] = callback; }
  append(...children) {
    for (const child of children) {
      if (child instanceof Control) child.parentElement = this;
      this.children.push(child);
    }
  }
  prepend(...children) {
    for (const child of children) if (child instanceof Control) child.parentElement = this;
    this.children.unshift(...children);
  }
  replaceChildren(...children) { this.children = [];this.append(...children); }
  add(option) { if (!this.children.length) this.value = option.value;this.append(option); }
  focus() { this.focused = true; }
  scrollIntoView() {}
  get options() { return this.children; }
  get lastElementChild() { return this.children.at(-1); }
  matches(selector) {
    if (selector === "[data-id]") return Boolean(this.dataset.id);
    const field = /^\[data-field="([^"]+)"\]$/.exec(selector);
    return field ? this.dataset.field === field[1] : this.tag === selector;
  }
  closest(selector) { return this.matches(selector) ? this : this.parentElement?.closest(selector); }
  querySelectorAll(selector) {
    return this.children.filter(child => child instanceof Control)
      .flatMap(child => [...(child.matches(selector) ? [child] : []),...child.querySelectorAll(selector)]);
  }
  querySelector(selector) { return this.querySelectorAll(selector)[0]; }
}

const pbd = fs.readFileSync("web_v1_static_preview/pbd.js", "utf8");
const html = fs.readFileSync("web_v1_static_preview/index.html", "utf8");
const controls = Object.fromEntries([...html.matchAll(/id="(pbd-[^"]+)"/g)]
  .map(([,id]) => [id, new Control()]));
const field = id => controls["pbd-" + id];
for (const id of ["bulk-criterion","student-filter"]) {
  field(id).append(new Control("option"),new Control("option"),new Control("option"));
}
const students = [{id:"saved-id",name:"Murid Sedia Ada",code:"Q01"}];
const requests = [];
let confirmation = false, view = "", rosterError = false, savedRecord = null;
const runtime = {
  window:{confirm:() => confirmation},
  document:{getElementById:id => controls[id],createElement:tag => new Control(tag)},
  showWebView:next => {view = next;},
  Option:class { constructor(text,value) {Object.assign(this,{text,value});} },
  File,FormData,URLSearchParams,crypto:require("node:crypto").webcrypto,
  async fetch(url,options) {
    const route = new URL(url,"https://example.invalid");
    const query = route.searchParams;
    const reply = (data,ok = true) => ({ok,json:async () => data});
    requests.push([route.pathname,query.get("class"),query.get("year"),options.method]);
    if (route.pathname.endsWith("/classes")) return reply({classes:["3 Amanah","3 Bestari"]});
    if (route.pathname.endsWith("/records")) {
      if (options.method === "POST") {
        savedRecord = JSON.parse(options.body);
        return reply({version:"record-v1"});
      }
      return reply({error:"Gangguan sejarah"},false);
    }
    if (route.pathname.endsWith("/import")) {
      const csv = await options.body.get("file").text();
      assert.equal(csv, 'Nama Murid,Kod Murid\n"Murid Sedia Ada","Q01"\n"Murid ""Contoh"", A","Q02"');
      return reply({students:[{name:"Murid Sedia Ada",code:"Q01"},{name:'Murid "Contoh", A',code:"Q02"}]});
    }
    assert.ok(route.pathname.endsWith("/roster"));
    if (rosterError) return reply({error:"Gangguan senarai"},false);
    if (options.method === "PUT") {
      const body = JSON.parse(options.body);
      assert.equal(body.version,"v1");
      assert.equal(body.students[0].id,"saved-id");
      assert.equal(body.students[1].name,'Murid "Contoh", A');
      return reply({students:body.students.map((row,i) => ({...row,id:row.id||"new-"+i})),version:"v2"});
    }
    return reply({students:structuredClone(students),version:"v1"});
  },
};
vm.runInNewContext(pbd,runtime);
const settle = () => new Promise(resolve => setImmediate(resolve));
const click = async id => {field(id).events.click();await settle();};

(async () => {
  assert.match(html,/cikgulajuPbdOpenRoster\?\.\(teacherClass\.value,rphSchoolYear\(\)\)/);
  runtime.window.cikgulajuPbdOpenRoster("3 Amanah","2027");
  await settle();
  assert.equal(view,"pbd");
  assert.equal(field("work").hidden,false);
  assert.equal(field("roster").open,true);
  assert.equal(field("roster-summary").focused,true);
  assert.equal(field("roster-summary").textContent,"Senarai murid (1)");
  assert.equal(field("scope").textContent,"3 Amanah · 2027");
  assert.ok(requests.some(req => req[0].endsWith("/roster") && req[1] === "3 Amanah" && req[2] === "2027"));
  const calls = requests.length;
  field("paste-input").value = "Nama Murid\tNo Kad Pengenalan\nMurid Contoh\t001234567890";
  await click("paste-preview");
  assert.match(field("message").textContent,/lajur Nama Murid dan Kod Murid/);
  assert.equal(requests.length,calls);
  field("paste-input").value = 'Nama Murid\tKod Murid (Pilihan)\r\nMurid Sedia Ada\tQ01\r\nMurid "Contoh", A\tQ02';
  await click("paste-preview");
  assert.equal(field("roster-summary").textContent,"Senarai murid (2) · Belum disimpan");
  assert.ok(!requests.some(req => req[3] === "PUT"));
  runtime.window.cikgulajuPbdOpenRoster("3 Bestari","2027");
  runtime.window.cikgulajuPbdOpenRoster("3 Amanah","2027");
  await settle();
  assert.equal(field("scope").textContent,"3 Amanah · 2027");
  assert.equal(field("roster-summary").textContent,"Senarai murid (2) · Belum disimpan");
  await click("save-roster");
  assert.equal(field("roster-summary").textContent,"Senarai murid (2)");
  assert.equal(field("message").textContent,"2 murid disimpan untuk 3 Amanah (2027).");
  confirmation = true;
  rosterError = true;
  runtime.window.cikgulajuPbdOpenRoster("3 Bestari","2026");
  await settle();
  assert.equal(field("class").value,"3 Amanah");
  assert.equal(field("year").value,"2027");
  assert.equal(field("roster-summary").textContent,"Senarai murid (2)");
  console.log("PBD roster: paste preview, duplicate detection, explicit save, class shortcut, and error recovery passed.");

  await click("new");
  const [first, second] = field("entry-rows").children;
  const rowField = (row,key) => row.querySelector('[data-field="' + key + '"]');
  const search = value => {field("student-search").value = value;field("student-search").events.input();};
  const filter = value => {field("student-filter").value = value;field("student-filter").events.change();};
  const selectVisible = () => {field("select-visible").checked = true;field("select-visible").events.change();};
  assert.equal(field("apply").disabled,true);
  selectVisible();
  search("q02");
  assert.equal(first.hidden,true);
  assert.equal(rowField(first,"selected").checked,false);
  assert.match(field("student-summary").textContent,/1 daripada 2 murid dipaparkan/);
  field("bulk-status").value = "Boleh sendiri";
  field("bulk-criterion").value = "status1";
  await click("apply");
  assert.equal(rowField(first,"status1").value,"Belum dinilai");
  assert.equal(rowField(second,"status1").value,"Boleh sendiri");
  assert.equal(savedRecord,null);
  search("");
  filter("pending");
  assert.equal(first.hidden,false);
  assert.equal(second.hidden,true);
  field("criteria2").value = "Kriteria tambahan";
  field("criteria2").events.input();
  assert.equal(second.hidden,false);
  search("Murid Sedia");
  assert.equal(first.hidden,false);
  assert.equal(second.hidden,true);
  field("editor").events.submit({preventDefault(){}});
  await settle();
  assert.equal(savedRecord.entries.length,2);
  assert.equal(savedRecord.entries[1].status1,"Boleh sendiri");
  assert.equal(field("bulk-result").hidden,true);

  await click("report");
  assert.equal(field("bulk").hidden,true);
  assert.equal(field("entry-rows").querySelectorAll('[data-field="selected"]').length,0);
  assert.equal(field("student-filter").options[1].textContent,"TP belum diisi");
  filter("pending");
  const [reportFirst,reportSecond] = field("entry-rows").children;
  const tp = rowField(reportFirst,"tp");
  tp.value = "TP4";
  field("entry-rows").events.change({target:tp});
  assert.equal(reportFirst.hidden,true);
  assert.equal(reportSecond.hidden,false);
  console.log("PBD assessment: visible-only bulk edits, pending filter, full save, and TP filter passed.");
})().catch(error => {console.error(error);process.exitCode = 1;});
