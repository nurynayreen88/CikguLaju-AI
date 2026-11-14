"use strict";
/* Editable teacher profile and weekly timetable.
   The browser never sees service keys or chooses a Telegram user ID. */
const teacherProfileState = {
  loaded: false, profileVersion: "", timetableVersion: "",
  classNames: [], savedPeriods: 0, savedProfile: null, savedTimetable: null,
  classAliases: {},
};
const teacherDays = ["Isnin","Selasa","Rabu","Khamis","Jumaat","Sabtu","Ahad"];
// Full, source-compatible names so RPH Hari Ini can match a saved period.
// Previously the subject was a datalist text field: difficult to scroll and
// inconsistent between mobile browsers. Keep legacy/custom values losslessly.
const teacherSubjectGroups = [
  { label:"Subjek utama", values:[
    "Bahasa Melayu","English","Matematik","Sains","Pendidikan Islam"
  ]},
  { label:"Subjek sekolah rendah lain", values:[
    "Pendidikan Moral","Pendidikan Seni Visual","Pendidikan Muzik",
    "Pendidikan Jasmani","Pendidikan Kesihatan","Pendidikan Jasmani dan Pendidikan Kesihatan",
    "Bahasa Arab","Sejarah","Reka Bentuk dan Teknologi"
  ]},
  { label:"Waktu bukan PdP", values:[
    "Rehat","Perhimpunan","Kokurikulum"
  ]},
];
const subjectNames = new Set(teacherSubjectGroups.flatMap(group => group.values));
const timetableOtherSubject = "__cikgulaju_custom_subject__";
const profileForm = document.getElementById("teacher-profile-form");
const teacherNameField = document.getElementById("profile-name");
function uppercaseTeacherName() {
  // Uppercase while typing, pasting and autofill without moving the caret.
  const original = teacherNameField.value;
  const uppercase = original.toLocaleUpperCase("ms-MY");
  if (original === uppercase) return;
  const start = teacherNameField.selectionStart;
  const end = teacherNameField.selectionEnd;
  teacherNameField.value = uppercase;
  if (start !== null && end !== null) {
    teacherNameField.setSelectionRange(
      original.slice(0,start).toLocaleUpperCase("ms-MY").length,
      original.slice(0,end).toLocaleUpperCase("ms-MY").length,
    );
  }
}
teacherNameField.addEventListener("input", uppercaseTeacherName);
teacherNameField.addEventListener("change", uppercaseTeacherName);
const timetableBody = document.getElementById("timetable-rows");
const profileSetupStatus = document.getElementById("profile-setup-status");
const profileSetupNext = document.getElementById("profile-setup-next");

function savedProfileReadiness() {
  if (!teacherProfileState.loaded || !teacherProfileState.savedProfile) return null;
  let saved;
  try { saved=JSON.parse(teacherProfileState.savedProfile); }
  catch (_err) { return null; }
  const checks=[
    {label:"Nama Guru",ready:Boolean(teacherProfileState.profileVersion &&
      saved.display_name && saved.display_name.trim()),target:teacherNameField},
    {label:"Sekolah",ready:Boolean(saved.school_code &&
      saved.state_name && saved.district_name),target:
      !schoolStateField.value ? schoolStateField :
      !schoolDistrictField.value ? schoolDistrictField : schoolChoiceField},
    {label:"Kelas",ready:Array.isArray(saved.class_names) &&
      saved.class_names.length>0,target:document.getElementById("profile-classes")},
    {label:"Jadual Hari Ini",ready:teacherProfileState.savedPeriods>0,
      target:timetableAddButton},
  ];
  return checks;
}

function renderProfileReadiness() {
  const checks=savedProfileReadiness();
  if (!checks) {
    profileSetupStatus.textContent="Maklumat persediaan belum tersedia. Tekan Refresh Profil.";
    profileSetupNext.disabled=true;
    return;
  }
  const done=checks.filter(check=>check.ready).length;
  const next=checks.find(check=>!check.ready);
  profileSetupStatus.textContent="Persediaan "+done+"/4: "+
    checks.map(check=>(check.ready?"✓ ":"○ ")+check.label).join(" · ")+
    (next ? ". Langkah seterusnya: "+next.label+"." : ". Semua maklumat asas sudah tersedia.");
  profileSetupNext.disabled=!next;
  profileSetupNext.hidden=!next;
}

profileSetupNext.addEventListener("click",()=>{
  const next=savedProfileReadiness()?.find(check=>!check.ready);
  if (!next || !next.target || next.target.disabled) return;
  const target=schoolCombos.get(next.target)?.input||next.target;
  target.scrollIntoView({block:"center",behavior:"smooth"});
  target.focus({preventScroll:true});
});

const profileMessage = document.getElementById("profile-save-status");
const timetableMessage = document.getElementById("timetable-save-status");
const profileSaveButton = document.getElementById("profile-save");
const timetableSaveButton = document.getElementById("timetable-save");
const timetableAddButton = document.getElementById("timetable-add");
const timetableReader = document.getElementById("timetable-reader");
const timetableReaderFile = document.getElementById("timetable-reader-file");
const timetableReaderStart = document.getElementById("timetable-reader-start");
const timetableReaderStatus = document.getElementById("timetable-reader-status");
const timetableReaderReview = document.getElementById("timetable-reader-review");
const timetableReaderTitle = document.getElementById("timetable-reader-review-title");
const timetableReaderNote = document.getElementById("timetable-reader-review-note");
const timetableReaderFields = document.getElementById("timetable-reader-fields");
const timetableReaderPreview = document.getElementById("timetable-reader-preview");
const timetableReaderReportRows = document.getElementById("timetable-reader-report-rows");
const timetableReaderUnclear = document.getElementById("timetable-reader-unclear");
const timetableReaderUnclearTitle = document.getElementById("timetable-reader-unclear-title");
const timetableReaderUnclearList = document.getElementById("timetable-reader-unclear-list");
const timetableReaderUnclearNote = document.getElementById("timetable-reader-unclear-note");
const timetableReaderNext = document.getElementById("timetable-reader-next");
const timetableReaderBack = document.getElementById("timetable-reader-back");
const timetableReaderDismiss = document.getElementById("timetable-reader-dismiss");
const timetableReaderFeedback = document.getElementById("timetable-reader-feedback");
let timetableReview = null;
let timetableReadRequest = null;
let timetableImportSaving = false;
const schoolLogoFile = document.getElementById("school-logo-file");
const schoolLogoUpload = document.getElementById("school-logo-upload");
const schoolLogoStatus = document.getElementById("school-logo-status");
const schoolLogoPreview = document.getElementById("school-logo-preview");
const schoolLogoPlaceholder = document.getElementById("school-logo-placeholder");
const schoolLogoAutoButton = document.getElementById("school-logo-auto");
const schoolLogoSelectionImage = document.getElementById("school-logo-selection-preview");
const schoolLogoSelectionStatus = document.getElementById("school-logo-selection-status");
let schoolLogoSelectionUrl = null;
let schoolLogoSelectionRequest = null;
let schoolLogoObjectUrl = null;
let schoolLogoPresent = null;
const attemptedAutoLogoCodes = new Set();

function setTeacherIdentity(profile) {
  // Only use the name explicitly saved in the shared teacher profile.
  // Telegram widget usernames are not substitutes for the teacher's name.
  const name = typeof profile?.display_name === "string" && profile.display_name.trim()
    ? profile.display_name.trim().toLocaleUpperCase("ms-MY") : "CIKGU";
  const school = typeof profile?.school_name === "string" && profile.school_name.trim()
    ? profile.school_name.trim() : "Ruang Guru";
  document.getElementById("sidebar-teacher-name").textContent = name;
  document.getElementById("sidebar-school-name").textContent = school;
  document.getElementById("workspace-teacher-name").textContent = name;
}

