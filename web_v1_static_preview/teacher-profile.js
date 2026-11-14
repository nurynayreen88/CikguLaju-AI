"use strict";
/* Editable teacher profile and weekly timetable.
   The browser never sees service keys or chooses a Telegram user ID. */
const teacherProfileState = {
  loaded: false, profileVersion: "", timetableVersion: "",
  classNames: [], savedPeriods: 0, savedProfile: null, savedTimetable: null,
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
    "Pendidikan Jasmani","Pendidikan Kesihatan","PJPK",
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
  next.target.scrollIntoView({block:"center",behavior:"smooth"});
  next.target.focus({preventScroll:true});
});

const profileMessage = document.getElementById("profile-save-status");
const timetableMessage = document.getElementById("timetable-save-status");
const profileSaveButton = document.getElementById("profile-save");
const timetableSaveButton = document.getElementById("timetable-save");
const timetableAddButton = document.getElementById("timetable-add");
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
  return JSON.stringify(profileEditorData()) !== teacherProfileState.savedProfile ||
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
  if (selected && !values.includes(selected)) {
    select.add(new Option(selected + " (semak profil)", selected));
  }
  select.value = selected || (placeholder ? "" : values[0] || "");
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

const schoolSearchFields=new Map([
  [schoolStateField,document.getElementById("profile-state-search")],
  [schoolDistrictField,document.getElementById("profile-district-search")],
  [schoolChoiceField,document.getElementById("profile-school-search")],
]);
const schoolSelectData=new Map();

function schoolSearchText(value) {
  return value.toLocaleUpperCase("ms-MY").normalize("NFKD")
    .replace(/\p{M}/gu,"").replace(/[^A-Z0-9]+/g," ").trim();
}

function filterSchoolSelect(control, selected=control.value) {
  const search=schoolSearchFields.get(control);
  const {placeholder,items}=schoolSelectData.get(control);
  const query=schoolSearchText(search?.value||"");
  const words=query ? query.split(" ") : [];
  const matches=items.filter(row=>{
    const label=schoolSearchText(row.label);
    const value=schoolSearchText(row.value);
    const initials=label.split(" ").map(word=>word[0]).join("");
    const text=label+" "+value+" "+initials;
    return words.every(word=>text.includes(word));
  });
  const visible=matches.some(row=>row.value===selected)
    ? matches : [...items.filter(row=>row.value===selected),...matches];
  control.replaceChildren(new Option(query&&!matches.length?"Tiada padanan":placeholder,""));
  for(const row of visible) {
    const label=control===schoolChoiceField ? row.label+" ("+row.value+")" : row.label;
    control.add(new Option(label,row.value));
  }
  if(selected&&!items.some(row=>row.value===selected))
    control.add(new Option(selected.toLocaleUpperCase("ms-MY")+" (rekod lama — semak semula)",selected));
  control.value=selected;
  control.disabled=!items.length&&!selected;
  return matches;
}

function populateSchoolSelect(control, placeholder, items, saved="") {
  schoolSelectData.set(control,{placeholder,items});
  const search=schoolSearchFields.get(control);
  if(search) {
    search.value="";
    search.disabled=!items.length;
  }
  filterSchoolSelect(control,saved);
}

for(const [control,search] of schoolSearchFields) {
  if(!search)continue;
  search.addEventListener("input",()=>{
    if(schoolSelectData.has(control))filterSchoolSelect(control);
  });
  search.addEventListener("keydown",event=>{
    if(event.key!=="Enter")return;
    event.preventDefault();
    if(!schoolSelectData.has(control))return;
    const matches=filterSchoolSelect(control);
    if(matches.length!==1||!schoolSearchText(search.value)) {
      control.focus();
      return;
    }
    if(control.value===matches[0].value) {
      control.focus();
      return;
    }
    control.value=matches[0].value;
    control.dispatchEvent(new Event("change",{bubbles:true}));
  });
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
      const districts=populateSchoolDistricts("",seq);
    updateAutoLogoButton();
    await districts;
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
    if(savedState && ![...schoolStateField.options].some(o=>o.value===savedState))
      schoolStateField.add(new Option(savedState.toLocaleUpperCase("ms-MY"),savedState));
    schoolStateField.value=savedState;
    schoolNameField.value=(profile.school_name||"").toLocaleUpperCase("ms-MY");
    schoolPickerNotice.textContent="Direktori sekolah tidak tersedia. Maklumat lama dikekalkan; cuba Refresh Profil.";
  }
}

schoolStateField.addEventListener("change",async()=>{
  const seq=++schoolPickerRequest;
  clearSchoolLogoSelection();
  schoolNameField.value="";
  schoolPickerNotice.textContent="Memuatkan PPD negeri yang dipilih…";
  try {
    await populateSchoolDistricts("",seq);
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
  clearSchoolLogoSelection();
  teacherProfileState.loaded=false;
  setTeacherProfileButtons(false);
  profileMessage.textContent="Memuatkan maklumat guru…";
  timetableMessage.textContent="Memuatkan jadual mengajar…";
  try {
    const result=await teacherApi("/api/web/teacher/profile","GET");
    if(!result.profile || !result.timetable || !Array.isArray(result.profile.class_names)
       || !Array.isArray(result.timetable.entries))throw new Error("Data profil tidak sah.");
    const profile=result.profile, timetable=result.timetable;
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
  if(!teacherProfileState.loaded)return;
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
  if(!teacherProfileState.loaded)return;
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
