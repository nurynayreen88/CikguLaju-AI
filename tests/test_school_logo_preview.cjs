const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const script = fs.readFileSync("web_v1_static_preview/teacher-profile.js", "utf8");
const processor = script.slice(script.indexOf("const schoolLogoCatalogSize="),
  script.indexOf("// Only a SAVED school code"));
const methods = script.slice(script.indexOf("function savedLogoSchoolCode()"),
  script.indexOf("async function importSavedSchoolLogo"));
const selectHandler = script.slice(script.indexOf('schoolChoiceField.addEventListener("change",'),
  script.indexOf("async function loadTeacherProfile()"));
const profileHandler = script.slice(script.indexOf('profileForm.addEventListener("submit",'),
  script.indexOf('timetableAddButton.addEventListener("click",'));
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
const profileForm = {addEventListener(_event, handler) { this.save = handler; }};
const profileMessage = {};
const stored = new Map();
const drawCalls = [];
const canvas = {
  getContext: () => ({
    clearRect() {},
    drawImage: (_picture, ...box) => drawCalls.push(box),
  }),
  toBlob: callback => callback({
    type: "image/png", size: 20, id: currentImage.id,
    width: canvas.width, height: canvas.height,
  }),
};
let currentImage;
const context = {
  AbortController, URLSearchParams, schoolChoiceField, schoolLogoSelectionImage,
  schoolLogoFile: {files: []}, schoolLogoAutoButton: {}, schoolLogoSelectionStatus: {hidden: true},
  profileForm, profileMessage, schoolLogoUpload: {}, profileSaveButton: {}, schoolLogoStatus:{},
  profileSaving: false, schoolLogoSaving: false, timetableImportSaving: false,
  pendingSchoolLogoCode: "", schoolLogoSelection: null,
  clearStoredSchoolLogo: () => {},
  loadSchoolLogo: async () => { context.displayedLogo=stored.get(JSON.parse(state.savedProfile).school_code); },
  validSchoolLogoFile: file => file?.type==="image/png",
  teacherClassLines: () => ["4 Amanah"],
  profileEditorData: () => ({school_code:schoolChoiceField.value}),
  teacherApi: async (_path,_method,body) => {
    context.profileSchoolCode=body.school_code;
    return {saved:true, version:"new version"};
  },
  renderProfileReadiness(){}, setTeacherIdentity(){}, renderTeacherTimetable(){}, timetableValueRows(){},
  FormData: class extends Map { append(key, value) { this.set(key,value); } },
  schoolNameField: {}, schoolPickerNotice: {},
  schoolCatalogOptions: [{value: "KBA4016", label: "SEKOLAH KEBANGSAAN PADANG PERAHU"},
                         {value: "KBA4017", label: "SEKOLAH UJIAN"}],
  schoolLogoSelectionUrl: null, schoolLogoSelectionRequest: null,
  teacherProfileState: state,
  document: {getElementById: () => schoolChoiceField, createElement: () => canvas},
  Image: class {
    set src(value) { this.id = value.slice(5); }
    async decode() {
      this.width = 100;
      this.height = 200;
      currentImage = this;
    }
  },
  URL: {createObjectURL: blob => "blob:" + blob.id, revokeObjectURL: url => revoked.push(url)},
  fetch: (path, options) => new Promise(resolve => requests.push({path, options, resolve})),
};
vm.runInNewContext(processor + methods + selectHandler + profileHandler, context);

const png = (id, saved=false) => ({ok: true, headers:{get:()=>saved?"1":null},
  blob: async () => ({type: "image/png", size: 20, id})});
const settle = () => new Promise(resolve => setImmediate(resolve));
const submit = () => profileForm.save({preventDefault(){}});

function finishUpload(request, success=true) {
  assert.equal(request.path,"/api/web/teacher/school-logo");
  assert.equal(request.options.method,"POST");
  const {body}=request.options;
  const code=body.get("school_code");
  assert.equal(code,context.profileSchoolCode);
  assert.equal(body.get("automatic"),"1");
  assert.equal(body.get("logo").id,code);
  if(success)stored.set(code,body.get("logo"));
  request.resolve({ok:success, json:async()=>success?{saved:true}:{error:"Storan tidak tersedia."}});
}

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
  assert.deepEqual(drawCalls.at(-1), [128, 0, 256, 512]);
  const fitted = await context.schoolLogoToPng({id: "small"}, {catalog: true});
  assert.equal(fitted.width, 512);
  assert.equal(fitted.height, 512);
  const manual = await context.schoolLogoToPng({id: "manual"});
  assert.equal(manual.width, 100);
  assert.equal(manual.height, 200);
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

  // Saving before the preview returns still applies the matching school logo.
  schoolChoiceField.value = "KBA4016";
  schoolChoiceField.change();
  const saving=submit();
  assert.equal(context.profileSaveButton.disabled,true);
  await settle();
  assert.equal(requests.length,4);
  requests[3].resolve(png("KBA4016"));
  await settle();
  finishUpload(requests[4]);
  await saving;
  assert.equal(context.displayedLogo.id,"KBA4016");
  assert.equal(requests.length,5);

  // A custom logo already associated with another school is reused.
  stored.set("KBA4017",{id:"manual KBA4017"});
  schoolChoiceField.value = "KBA4017";
  schoolChoiceField.change();
  requests[5].resolve(png("manual KBA4017",true));
  await submit();
  assert.equal(context.displayedLogo.id,"manual KBA4017");
  assert.equal(requests.length,6);

  // A failed second write can be retried by pressing the same Save button.
  schoolChoiceField.value = "KBA4016";
  schoolChoiceField.change();
  requests[6].resolve(png("KBA4016"));
  const failure=submit();
  await settle();
  finishUpload(requests[7],false);
  await failure;
  assert.match(profileMessage.textContent,/cuba lagi/);
  const retry=submit();
  await settle();
  requests[8].resolve(png("KBA4016"));
  await settle();
  finishUpload(requests[9]);
  await retry;
  assert.equal(context.displayedLogo.id,"KBA4016");
})().catch(error => { console.error(error); process.exitCode = 1; });