function setSchoolLogoPreview(blob) {
  if (schoolLogoObjectUrl) URL.revokeObjectURL(schoolLogoObjectUrl);
  schoolLogoObjectUrl = URL.createObjectURL(blob);
  schoolLogoPreview.src = schoolLogoObjectUrl;
  schoolLogoPreview.hidden = false;
  schoolLogoPlaceholder.hidden = true;
}

async function loadSchoolLogo() {
  try {
    const response = await fetch("/api/web/teacher/school-logo", {
      credentials:"same-origin",cache:"no-store",
    });
    if (response.status === 404) {
      if (schoolLogoObjectUrl) URL.revokeObjectURL(schoolLogoObjectUrl);
      schoolLogoObjectUrl = null;
      schoolLogoPreview.hidden = true;
      schoolLogoPreview.removeAttribute("src");
      schoolLogoPlaceholder.hidden = false;
      schoolLogoPresent = false;
      schoolLogoStatus.textContent = "Belum ada logo sekolah. Pilih fail atau gunakan Ambil Logo Automatik.";
      return false;
    }
    if (!response.ok) throw new Error("Logo sekolah tidak dapat dimuatkan.");
    const blob = await response.blob();
    if (blob.type !== "image/png" || blob.size > 460800) throw new Error("Logo tersimpan tidak sah.");
    setSchoolLogoPreview(blob);
    schoolLogoPresent = true;
    schoolLogoStatus.textContent = "Logo tersimpan. Cetakan RPT berlogo memerlukan akses berbayar aktif.";
    return true;
  } catch (error) {
    schoolLogoPresent = null; // unknown: never overwrite on a failed storage lookup
    schoolLogoStatus.textContent = error.message;
    return null;
  }
}

schoolLogoFile.addEventListener("change", () => {
  const file = schoolLogoFile.files?.[0];
  schoolLogoUpload.disabled = !file;
  if (!file) {
    updateAutoLogoButton();
    void previewSelectedSchoolLogo();
    return;
  }
  clearSchoolLogoSelection();
  updateAutoLogoButton();
  if (file.size > 2 * 1024 * 1024 || !["image/png","image/jpeg","image/webp"].includes(file.type)) {
    schoolLogoUpload.disabled = true;
    schoolLogoStatus.textContent = "Pilih imej PNG, JPG atau WebP maksimum 2 MB.";
    return;
  }
  setSchoolLogoPreview(file);
  schoolLogoStatus.textContent = "Pratonton sahaja. Tekan Muat Naik Logo untuk menyimpan.";
});

async function schoolLogoToPng(file) {
  // Canvas removes image metadata and normalizes PNG/JPEG/WebP to a compact,
  // static PNG. Private server accepts PNG only, independently validating it.
  const url=URL.createObjectURL(file),picture=new Image();
  try {
    picture.src=url;
    await picture.decode();
    if (picture.width < 32 || picture.height < 32 ||
        picture.width * picture.height > 12000000)
      throw new Error("Dimensi gambar tidak sah atau terlalu besar.");
    for (const side of [512,420,320,240]) {
      const factor=Math.min(1,side/Math.max(picture.width,picture.height));
      const canvas=document.createElement("canvas");
      canvas.width=Math.max(32,Math.round(picture.width*factor));
      canvas.height=Math.max(32,Math.round(picture.height*factor));
      const ctx=canvas.getContext("2d");
      if (!ctx) throw new Error("Pemprosesan logo tidak tersedia.");
      ctx.clearRect(0,0,canvas.width,canvas.height);
      ctx.drawImage(picture,0,0,canvas.width,canvas.height);
      const png=await new Promise(resolve=>canvas.toBlob(resolve,"image/png"));
      if (png?.type==="image/png" && png.size>0 && png.size<450*1024)
        return png;
    }
    throw new Error("Fail terlalu rumit untuk dijadikan logo. Cuba gambar lebih kecil.");
  } finally {
    URL.revokeObjectURL(url);
  }
}

// Only a SAVED school code can request a logo; unsaved changes do not switch
// the school attached to the user's existing private storan kekal logo object.
function savedLogoSchoolCode() {
  if (!teacherProfileState.loaded || !teacherProfileState.savedProfile) return "";
  let saved;
  try {saved=JSON.parse(teacherProfileState.savedProfile);}catch(_err){return "";}
  const current=document.getElementById("profile-school-choice").value;
  return saved?.school_code && saved.school_code===current ? current : "";
}
function selectedLogoSchoolCode() {
  const code=schoolChoiceField.value;
  return teacherProfileState.loaded && schoolCatalogOptions.some(row=>row.value===code) ? code : "";
}

function updateAutoLogoButton() {
  const saved=savedLogoSchoolCode();
  const preview=selectedLogoSchoolCode()&&!saved;
  schoolLogoAutoButton.textContent=preview?"Lihat Logo Sekolah":"Ambil Logo Automatik";
  schoolLogoAutoButton.disabled=!(saved || (preview && !schoolLogoFile.files?.length));
}

function clearSchoolLogoSelection() {
  schoolLogoSelectionRequest?.abort();
  schoolLogoSelectionRequest=null;
  if(schoolLogoSelectionUrl)URL.revokeObjectURL(schoolLogoSelectionUrl);
  schoolLogoSelectionUrl=null;
  schoolLogoSelectionImage.hidden=true;
  schoolLogoSelectionImage.removeAttribute("src");
  schoolLogoSelectionImage.parentElement.classList.remove("is-candidate");
  schoolLogoSelectionStatus.hidden=true;
  schoolLogoSelectionStatus.textContent="";
}

async function fetchSchoolLogoCandidate(path, signal) {
  const response=await fetch(path,{
    credentials:"same-origin",cache:"no-store",redirect:"error",signal,
  });
  if(response.status===404)throw new Error(
    "Logo automatik belum tersedia untuk sekolah ini. Gunakan Muat Naik Logo.");
  if(!response.ok)throw new Error("Sumber logo sekolah belum dapat dihubungi.");
  const blob=await response.blob();
  if(!["image/png","image/jpeg","image/gif"].includes(blob.type) ||
      blob.size<=0 || blob.size>2*1024*1024)
    throw new Error("Logo daripada sumber tidak sah. Sila muat naik sendiri.");
  return blob;
}

