"use strict";
// Pure UI-state regression; no web login, network request, Supabase or credit mutation.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const source = fs.readFileSync("web_v1_static_preview/rph-today.js", "utf8");
const start = source.indexOf(" function includedChoices(){");
const end = source.indexOf(" function clearResults(){", start);
assert.ok(start > -1 && end > start, "Expected isolated updateAll function");
const body = source.slice(start, end);
assert.ok(!/\b(fetch|credit|debit|localStorage)\s*\(/.test(body),
  "Status indicator must not make network, credit, or browser storage calls");

function slot(class_name, subject, date) {
  return {
    slot: {can_prepare: true, class_name, subject},
    date,
    busy: false,
    message: {textContent: ""},
    controls: {lesson: {value: "", hidden: false,
      dataset: {ready: "1", hasOptions: "1"}, disabled: false}},
  };
}
const a = slot("4 Bestari", "Matematik", "2027-01-04");
const b = slot("5 Amanah", "Sains", "2027-01-05");
const ctx = {
  choices: [], loading: false, reviewing: false, weekly: false,
  bundleBusy: false, singleDownloads: 0, savingProgress: false,
  noPdpDates: new Set(), weekSlotCount: {textContent: ""},
  list: {querySelectorAll: () => []}, confirmWrap: {hidden: true},
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
ctx.noPdpDates.add(a.date);
update();
assert.equal(ctx.weekSlotCount.textContent, "1");
ctx.noPdpDates.add(b.date);
update();
assert.equal(ctx.confirmWrap.hidden, true);
assert.equal(ctx.generateAll.disabled, true);
assert.equal(ctx.weekSlotCount.textContent, "0");
ctx.noPdpDates.clear();
ctx.choices = [{slot: {can_prepare: false}, controls: {}}];
ctx.resultsHost.hidden = true;
update();
assert.equal(ctx.generateAll.disabled, true);
assert.match(ctx.allStatus.textContent, /Tiada slot dengan bahan disahkan/);
console.log("RPH_HARI_INI_SELECTION_PROGRESS: PASS (no API, no quota, unchanged flow)");

const labelFunctions = source.slice(source.indexOf(" function lessonPickerLabel("),
  source.indexOf(" const summaryStatus="));
vm.runInNewContext(labelFunctions, ctx);
assert.equal(ctx.lessonPickerLabel("SCIENCE_DLP"), "Lesson");
assert.equal(ctx.nativeLessonLabel({label: "Lesson 46 • Sources of Basic Materials",
  textbook_ref: "Textbook pp. 142–144"}, "SCIENCE_DLP"),
  "Lesson 46 • Sources of Basic Materials • Textbook pp. 142–144");
assert.equal(ctx.nativeLessonLabel({label: "Review 08 • Materials Review"}, "SCIENCE_DLP"),
  "Review 08 • Materials Review");
assert.equal(ctx.nativeLessonLabel({label: "Review 08 • Materials Review"}, "SCIENCE"), "");
assert.equal(ctx.nativeLessonLabel({label: "Review 11 • Unknown review"}, "SCIENCE_DLP"), "");

const initialize = source.slice(source.indexOf(" async function initialize("),
  source.indexOf(" function makeChoice("));
const selected = [];
const requested = [];
Object.assign(ctx, {
  requestId: 3, updateAll: () => {},
  advance: async (choice, step) => selected.push([choice.slot.subject_code, step]),
  sourceOptions: async (...args) => { requested.push(args); return [{value: "SCIENCE"}]; },
});
vm.runInNewContext(initialize, ctx);
(async () => {
  for (const [subject_code, curriculum] of [["SCIENCE_DLP", "dlp"], ["SCIENCE", "kssr"]]) {
    const choice = {slot: {year: 4, subject_code, curriculum},
      message: {textContent: ""}, ticket: 3};
    await ctx.initialize(choice);
    assert.equal(choice.busy, false);
  }
  assert.deepEqual(selected, [["SCIENCE_DLP", "subject"], ["SCIENCE", "subject"]]);
  assert.equal(requested.length, 1);
  assert.equal(requested[0][1], "subjects");
})().catch(error => { console.error(error); process.exitCode = 1; });
