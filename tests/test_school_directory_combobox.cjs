const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const script = fs.readFileSync("web_v1_static_preview/teacher-profile.js", "utf8");
const code = script.slice(script.indexOf("const schoolSelectData="),
  script.indexOf("async function getSchoolChoices("));
class Element {
  constructor() {
    this.attributes = {};
    this.events = {};
    this.children = [];
    this.dataset = {};
    this.value = "";
    this.classes = new Set();
    this.classList = {add: name => this.classes.add(name), remove: name => this.classes.delete(name)};
  }
  get options() { return this.children; }
  get selectedOptions() { return this.children.filter(child => child.value === this.value); }
  setAttribute(name, value) { this.attributes[name] = value; }
  removeAttribute(name) { delete this.attributes[name]; }
  add(child) { this.children.push(child); }
  replaceChildren(...children) { this.children = children; }
  addEventListener(type, callback) { this.events[type] = callback; }
  dispatchEvent(event) { this.events[event.type]?.(event); }
  scrollIntoView() {}
  closest() { return this.attributes.role === "option" ? this : null; }
}
const elements = new Map();
function picker(id) {
  const control = Object.assign(new Element(), {id});
  const input = Object.assign(new Element(), {id: id + "-input", parentElement: new Element()});
  const list = Object.assign(new Element(), {id: id + "-list", parentElement: new Element()});
  const empty = new Element();
  list.parentElement.querySelector = () => empty;
  for (const element of [control, input, list, {id: id + "-label"}]) {
    elements.set(element.id, element);
  }
  return {control, input, list, empty, menu: list.parentElement};
}
const state = picker("profile-state");
const ppd = picker("profile-district");
const school = picker("profile-school-choice");
const runtime = {
  schoolStateField: state.control, schoolDistrictField: ppd.control, schoolChoiceField: school.control,
  document: {getElementById: id => elements.get(id), createElement: () => new Element()},
  Option: class { constructor(textContent, value) { Object.assign(this, {textContent, value}); } },
  Event: class { constructor(type) { this.type = type; } },
};
vm.runInNewContext(code + "\nthis.populate = populateSchoolSelect;", runtime);
const populate = (picker, placeholder, rows, saved) => runtime.populate(picker.control, placeholder, rows, saved);
const type = (picker, value) => {
  picker.input.value = value;
  picker.input.dispatchEvent({type: "input"});
};
const key = (picker, key) => picker.input.dispatchEvent({type: "keydown", key, preventDefault() {}});
const labels = picker => picker.list.children.map(row => row.textContent);
const click = (picker, target) => picker.list.dispatchEvent({type: "click", target});

populate(state, "Pilih negeri", [{label: "KUALA LUMPUR", value: "Kuala Lumpur"},
                                {label: "KEDAH", value: "Kedah"}]);
populate(ppd, "Pilih negeri dahulu", []);
populate(school, "Pilih PPD dahulu", []);
assert.equal(state.control.hidden, true);
assert.equal(ppd.input.disabled, true);
assert.equal(school.input.disabled, true);
state.input.dispatchEvent({type: "click"});
assert.deepEqual(labels(state), ["KUALA LUMPUR", "KEDAH"]);
assert.equal(state.input.attributes["aria-expanded"], "true");
type(state, "kl");
assert.deepEqual(labels(state), ["KUALA LUMPUR"]);
key(state, "Enter");
assert.equal(state.control.value, "Kuala Lumpur");
assert.equal(state.input.value, "KUALA LUMPUR");
assert.equal(state.menu.hidden, true);

state.control.addEventListener("change", () => populate(ppd, "Pilih PPD",
  [{label: "PPD KUBANG PASU", value: "PPD KUBANG PASU"},
   {label: "PPD KOTA SETAR", value: "PPD KOTA SETAR"}]));
ppd.control.addEventListener("change", () => populate(school, "Pilih sekolah",
  [{label: "SEKOLAH KEBANGSAAN PADANG PERAHU", value: "KBA4016"},
   {label: "SEKOLAH KEBANGSAAN SINTOK", value: "KBA4020"}]));
state.input.dispatchEvent({type: "click"});
type(state, "ked");
click(state, state.list.children[0]);
assert.equal(state.control.value, "Kedah");
ppd.input.dispatchEvent({type: "focus"});
type(ppd, "pasu kubang");
key(ppd, "ArrowDown");
assert.equal(ppd.input.attributes["aria-activedescendant"], "profile-district-list-0");
key(ppd, "Enter");
assert.equal(ppd.control.value, "PPD KUBANG PASU");
school.input.dispatchEvent({type: "click"});
type(school, "kba4016");
assert.deepEqual(labels(school), ["SEKOLAH KEBANGSAAN PADANG PERAHU (KBA4016)"]);
click(school, school.list.children[0]);
assert.equal(school.control.value, "KBA4016");
school.input.dispatchEvent({type: "click"});
type(school, "SK Sintok");
assert.deepEqual(labels(school), ["SEKOLAH KEBANGSAAN SINTOK (KBA4020)"]);
type(school, "tiada");
assert.equal(school.empty.hidden, false);
key(school, "Escape");
assert.equal(school.control.value, "KBA4016");
assert.match(school.input.value, /PADANG PERAHU/);
assert.equal(school.menu.hidden, true);
populate(school, "Pilih PPD dahulu", []);
assert.equal(school.input.disabled, true);
assert.equal(school.control.value, "");