async function previewSelectedSchoolLogo() {
  clearSchoolLogoSelection();
  const code=selectedLogoSchoolCode();
  if(!code || savedLogoSchoolCode() || schoolLogoFile.files?.length)return;
  const request=new AbortController();
  schoolLogoSelectionRequest=request;
  schoolLogoSelectionImage.parentElement.classList.add("is-candidate");
  schoolLogoSelectionStatus.hidden=false;
  schoolLogoSelectionStatus.textContent="Memuatkan logo sekolah yang dipilih…";
  try {
    const query=new URLSearchParams({school_code:code});
    const blob=await fetchSchoolLogoCandidate("/api/web/teacher/school-logo-preview?"+query,request.signal);
    if(request.signal.aborted || selectedLogoSchoolCode()!==code || savedLogoSchoolCode())return;
    schoolLogoSelectionUrl=URL.createObjectURL(blob);
    schoolLogoSelectionImage.src=schoolLogoSelectionUrl;
    await schoolLogoSelectionImage.decode();
    if(request.signal.aborted || selectedLogoSchoolCode()!==code || savedLogoSchoolCode())return;
    schoolLogoSelectionImage.hidden=false;
    schoolLogoSelectionStatus.textContent="Pratonton logo sekolah. Simpan maklumat guru untuk mengesahkan pilihan sekolah.";
  }catch(error){
    if(request.signal.aborted)return;
    clearSchoolLogoSelection();
    schoolLogoSelectionImage.parentElement.classList.add("is-candidate");
    schoolLogoSelectionStatus.hidden=false;
    schoolLogoSelectionStatus.textContent=error.message;
  }
}
async function saveCandidateLogoToPrivateStorage(png) {
  const body=new FormData();
  body.append("logo",png,"logo.png");
  const response=await fetch("/api/web/teacher/school-logo",{
    method:"POST",credentials:"same-origin",cache:"no-store",body,
  });
  const result=await response.json().catch(()=>({}));
  if(!response.ok || result.saved!==true)
    throw new Error(result.error||"Logo tidak berjaya disimpan.");
}
async function importSavedSchoolLogo(automatic=false) {
  const code=savedLogoSchoolCode();
  if(!code || schoolLogoAutoButton.disabled)return;
  if(automatic && attemptedAutoLogoCodes.has(code))return;
  if(automatic && (schoolLogoPresent!==false || schoolLogoFile.files?.length))return;
  if(!automatic && schoolLogoPresent===true &&
     !window.confirm("Logo sekolah sedia ada akan diganti. Teruskan?"))return;
  attemptedAutoLogoCodes.add(code);
  schoolLogoAutoButton.disabled=true;
  schoolLogoStatus.textContent="Mengambil logo sekolah berdasarkan kod sekolah…";
  try {
    const blob=await fetchSchoolLogoCandidate("/api/web/teacher/school-logo-candidate");
    // The browser normalizes metadata, transparency and GIF first frame before
    // the same server-side PNG validation used for manual private uploads.
    const png=await schoolLogoToPng(blob);
    if(savedLogoSchoolCode()!==code)throw new Error(
      "Sekolah berubah semasa logo dimuatkan. Simpan profil dan cuba lagi.");
    // A manual upload may have started or finished during the remote fetch.
    // Never let a background auto-import overwrite that newly supplied logo.
    if(automatic && (schoolLogoPresent===true || schoolLogoFile.files?.length)){
      schoolLogoStatus.textContent="Logo pilihan guru dikekalkan.";
      return;
    }
    await saveCandidateLogoToPrivateStorage(png);
    await loadSchoolLogo();
    schoolLogoStatus.textContent=
      "Logo sekolah berjaya diambil dan disimpan. Sila semak lencana sebelum mencetak RPT.";
  }catch(error){
    schoolLogoStatus.textContent=error.message;
  }finally{
    updateAutoLogoButton();
  }
}
async function refreshLogoAndTryAutomaticImport(schoolChanged=false) {
  const stored=await loadSchoolLogo();
  if(stored===true && schoolChanged)
    schoolLogoStatus.textContent=
      "Sekolah telah ditukar. Logo lama dikekalkan; sila semak dan ganti jika perlu.";
  if(stored===false && savedLogoSchoolCode())await importSavedSchoolLogo(true);
}
schoolLogoAutoButton.addEventListener("click",()=>{
  if(savedLogoSchoolCode())void importSavedSchoolLogo(false);
  else void previewSelectedSchoolLogo();
});

