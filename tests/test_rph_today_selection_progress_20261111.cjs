"use strict";
// Pure UI-state regression; no web login, network request, Supabase or credit mutation.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync("web_v1_static_preview/rph-today.js", "utf8");
const start = source.indexOf(" function updateAll(){");
const end = source.indexOf(" function clearResults(){", start);
assert.ok(start > -1 && end > start, "Expected isolated updateAll function");
const body = source.slice(start, end);
assert.ok(!/\b(fetch|credit|debit|localStorage)\s*\(/.test(body),
  "Status indicator must not make network, credit, or browser storage calls");

function slot(class_name, subject) {
  return {
    slot: {can_prepare: true, class_name, subject},
    busy: false,
    message: {textContent: ""},
    controls: {lesson: {value: "", hidden: false,
      dataset: {ready: "1", hasOptions: "1"}, disabled: false}},
  };
}
const a = slot("4 Bestari", "Matematik");
const b = slot("5 Amanah", "Sains");
const ctx = {
  choices: [], loading: false, reviewing: false,
  confirm: {checked: false}, generateAll: {disabled: true},
  resultsHost: {hidden: true}, allStatus: {textContent: ""},
  TAGS: ["component", "theme", "unit", "topic", "lesson"],
};
vm.runInNewContext(body + "\nthis.updateAll = updateAll;", ctx);
const update = () => ctx.updateAll();

update();
assert.equal(ctx.generateAll.disabled, true);
assert.equal(ctx.allStatus.textContent, "");

ctx.choices = [a, b];
update();
assert.equal(ctx.generateAll.disabled, true);
assert.match(ctx.allStatus.textContent, /0 daripada 2 slot lengkap/);
assert.match(ctx.allStatus.textContent, /4 Bestari \(Matematik\)/);

a.controls.lesson.value = "MT4-PDP-012";
update();
assert.match(ctx.allStatus.textContent, /1 daripada 2 slot lengkap/);
assert.match(ctx.allStatus.textContent, /5 Amanah \(Sains\)/);

b.message.textContent = "Katalog utama belum tersedia.";
b.controls.lesson.dataset.hasOptions = "";
update();
assert.match(ctx.allStatus.textContent, /Semak pilihan sumber/);

b.message.textContent = "";
b.controls.lesson.dataset.hasOptions = "1";
b.controls.lesson.value = "SN5-PDP-022";
update();
assert.equal(ctx.generateAll.disabled, true);
assert.match(ctx.allStatus.textContent, /Sahkan hari PdP sebenar/);

ctx.confirm.checked = true;
update();
assert.equal(ctx.generateAll.disabled, false);
assert.match(ctx.allStatus.textContent, /Tekan Jana Bahan Semua Lesson/);

a.busy = true;
update();
assert.equal(ctx.generateAll.disabled, true);
assert.match(ctx.allStatus.textContent, /Sedang menyemak pilihan kurikulum/);
a.busy = false;

ctx.allStatus.textContent = "Menyemak bahan bagi dua kelas";
ctx.resultsHost.hidden = false;
update();
assert.equal(ctx.allStatus.textContent, "Menyemak bahan bagi dua kelas",
  "Do not overwrite real batch results or errors");
ctx.resultsHost.hidden = true;
ctx.reviewing = true;
update();
assert.equal(ctx.generateAll.disabled, true);
assert.equal(ctx.allStatus.textContent, "Menyemak bahan bagi dua kelas");

ctx.reviewing = false;
ctx.choices = [{slot: {can_prepare: false}, controls: {}}];
ctx.resultsHost.hidden = true;
update();
assert.equal(ctx.generateAll.disabled, true);
assert.match(ctx.allStatus.textContent, /Tiada slot dengan bahan disahkan/);
console.log("RPH_HARI_INI_SELECTION_PROGRESS: PASS (no API, no quota, unchanged flow)");
