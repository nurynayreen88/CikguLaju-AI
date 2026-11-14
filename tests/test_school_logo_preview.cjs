const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const script = fs.readFileSync("web_v1_static_preview/teacher-profile.js", "utf8");
const methods = script.slice(script.indexOf("function savedLogoSchoolCode()"),
  script.indexOf("async function saveCandidateLogoToPrivateStorage"));
const selectHandler = script.slice(script.indexOf('schoolChoiceField.addEventListener("change",'),
  script.indexOf("async function loadTeacherProfile()"));
const requests = [];
const revoked = [];
const classes = new Set();
const schoolLogoSelectionImage = {
  hidden: true,
  parentElement: {classList: {add: name => classes.add(name), remove: name => classes.delete(name)}},
  decode: async () => {},
  removeAttribute() { delete this.src; },
};
const schoolChoiceField = {
  value: "",
  addEventListener(event, handler) { this[event] = handler; },
};
const state = {loaded: true, savedProfile: JSON.stringify({school_code: "KBA4015"})};
const context = {
  AbortController, URLSearchParams, schoolChoiceField, schoolLogoSelectionImage,
  schoolLogoFile: {files: []}, schoolLogoAutoButton: {}, schoolLogoSelectionStatus: {hidden: true},
  schoolNameField: {}, schoolPickerNotice: {},
  schoolCatalogOptions: [{value: "KBA4016", label: "SEKOLAH KEBANGSAAN PADANG PERAHU"},
                         {value: "KBA4017", label: "SEKOLAH UJIAN"}],
  schoolLogoSelectionUrl: null, schoolLogoSelectionRequest: null,
  teacherProfileState: state, document: {getElementById: () => schoolChoiceField},
  URL: {createObjectURL: blob => "blob:" + blob.id, revokeObjectURL: url => revoked.push(url)},
  fetch: (path, options) => new Promise(resolve => requests.push({path, options, resolve})),
};
vm.runInNewContext(methods + selectHandler, context);

const png = id => ({ok: true, blob: async () => ({type: "image/png", size: 20, id})});
const settle = () => new Promise(resolve => setImmediate(resolve));

(async () => {
  schoolChoiceField.value = "KBA4016";
  schoolChoiceField.change();
  assert.equal(context.schoolLogoAutoButton.disabled, false);
  assert.equal(context.schoolLogoAutoButton.textContent, "Lihat Logo Sekolah");
  assert.equal(requests[0].path, "/api/web/teacher/school-logo-preview?school_code=KBA4016");
  assert.equal(requests[0].options.method, undefined);

  schoolChoiceField.value = "KBA4017";
  schoolChoiceField.change();
  assert.equal(requests[0].options.signal.aborted, true);
  requests[1].resolve(png("KBA4017"));
  await settle();
  assert.equal(schoolLogoSelectionImage.src, "blob:KBA4017");
  assert.equal(schoolLogoSelectionImage.hidden, false);
  assert.ok(classes.has("is-candidate"));
  requests[0].resolve(png("KBA4016"));
  await settle();
  assert.equal(schoolLogoSelectionImage.src, "blob:KBA4017");

  schoolChoiceField.value = "KBA4016";
  schoolChoiceField.change();
  requests[2].resolve({status: 404});
  await settle();
  assert.equal(schoolLogoSelectionImage.hidden, true);
  assert.equal(classes.has("is-candidate"), true);
  assert.ok(revoked.includes("blob:KBA4017"));
  assert.match(context.schoolLogoSelectionStatus.textContent, /belum tersedia/);
  assert.equal(state.savedProfile, JSON.stringify({school_code: "KBA4015"}));

  schoolChoiceField.value = "KBA4015";
  schoolChoiceField.change();
  assert.equal(context.schoolLogoAutoButton.textContent, "Ambil Logo Automatik");
  assert.equal(classes.has("is-candidate"), false);
  assert.equal(requests.length, 3);
})().catch(error => { console.error(error); process.exitCode = 1; });