schoolLogoUpload.addEventListener("click", async () => {
  const file = schoolLogoFile.files?.[0];
  if (!file || schoolLogoUpload.disabled) return;
  schoolLogoUpload.disabled = true;
  schoolLogoStatus.textContent = "Memproses dan menyimpan logo sekolah…";
  try {
    const png=await schoolLogoToPng(file);
    const body = new FormData();
    body.append("logo", png, "logo.png");
    const response = await fetch("/api/web/teacher/school-logo", {
      method:"POST",credentials:"same-origin",cache:"no-store",body,
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok || result.saved !== true) throw new Error(
      result.error || "Logo tidak berjaya dimuat naik.");
    schoolLogoFile.value = "";
    updateAutoLogoButton();
    await loadSchoolLogo();
    schoolLogoStatus.textContent = "Logo sekolah berjaya disimpan. Ia dicetak pada RPT hanya jika akses berbayar aktif.";
  } catch (error) {
    schoolLogoStatus.textContent = error.message;
    schoolLogoUpload.disabled = false;
  }
});

function profileEditorData() {
  return {
    display_name: teacherNameField.value.trim().toLocaleUpperCase("ms-MY"),
    school_name: document.getElementById("profile-school").value.trim(),
    state_name: document.getElementById("profile-state").value,
    district_name: document.getElementById("profile-district").value,
    school_code: document.getElementById("profile-school-choice").value,
    class_names: teacherClassLines(),
  };
}
function hasUnsavedTeacherChanges() {
  if (!teacherProfileState.loaded) return false;
  return timetableReview!==null ||
         JSON.stringify(profileEditorData()) !== teacherProfileState.savedProfile ||
         JSON.stringify(timetableValueRows()) !== teacherProfileState.savedTimetable;
}
async function refreshTeacherProfile() {
  if (hasUnsavedTeacherChanges() &&
      !window.confirm("Ada maklumat belum disimpan. Teruskan Refresh?")) return;
  await loadTeacherProfile();
}
document.getElementById("profile-refresh").addEventListener("click", refreshTeacherProfile);
document.querySelector('[data-web-view="account"]').addEventListener("click", () => {
  if (!hasUnsavedTeacherChanges()) loadTeacherProfile();
});
document.querySelector('[data-web-view="rph"]').addEventListener("click", () => {
  if (typeof loadTeacherClasses === "function") loadTeacherClasses();
});

function teacherClassLines() {
  return document.getElementById("profile-classes").value.split(/\r?\n/)
    .map(s => s.trim()).filter(Boolean);
}

function makeTimetableSelect(values, selected, field, placeholder) {
  const select = document.createElement("select");
  select.dataset.field = field;
  if (placeholder) select.add(new Option(placeholder, ""));
  for (const text of values) select.add(new Option(text, text));
  const existing = selected && values.find(value=>value.toLowerCase()===selected.toLowerCase());
  if (selected && !existing) {
    select.add(new Option(selected + " (semak profil)", selected));
  }
  select.value = existing || selected || (placeholder ? "" : values[0] || "");
  select.setAttribute("aria-label", field);
  return select;
}

function makeTimetableSubjectPicker(value, index) {
  const wrap=document.createElement("div");
  wrap.className="timetable-subject-picker";
  const choose=document.createElement("select");
  choose.dataset.field="subject";
  choose.setAttribute("aria-label","Pilih subjek untuk waktu "+(index+1));
  choose.add(new Option("Pilih subjek",""));
  for(const group of teacherSubjectGroups){
    const options=document.createElement("optgroup");
    options.label=group.label;
    for(const name of group.values){
      const label=({
        "English":"Bahasa Inggeris (English)",
        "Pendidikan Jasmani":"Pendidikan Jasmani (PJ)",
        "Pendidikan Kesihatan":"Pendidikan Kesihatan (PK)",
        "Reka Bentuk dan Teknologi":"Reka Bentuk dan Teknologi (RBT)"
      })[name] || name;
      options.append(new Option(label,name));
    }
    choose.append(options);
  }
  choose.add(new Option("Lain-lain — taip sendiri",timetableOtherSubject));
  const custom=document.createElement("input");
  custom.type="text";
  custom.dataset.field="subject_custom";
  custom.maxLength=60;
  custom.placeholder="Taip nama subjek";
  custom.setAttribute("aria-label","Nama subjek lain untuk waktu "+(index+1));
  const saved=typeof value==="string"?value:"";
  const isKnown=subjectNames.has(saved);
  choose.value=isKnown?saved:(saved?timetableOtherSubject:"");
  custom.value=isKnown?"":saved;
  custom.hidden=choose.value!==timetableOtherSubject;
  custom.disabled=custom.hidden;
  choose.addEventListener("change",()=>{
    const isCustom=choose.value===timetableOtherSubject;
    custom.hidden=!isCustom;
    custom.disabled=!isCustom;
    timetableMessage.textContent="Perubahan jadual belum disimpan.";
    if(isCustom)custom.focus();
  });
  wrap.append(choose,custom);
  return wrap;
}

function makeTimetableInput(type, field, value) {
  const input = document.createElement("input");
  input.type = type;
  input.dataset.field = field;
  input.value = value || "";
  input.setAttribute("aria-label", field);
  if (type === "text") {
    input.maxLength = 60;
    input.placeholder = "Taip nama subjek";
  }
  return input;
}

function timetableValueRows() {
  return [...timetableBody.querySelectorAll("tr")].map(tr => {
    const entry = {};
    for (const field of ["day","start","end","class_name","subject"]) {
      const control=tr.querySelector('[data-field="' + field + '"]');
      entry[field]=field==="subject" && control.value===timetableOtherSubject
        ? tr.querySelector('[data-field="subject_custom"]').value.trim()
        : control.value.trim();
    }
    return entry;
  });
}

function renderTeacherTimetable(entries) {
  timetableBody.replaceChildren();
  for (const [index, row] of entries.entries()) {
    const tr = document.createElement("tr");
    const fields = [
      makeTimetableSelect(teacherDays,row.day,"day",null),
      makeTimetableInput("time","start",row.start),
      makeTimetableInput("time","end",row.end),
      makeTimetableSelect(teacherProfileState.classNames,row.class_name,"class_name","Pilih kelas"),
      makeTimetableSubjectPicker(row.subject,index),
    ];
    for (const [fieldIndex,el] of fields.entries()) {
      const td=document.createElement("td");
      td.dataset.label=["Hari","Mula","Tamat","Kelas","Subjek"][fieldIndex];
      td.append(el);tr.append(td);
    }
    const action = document.createElement("button");
    action.type = "button";action.className = "remove-period";
    action.textContent = "Buang";action.setAttribute("aria-label","Buang waktu "+(index + 1));
    action.addEventListener("click", () => {
      const rows=timetableValueRows();
      rows.splice(index,1);
      renderTeacherTimetable(rows);
      timetableMessage.textContent="Perubahan jadual belum disimpan.";
    });
    const last=document.createElement("td");
    last.dataset.label="Buang";
    last.append(action);tr.append(last);
    timetableBody.append(tr);
  }
  document.getElementById("timetable-empty").hidden=entries.length>0;
}

function setTeacherProfileButtons(enabled) {
  profileSaveButton.disabled=!enabled;
  timetableSaveButton.disabled=!enabled;
  timetableAddButton.disabled=!enabled;
  timetableReaderFile.disabled=!enabled;
  updateTimetableReaderButtons();
  updateAutoLogoButton();
}

async function teacherApi(url, method, body) {
  const opts={method,credentials:"same-origin",cache:"no-store",
              headers:{"Accept":"application/json"}};
  if (body !== undefined) {
    opts.headers["Content-Type"]="application/json";
    opts.body=JSON.stringify(body);
  }
  const response=await fetch(url,opts);
  const data=await response.json().catch(()=>({}));
  if(!response.ok)throw new Error(
    (typeof data.error==="string" && data.error) ||
    (response.status===401 ? "Sesi tamat. Sila log masuk semula." : "Sambungan tidak tersedia (HTTP "+response.status+")."));
  return data;
}

// All choices come from the server's authenticated pangkalan data school directory.
// Keep existing free-text school profiles readable until their owner selects
// an exact school code; never silently replace or erase an old school name.
const schoolStateField=document.getElementById("profile-state");
const schoolDistrictField=document.getElementById("profile-district");
const schoolChoiceField=document.getElementById("profile-school-choice");
const schoolNameField=document.getElementById("profile-school");
const schoolPickerNotice=document.getElementById("profile-school-notice");
let schoolPickerRequest=0;
let schoolCatalogOptions=[];

const schoolSelectData=new Map();

function schoolSearchText(value) {
  return value.toLocaleUpperCase("ms-MY").normalize("NFKD")
    .replace(/\p{M}/gu,"").replace(/[^A-Z0-9]+/g," ").trim();
}

function schoolOptionLabel(control,row) {
  return control===schoolChoiceField ? row.label+" ("+row.value+")" : row.label;
}

function initSchoolCombo(control,searchPlaceholder) {
  const input=document.getElementById(control.id+"-input");
  const list=document.getElementById(control.id+"-list");
  const menu=list.parentElement;
  const empty=menu.querySelector(".school-picker-empty");
  const combo=input.parentElement;
  let items=[];
  let matches=[];
  let active=-1;

  function close() {
    menu.hidden=true;
    input.setAttribute("aria-expanded","false");
    input.removeAttribute("aria-activedescendant");
    input.placeholder=control.options[0]?.textContent||"";
    input.value=control.value ? control.selectedOptions[0]?.textContent||"" : "";
  }

  function highlight(index) {
    list.children[active]?.classList.remove("is-active");
    active=index;
    const option=list.children[active];
    if(!option) {
      input.removeAttribute("aria-activedescendant");
      return;
    }
    option.classList.add("is-active");
    input.setAttribute("aria-activedescendant",option.id);
    option.scrollIntoView({block:"nearest"});
  }

  function filter() {
    const words=schoolSearchText(input.value).split(" ").filter(Boolean);
    matches=items.filter(row=>{
      const label=schoolSearchText(row.label);
      const value=schoolSearchText(row.value);
      const initials=label.split(" ").map(word=>word[0]).join("");
      const searchable=label+" "+value+" "+initials;
      return words.every(word=>searchable.includes(word));
    });
    active=-1;
    input.removeAttribute("aria-activedescendant");
    list.replaceChildren(...matches.map((row,index)=>{
      const option=document.createElement("li");
      option.id=list.id+"-"+index;
      option.setAttribute("role","option");
      option.setAttribute("aria-selected",String(control.value===row.value));
      option.dataset.index=index;
      option.textContent=schoolOptionLabel(control,row);
      return option;
    }));
    empty.hidden=matches.length>0;
    list.scrollTop=0;
  }

  function open() {
    if(input.disabled || !menu.hidden)return;
    menu.hidden=false;
    input.setAttribute("aria-expanded","true");
    input.value="";
    input.placeholder=searchPlaceholder;
    filter();
  }

  function choose(row) {
    if(!row)return;
    const changed=control.value!==row.value;
    control.value=row.value;
    close();
    if(changed)control.dispatchEvent(new Event("change",{bubbles:true}));
  }

  input.addEventListener("focus",open);
  input.addEventListener("click",open);
  input.addEventListener("blur",close);
  input.addEventListener("input",()=>{
    if(menu.hidden) {
      const typed=input.value;
      open();
      input.value=typed;
    }
    filter();
  });
  input.addEventListener("keydown",event=>{
    if(event.isComposing)return;
    if(event.key==="Escape" && !menu.hidden) {
      event.preventDefault();
      close();
    } else if(event.key==="ArrowDown" || event.key==="ArrowUp") {
      event.preventDefault();
      open();
      if(matches.length)highlight(event.key==="ArrowDown"
        ? Math.min(active+1,matches.length-1)
        : active<0 ? matches.length-1 : Math.max(active-1,0));
    } else if(event.key==="Enter") {
      event.preventDefault();
      if(menu.hidden)open();
      else choose(matches[active]||(matches.length===1 ? matches[0] : null));
    }
  });
  list.addEventListener("mousedown",event=>event.preventDefault());
  list.addEventListener("click",event=>{
    const option=event.target.closest('[role="option"]');
    if(option)choose(matches[Number(option.dataset.index)]);
  });

  control.hidden=true;
  combo.hidden=false;
  document.getElementById(control.id+"-label").htmlFor=input.id;
  return {
    update(rows) {
      items=rows;
      input.disabled=!rows.length;
      close();
    },
    input,
  };
}

const schoolCombos=new Map([
  [schoolStateField,initSchoolCombo(schoolStateField,"Taip nama negeri")],
  [schoolDistrictField,initSchoolCombo(schoolDistrictField,"Taip nama PPD")],
  [schoolChoiceField,initSchoolCombo(schoolChoiceField,"Taip nama atau kod sekolah")],
]);

function populateSchoolSelect(control, placeholder, items, saved="") {
  schoolSelectData.set(control,{items});
  control.replaceChildren(new Option(placeholder,""));
  for(const row of items)control.add(new Option(schoolOptionLabel(control,row),row.value));
  if(saved&&!items.some(row=>row.value===saved))
    control.add(new Option(saved.toLocaleUpperCase("ms-MY")+" (rekod lama — semak semula)",saved));
  control.value=saved;
  control.disabled=!items.length&&!saved;
  schoolCombos.get(control).update(items);
}

async function getSchoolChoices(kind, state="", district="") {
  const params=new URLSearchParams({kind});
  if(kind!=="states")params.set("state",state);
  if(kind==="schools")params.set("district",district);
  const data=await teacherApi("/api/web/teacher/school-directory?"+params,"GET");
  if(!Array.isArray(data.items))throw new Error("Senarai sekolah pangkalan data tidak sah.");
  return data.items;
}

async function populateSchoolDistricts(saved="", requestId=schoolPickerRequest) {
  const state=schoolStateField.value;
  populateSchoolSelect(schoolDistrictField,"Memuatkan PPD…",[]);
  populateSchoolSelect(schoolChoiceField,"Pilih PPD dahulu",[]);
  schoolCatalogOptions=[];
  if(!state) {
    populateSchoolSelect(schoolDistrictField,"Pilih negeri dahulu",[]);
    return;
  }
  const items=await getSchoolChoices("districts",state);
  if(requestId!==schoolPickerRequest||schoolStateField.value!==state)return;
  populateSchoolSelect(schoolDistrictField,"Pilih PPD / daerah pendidikan",items,saved);
}

async function populateSchoolNames(saved="",requestId=schoolPickerRequest) {
  const state=schoolStateField.value,district=schoolDistrictField.value;
  populateSchoolSelect(schoolChoiceField,"Memuatkan sekolah…",[]);
  schoolCatalogOptions=[];
  if(!state||!district) {
    populateSchoolSelect(schoolChoiceField,"Pilih PPD dahulu",[]);
    return;
  }
  const items=await getSchoolChoices("schools",state,district);
  if(requestId!==schoolPickerRequest||
     schoolStateField.value!==state||schoolDistrictField.value!==district)return;
  schoolCatalogOptions=items;
  populateSchoolSelect(schoolChoiceField,"Pilih sekolah",items,saved);
}

async function loadSchoolPickerForProfile(profile) {
  const seq=++schoolPickerRequest;
  const savedState=profile.state_name||"";
  const savedDistrict=profile.district_name||"";
  const savedCode=profile.school_code||"";
  schoolNameField.value=(profile.school_name||"").toLocaleUpperCase("ms-MY");
  const currentStates=schoolSelectData.get(schoolStateField)?.items||
    [...schoolStateField.options].filter(option=>option.value).map(option=>({
      value:option.value,label:option.textContent.toLocaleUpperCase("ms-MY"),
    }));
  populateSchoolSelect(schoolStateField,"Pilih negeri",currentStates,savedState);
  populateSchoolSelect(schoolDistrictField,"Pilih negeri dahulu",[]);
  populateSchoolSelect(schoolChoiceField,"Pilih PPD dahulu",[]);
  schoolPickerNotice.textContent="Memuatkan negeri, PPD dan sekolah dari pangkalan data…";
  try {
    const states=await getSchoolChoices("states");
    if(seq!==schoolPickerRequest)return;
    populateSchoolSelect(schoolStateField,"Pilih negeri",states,savedState);
    if(savedState && savedDistrict) {
      await populateSchoolDistricts(savedDistrict,seq);
      await populateSchoolNames(savedCode,seq);
    } else if(savedState) {
      await populateSchoolDistricts("",seq);
    }
    if(seq!==schoolPickerRequest)return;
    // Use the server's verified full uppercase display label for a linked
    // school; old free-text profiles still keep their existing identity.
    const matchingSchool=savedCode && schoolCatalogOptions.find(row=>row.value===savedCode);
    if(matchingSchool)schoolNameField.value=matchingSchool.label;
    schoolPickerNotice.textContent=savedCode
      ? "Sekolah dipadankan melalui kod rasmi. Rujukan direktori Jun 2022."
      : savedState && profile.school_name
      ? "Nama sekolah lama dikekalkan. Pilih PPD dan sekolah untuk melengkapkan padanan rasmi."
      : "Pilih Negeri → PPD → Sekolah. Nama penuh akan diisi automatik (rujukan Jun 2022).";
  } catch(err) {
    if(seq!==schoolPickerRequest)return;
    // Account and timetable still work; do not wipe school data during outages.
    populateSchoolSelect(schoolStateField,"Pilih negeri",schoolSelectData.get(schoolStateField).items,savedState);
    if(savedDistrict&&!schoolDistrictField.value)
      populateSchoolSelect(schoolDistrictField,"Pilih PPD / daerah pendidikan",[],savedDistrict);
    if(savedCode&&!schoolChoiceField.value)
      populateSchoolSelect(schoolChoiceField,"Pilih sekolah",[],savedCode);
    schoolNameField.value=(profile.school_name||"").toLocaleUpperCase("ms-MY");
    schoolPickerNotice.textContent="Direktori sekolah tidak tersedia. Maklumat lama dikekalkan; cuba Refresh Profil.";
  }
}

for(const control of schoolCombos.keys()) {
  const rows=[...control.options].filter(option=>option.value).map(option=>({
    value:option.value,label:option.textContent.toLocaleUpperCase("ms-MY"),
  }));
  populateSchoolSelect(control,control.options[0]?.textContent||"",rows,control.value);
}

schoolStateField.addEventListener("change",async()=>{
  const seq=++schoolPickerRequest;
  clearSchoolLogoSelection();
  schoolNameField.value="";
  schoolPickerNotice.textContent="Memuatkan PPD negeri yang dipilih…";
  try {
    const districts=populateSchoolDistricts("",seq);
    updateAutoLogoButton();
    await districts;
    if(seq===schoolPickerRequest)
      schoolPickerNotice.textContent="Pilih PPD, kemudian sekolah.";
  } catch(err) {
    if(seq===schoolPickerRequest)
      schoolPickerNotice.textContent="PPD tidak dapat dimuatkan. Maklumat belum disimpan.";
  }
});
schoolDistrictField.addEventListener("change",async()=>{
  const seq=++schoolPickerRequest;
  clearSchoolLogoSelection();
  schoolNameField.value="";
  schoolPickerNotice.textContent="Memuatkan sekolah PPD yang dipilih…";
  try {
    const schools=populateSchoolNames("",seq);
    updateAutoLogoButton();
    await schools;
    if(seq===schoolPickerRequest)
      schoolPickerNotice.textContent="Pilih sekolah untuk mengisi nama penuh.";
  } catch(err) {
    if(seq===schoolPickerRequest)
      schoolPickerNotice.textContent="Senarai sekolah tidak dapat dimuatkan. Maklumat belum disimpan.";
  }
});
schoolChoiceField.addEventListener("change",()=>{
  const chosen=schoolCatalogOptions.find(row=>row.value===schoolChoiceField.value);
  updateAutoLogoButton();
  schoolNameField.value=chosen?.label||"";
  schoolPickerNotice.textContent=chosen
    ? "Nama rasmi sekolah diisi automatik; tekan Simpan Profil untuk menyimpannya di pangkalan data."
    : "Pilih sekolah daripada senarai.";
  void previewSelectedSchoolLogo();
});

async function loadTeacherProfile() {
  if(timetableImportSaving)return;
  clearSchoolLogoSelection();
  teacherProfileState.loaded=false;
  timetableReadRequest?.abort();
  timetableReader.hidden=true;
  timetableReaderFile.value="";
  timetableReview=null;
  timetableReaderStatus.textContent="";
  setTeacherProfileButtons(false);
  profileMessage.textContent="Memuatkan maklumat guru…";
  timetableMessage.textContent="Memuatkan jadual mengajar…";
  try {
    const result=await teacherApi("/api/web/teacher/profile","GET");
    if(!result.profile || !result.timetable || !Array.isArray(result.profile.class_names)
       || !Array.isArray(result.timetable.entries))throw new Error("Data profil tidak sah.");
    const profile=result.profile, timetable=result.timetable;
    teacherProfileState.classAliases=profile.timetable_class_aliases||{};
    teacherNameField.value=(profile.display_name || "Cikgu").toLocaleUpperCase("ms-MY");
    await loadSchoolPickerForProfile(profile);
    document.getElementById("profile-classes").value=profile.class_names.join("\n");
    setTeacherIdentity({...profile,school_name:schoolNameField.value});
    teacherProfileState.classNames=[...profile.class_names];
    teacherProfileState.profileVersion=profile.version || "";
    teacherProfileState.timetableVersion=timetable.version || "";
    teacherProfileState.savedPeriods=timetable.entries.length;
    teacherProfileState.savedProfile=JSON.stringify(profileEditorData());
    renderTeacherTimetable(timetable.entries);
    teacherProfileState.savedTimetable=JSON.stringify(timetableValueRows());
    teacherProfileState.loaded=true;
    timetableReader.hidden=result.timetable_auto_read!==true;
    setTeacherProfileButtons(true);
    renderProfileReadiness();
    void refreshLogoAndTryAutomaticImport();
    profileMessage.textContent="Maklumat guru tersedia untuk disunting.";
    timetableMessage.textContent=timetable.entries.length+" waktu dimuatkan.";
  }catch(err){
    profileMessage.textContent=err.message;
    timetableMessage.textContent="Tidak dapat memuatkan jadual. Simpan dimatikan untuk melindungi rekod lama.";
    renderProfileReadiness();
  }
}

profileForm.addEventListener("submit", async event => {
  event.preventDefault();
  if(!teacherProfileState.loaded || timetableImportSaving)return;
  const class_names=teacherClassLines();
  if(class_names.length>25) {
    profileMessage.textContent="Maksimum 25 kelas. Sila kurangkan senarai.";
    return;
  }
  const previousCode=teacherProfileState.savedProfile
    ? JSON.parse(teacherProfileState.savedProfile).school_code : "";
  const editedProfile={...profileEditorData(),class_names};
  const body={...editedProfile,version:teacherProfileState.profileVersion};
  profileSaveButton.disabled=true;
  profileMessage.textContent="Menyimpan maklumat guru…";
  try {
    const result=await teacherApi("/api/web/teacher/profile","PUT",body);
    if(!result.saved || typeof result.version!=="string")throw new Error("Pengesahan simpan tidak lengkap.");
    teacherProfileState.profileVersion=result.version;
    teacherProfileState.timetableVersion=result.version;
    teacherProfileState.savedProfile=JSON.stringify(editedProfile);
    teacherProfileState.classNames=class_names;
    updateAutoLogoButton();
    renderProfileReadiness();
    if(body.school_code && savedLogoSchoolCode()===body.school_code){
      clearSchoolLogoSelection();
      if(body.school_code!==previousCode)void refreshLogoAndTryAutomaticImport(true);
    }
    setTeacherIdentity(body);
    renderTeacherTimetable(timetableValueRows());
    if(typeof loadTeacherClasses==="function")loadTeacherClasses();
    profileMessage.textContent="Maklumat guru dan senarai kelas berjaya disimpan.";
  }catch(err){
    profileMessage.textContent=err.message;
  }finally{
    profileSaveButton.disabled=!teacherProfileState.loaded;
  }
});

timetableAddButton.addEventListener("click",() => {
  if(!teacherProfileState.loaded)return;
  if(!teacherProfileState.classNames.length){
    timetableMessage.textContent="Simpan sekurang-kurangnya satu kelas dalam profil dahulu.";
    return;
  }
  const rows=timetableValueRows();
  if(rows.length>=80){
    timetableMessage.textContent="Maksimum 80 waktu mengajar.";
    return;
  }
  rows.push({day:"Isnin",start:"07:30",end:"08:30",
             class_name:teacherProfileState.classNames[0],subject:""});
  renderTeacherTimetable(rows);
  const newSubject=timetableBody.lastElementChild?.querySelector('[data-field="subject"]');
  newSubject?.focus();
  timetableMessage.textContent="Pilih subjek daripada senarai atau Lain-lain untuk menaip sendiri. Kemudian simpan jadual.";
});

timetableSaveButton.addEventListener("click",async() => {
  if(!teacherProfileState.loaded || timetableImportSaving)return;
  const entries=timetableValueRows();
  if(!entries.length && teacherProfileState.savedPeriods>0 &&
     !window.confirm("Ini akan mengosongkan jadual waktu yang disimpan. Teruskan?"))return;
  if(!entries.length && !teacherProfileState.savedPeriods){
    timetableMessage.textContent="Tambah waktu dahulu sebelum menyimpan.";
    return;
  }
  timetableSaveButton.disabled=true;
  timetableMessage.textContent="Menyimpan jadual waktu…";
  try{
    const result=await teacherApi("/api/web/teacher/timetable","PUT",{
      entries,version:teacherProfileState.timetableVersion,
    });
    if(!result.saved || typeof result.version!=="string")throw new Error("Pengesahan simpan tidak lengkap.");
    teacherProfileState.timetableVersion=result.version;
    teacherProfileState.profileVersion=result.version;
    teacherProfileState.savedTimetable=JSON.stringify(entries);
    teacherProfileState.savedPeriods=entries.length;
    renderProfileReadiness();
    timetableMessage.textContent=entries.length+" waktu berjaya disimpan. Jadual ini turut tersedia di Telegram.";
  }catch(err){
    timetableMessage.textContent=err.message;
  }finally{
    timetableSaveButton.disabled=!teacherProfileState.loaded;
  }
});


function updateTimetableReaderButtons() {
  timetableReaderStart.disabled=!teacherProfileState.loaded || !timetableReaderFile.files.length ||
    timetableReadRequest!==null || timetableImportSaving;
  timetableReaderReview.hidden=!timetableReview;
  timetableReaderBack.disabled=timetableImportSaving;
  timetableReaderDismiss.disabled=timetableImportSaving;
  timetableReaderNext.disabled=timetableImportSaving;
}

function sameTimetablePeriod(first,second) {
  return first.day===second.day && first.start===second.start && first.end===second.end
    && first.class_name.toLowerCase()===second.class_name.toLowerCase()
    && first.subject.toLowerCase()===second.subject.toLowerCase();
}

function overlappingTimetablePeriod(first,second) {
  return first.day===second.day && first.start<second.end && second.start<first.end;
}

function renderUnclearTimetableCells(result) {
  const cells=result.unclear_cells||[];
  const count=result.uncertain||0;
  const messages={
    time:"Masa tidak dapat dikenal pasti",
    details:"Kelas dan subjek tidak dapat dikenal pasti",
    review:"Semak kelas atau subjek dalam senarai di atas",
  };
  timetableReaderUnclear.hidden=!count;
  timetableReaderUnclear.open=true;
  timetableReaderUnclearTitle.textContent=count+" petak kurang jelas";
  timetableReaderUnclearList.replaceChildren();
  for(const cell of cells){
    const item=document.createElement("li");
    item.textContent="Halaman "+cell.page+" · "+cell.day+
      (cell.start ? " "+cell.start+"–"+cell.end : "")+" · "+messages[cell.reason];
    timetableReaderUnclearList.append(item);
  }
  const remaining=count-cells.length;
  timetableReaderUnclearNote.hidden=remaining<=0;
  timetableReaderUnclearNote.textContent=remaining>0
    ? remaining+" petak lagi perlu disemak pada jadual asal."
    : "";
}

function timetableReviewGroup(row, index, field) {
  const value=field==="subject" ? row.subject_code || row.subject : row.class_name;
  return value ? value.toUpperCase() : "?" + index;
}

function reviewField(label) {
  const field=document.createElement("fieldset");
  const legend=document.createElement("legend");
  legend.textContent=label;
  field.append(legend);
  timetableReaderFields.append(field);
  return field;
}

function renderTimetableMappings(field) {
  const isSubject=field==="subject";
  const mappings=isSubject ? timetableReview.subjects : timetableReview.classes;
  const groups=new Map();
  timetableReview.rows.forEach((row,index)=>{
    const key=timetableReviewGroup(row,index,field);
    if(!groups.has(key))groups.set(key,{row,index,count:0});
    groups.get(key).count++;
  });
  for(const [key,{row,index,count}] of groups){
    const unknown=key.startsWith("?");
    const label=unknown ? row.day+" · "+(row.start || "waktu "+(index+1))
      : isSubject ? row.subject_code || row.subject : row.class_name;
    const group=reviewField(label+" · "+count+" waktu");
    group.dataset.key=key;
    if(isSubject){
      const suggested=row.subject_code===row.subject ? "" : row.subject;
      group.append(makeTimetableSubjectPicker(mappings.get(key) ?? suggested,index));
      group.querySelector("select").setAttribute("aria-label","Subjek "+label);
    }else{
      const input=document.createElement("input");
      input.type="text";
      input.maxLength=40;
      input.placeholder="Nama penuh kelas";
      input.setAttribute("aria-label","Nama penuh kelas "+label);
      const saved=Object.hasOwn(teacherProfileState.classAliases,key) ? teacherProfileState.classAliases[key] : "";
      input.value=mappings.get(key) ?? (saved || row.class_name);
      group.append(input);
    }
  }
}

function renderTimetableTimes() {
  timetableReview.rows.forEach((row,index)=>{
    const subject=timetableReview.subjects.get(timetableReviewGroup(row,index,"subject"));
    const className=timetableReview.classes.get(timetableReviewGroup(row,index,"class_name"));
    const group=reviewField((index+1)+". "+className+" · "+subject);
    const times=timetableReview.times[index] || row;
    const fields=document.createElement("div");
    fields.className="timetable-time-fields";
    const controls=[
      ["Hari",makeTimetableSelect(teacherDays,times.day,"day",null)],
      ["Mula",makeTimetableInput("time","start",times.start)],
      ["Tamat",makeTimetableInput("time","end",times.end)],
    ];
    for(const [label,control] of controls){
      const field=document.createElement("label");
      field.textContent=label;
      control.setAttribute("aria-label",label+" waktu "+(index+1));
      field.append(control);
      fields.append(field);
    }
    group.append(fields);
    const skip=document.createElement("input");
    skip.type="checkbox";
    skip.dataset.field="skip";
    skip.checked=Boolean(times.skip);
    const label=document.createElement("label");
    label.append(skip," Abaikan waktu ini");
    group.append(label);
  });
}

function renderTimetableReadReport() {
  const current=JSON.parse(teacherProfileState.savedTimetable);
  timetableReview.base=teacherProfileState.savedTimetable;
  timetableReview.choices=[];
  timetableReaderReportRows.replaceChildren();
  for(const [index,raw] of timetableReview.rows.entries()){
    const {day,start,end,skip}=timetableReview.times[index];
    if(skip)continue;
    const row={day,start,end,
      class_name:timetableReview.classes.get(timetableReviewGroup(raw,index,"class_name")),
      subject:timetableReview.subjects.get(timetableReviewGroup(raw,index,"subject"))};
    const overlaps=current.map((period,i)=>overlappingTimetablePeriod(period,row) ? i : -1).filter(i=>i>=0);
    const duplicate=overlaps.some(i=>sameTimetablePeriod(current[i],row));
    const canUpdate=overlaps.length===1 && !duplicate;
    const previous=timetableReview.choices.find(choice=>sameTimetablePeriod(choice.row,row));
    const input=document.createElement("input");
    input.type="checkbox";
    input.checked=!previous && !overlaps.length &&
      !timetableReview.choices.some(choice=>choice.input.checked && overlappingTimetablePeriod(choice.row,row));
    input.disabled=Boolean(previous || (overlaps.length && !canUpdate));
    input.setAttribute("aria-label",(canUpdate ? "Kemas kini " : "Pilih ")+day+" "+start+" "+row.subject);
    const note=previous || duplicate ? "Pendua"
      : canUpdate ? "Tanda untuk kemas kini "+current[overlaps[0]].start+"–"+current[overlaps[0]].end+
        " · "+current[overlaps[0]].class_name+" · "+current[overlaps[0]].subject
      : overlaps.length ? "Bertindih dengan beberapa waktu sedia ada" : "Waktu baharu";
    const tr=document.createElement("tr");
    const cell=document.createElement("td");
    cell.append(input);
    tr.append(cell);
    for(const value of [day+" "+start+"–"+end,row.class_name,row.subject,note]){
      const td=document.createElement("td");
      td.textContent=value;
      tr.append(td);
    }
    timetableReaderReportRows.append(tr);
    timetableReview.choices.push({row,input,replace:canUpdate ? overlaps[0] : -1});
  }
}

function showTimetableStep(step) {
  const titles=["Sahkan Subjek","Sahkan Kelas","Sahkan Masa","Semak dan Simpan"];
  const instructions=[
    "Pilih nama subjek sekali bagi setiap singkatan atau nama yang dikesan.",
    "Taip nama penuh bagi setiap kod kelas.",
    "Semak hari, masa mula dan masa tamat. Tandakan Abaikan waktu ini jika perlu.",
    "Pilih waktu yang hendak ditambah atau dikemas kini.",
  ];
  timetableReview.step=step;
  timetableReaderFields.replaceChildren();
  timetableReaderPreview.hidden=step!==3;
  timetableReaderBack.hidden=step===0;
  timetableReaderTitle.textContent=(step+1)+"/4 · "+titles[step];
  timetableReaderNote.textContent=instructions[step];
  timetableReaderNext.textContent=step===3 ? "Simpan Waktu Dipilih" : titles[step];
  timetableReaderFeedback.textContent="";
  if(step<2)renderTimetableMappings(step===0 ? "subject" : "class_name");
  else if(step===2)renderTimetableTimes();
  else renderTimetableReadReport();
  timetableReaderReview.hidden=false;
  timetableReaderTitle.focus();
}

function rememberTimetableStep() {
  const {step,subjects,classes}=timetableReview;
  const groups=[...timetableReaderFields.querySelectorAll("fieldset")];
  if(step===2){
    timetableReview.times=groups.map(group=>{
      const value=field=>group.querySelector('[data-field="'+field+'"]').value;
      return {day:value("day"),start:value("start"),end:value("end"),
        skip:group.querySelector('[data-field="skip"]').checked};
    });
    return;
  }
  for(const group of groups){
    if(step===0){
      const select=group.querySelector("select");
      subjects.set(group.dataset.key,select.value===timetableOtherSubject
        ? group.querySelector('[data-field="subject_custom"]').value.trim() : select.value);
    }else if(step===1){
      classes.set(group.dataset.key,group.querySelector("input").value.trim());
    }
  }
}

timetableReaderFile.addEventListener("change",()=>{
  timetableReadRequest?.abort();
  timetableReview=null;
  timetableReaderStatus.textContent="";
  updateTimetableReaderButtons();
});

timetableReaderStart.addEventListener("click",async()=>{
  const file=timetableReaderFile.files[0];
  if(!teacherProfileState.loaded || timetableReader.hidden || !file || timetableReadRequest || timetableImportSaving)return;
  if(file.size===0 || file.size>8*1024*1024){
    timetableReaderStatus.textContent="Pilih satu fail jadual berukuran maksimum 8 MB.";
    return;
  }
  const controller=new AbortController();
  timetableReadRequest=controller;
  timetableReview=null;
  updateTimetableReaderButtons();
  timetableReaderStatus.textContent="Sedang membaca jadual waktu…";
  const timeout=setTimeout(()=>controller.abort("timeout"),25000);
  try{
    const body=new FormData();
    body.append("timetable",file);
    const response=await fetch("/api/web/teacher/timetable/read",{
      method:"POST",credentials:"same-origin",cache:"no-store",body,signal:controller.signal,
      headers:{"Accept":"application/json"},
    });
    const result=await response.json().catch(()=>({}));
    if(!response.ok || !Array.isArray(result.entries) || !result.entries.length)
      throw new Error(result.error || "Jadual belum dapat dibaca. Cuba lagi.");
    if(controller.signal.aborted || timetableReader.hidden)return;
    timetableReview={rows:result.entries,subjects:new Map(),classes:new Map(),times:[]};
    const summary=[result.entries.length+" waktu dikesan."];
    if(result.uncertain)summary.push(result.uncertain+" petak kurang jelas.");
    if(result.unreadable_pages)summary.push(result.unreadable_pages+" halaman kurang jelas.");
    if(result.uncertain || result.unreadable_pages)summary.push("Semak jadual asal dan tambah waktu yang tertinggal.");
    timetableReaderStatus.textContent=summary.join(" ");
    renderUnclearTimetableCells(result);
    showTimetableStep(0);
  }catch(err){
    if(controller.signal.reason==="timeout"){
      timetableReaderStatus.textContent="Bacaan mengambil masa terlalu lama. Cuba satu halaman atau gambar yang lebih kecil.";
    }else if(!controller.signal.aborted){
      timetableReaderStatus.textContent=err.message;
    }
  }finally{
    clearTimeout(timeout);
    if(timetableReadRequest===controller)timetableReadRequest=null;
    updateTimetableReaderButtons();
  }
});

async function saveTimetableReview() {
  if(profileSaveButton.disabled || timetableSaveButton.disabled)return;
  const current=JSON.parse(teacherProfileState.savedTimetable);
  if(JSON.stringify(timetableValueRows())!==teacherProfileState.savedTimetable){
    timetableReaderFeedback.textContent="Simpan suntingan dalam Jadual Sedia Ada dahulu, kemudian semak pilihan import.";
    return;
  }
  if(timetableReview.base!==teacherProfileState.savedTimetable){
    renderTimetableReadReport();
    timetableReaderFeedback.textContent="Jadual sedia ada telah berubah. Semak semula pilihan waktu.";
    return;
  }
  const selected=timetableReview.choices.filter(choice=>choice.input.checked);
  if(!selected.length){
    timetableReaderFeedback.textContent="Pilih sekurang-kurangnya satu waktu.";
    return;
  }
  const replacements=selected.map(choice=>choice.replace).filter(index=>index>=0);
  const entries=current.filter((_,index)=>!replacements.includes(index)).concat(selected.map(choice=>choice.row));
  if(new Set(replacements).size!==replacements.length ||
     selected.some(({row})=>entries.some(other=>other!==row && overlappingTimetablePeriod(row,other)))){
    timetableReaderFeedback.textContent="Waktu yang dipilih bertindih. Semak pilihan atau kembali untuk betulkan masa.";
    return;
  }
  if(entries.length>80){
    timetableReaderFeedback.textContent="Maksimum 80 waktu dalam jadual.";
    return;
  }
  if(replacements.length && !window.confirm("Kemas kini "+replacements.length+" waktu sedia ada dan simpan jadual?"))return;
  const subjectAliases=Object.fromEntries(timetableReview.rows
    .filter(row=>row.subject_code)
    .map(row=>[row.subject_code,timetableReview.subjects.get(row.subject_code)]));
  const classAliases=Object.fromEntries([...timetableReview.classes].filter(([key])=>!key.startsWith("?")));
  timetableImportSaving=true;
  timetableReaderFile.disabled=true;
  timetableAddButton.disabled=true;
  profileSaveButton.disabled=true;
  timetableSaveButton.disabled=true;
  const controls=[...timetableBody.querySelectorAll("input, select, button")].filter(control=>!control.disabled);
  controls.forEach(control=>{control.disabled=true;});
  updateTimetableReaderButtons();
  timetableReaderFeedback.textContent="Menyimpan jadual…";
  try{
    const result=await teacherApi("/api/web/teacher/timetable/import","PUT",{
      changes:selected.map(({row,replace})=>({entry:row,replace:current[replace]||null})),
      subject_aliases:subjectAliases,class_aliases:classAliases,version:teacherProfileState.timetableVersion,
    });
    if(!result.saved || typeof result.version!=="string")throw new Error("Pengesahan simpan tidak lengkap.");
    teacherProfileState.profileVersion=result.version;
    teacherProfileState.timetableVersion=result.version;
    Object.assign(teacherProfileState.classAliases,classAliases);
    const classes=new Map(teacherProfileState.classNames.map(name=>[name.toLowerCase(),name]));
    const draftClasses=new Map(teacherClassLines().map(name=>[name.toLowerCase(),name]));
    const savedProfile=JSON.parse(teacherProfileState.savedProfile);
    for(const {class_name:name} of entries){
      if(!classes.has(name.toLowerCase())){
        classes.set(name.toLowerCase(),name);
        draftClasses.set(name.toLowerCase(),name);
      }
    }
    teacherProfileState.classNames=[...classes.values()];
    savedProfile.class_names=teacherProfileState.classNames;
    teacherProfileState.savedProfile=JSON.stringify(savedProfile);
    document.getElementById("profile-classes").value=[...draftClasses.values()].join("\n");
    renderTeacherTimetable(entries);
    teacherProfileState.savedTimetable=JSON.stringify(timetableValueRows());
    teacherProfileState.savedPeriods=entries.length;
    renderProfileReadiness();
    if(typeof loadTeacherClasses==="function")loadTeacherClasses();
    timetableReview=null;
    timetableReaderFile.value="";
    const message=selected.length+" waktu dipilih berjaya disimpan.";
    timetableMessage.textContent=message;
    timetableReaderStatus.textContent=message;
  }catch(err){
    timetableReaderFeedback.textContent=err.message;
  }finally{
    timetableImportSaving=false;
    controls.forEach(control=>{control.disabled=false;});
    timetableReaderFile.disabled=!teacherProfileState.loaded;
    timetableAddButton.disabled=!teacherProfileState.loaded;
    profileSaveButton.disabled=!teacherProfileState.loaded;
    timetableSaveButton.disabled=!teacherProfileState.loaded;
    updateTimetableReaderButtons();
  }
}

timetableReaderNext.addEventListener("click",()=>{
  if(!timetableReview || timetableImportSaving)return;
  const {step,subjects,classes}=timetableReview;
  if(step===3){
    void saveTimetableReview();
    return;
  }
  rememberTimetableStep();
  if(step<2 && [...(step===0 ? subjects : classes).values()].some(value=>!value)){
    timetableReaderFeedback.textContent=step===0 ? "Pilih nama bagi setiap subjek." : "Isi nama penuh bagi setiap kelas.";
    return;
  }
  if(step===2 && timetableReview.times.some(row=>!row.skip && (!row.start || !row.end || row.start>=row.end))){
    timetableReaderFeedback.textContent="Betulkan masa mula dan tamat atau abaikan waktu berkenaan.";
    return;
  }
  if(step===2 && timetableReview.times.every(row=>row.skip)){
    timetableReaderFeedback.textContent="Kekalkan sekurang-kurangnya satu waktu untuk disemak.";
    return;
  }
  showTimetableStep(step+1);
});

timetableReaderBack.addEventListener("click",()=>{
  if(!timetableReview || timetableImportSaving)return;
  rememberTimetableStep();
  showTimetableStep(timetableReview.step-1);
});

timetableReaderDismiss.addEventListener("click",()=>{
  if(timetableImportSaving)return;
  timetableReview=null;
  timetableReaderStatus.textContent="";
  updateTimetableReaderButtons();
  timetableReaderStart.focus();
});
