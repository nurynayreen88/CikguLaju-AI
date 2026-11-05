"use strict";
/* Editable teacher profile and weekly timetable.
   The browser never sees service keys or chooses a Telegram user ID. */
const teacherProfileState = {
  loaded: false, profileVersion: "", timetableVersion: "",
  classNames: [], savedPeriods: 0,
};
const teacherDays = ["Isnin","Selasa","Rabu","Khamis","Jumaat","Sabtu","Ahad"];
const profileForm = document.getElementById("teacher-profile-form");
const timetableBody = document.getElementById("timetable-rows");
const profileMessage = document.getElementById("profile-save-status");
const timetableMessage = document.getElementById("timetable-save-status");
const profileSaveButton = document.getElementById("profile-save");
const timetableSaveButton = document.getElementById("timetable-save");
const timetableAddButton = document.getElementById("timetable-add");

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

function makeTimetableInput(type, field, value) {
  const input = document.createElement("input");
  input.type = type;
  input.dataset.field = field;
  input.value = value || "";
  input.setAttribute("aria-label", field);
  if (type === "text") {
    input.maxLength = 60;
    input.setAttribute("list", "profile-subject-options");
    input.placeholder = "Contoh: Matematik";
  }
  return input;
}

function timetableValueRows() {
  return [...timetableBody.querySelectorAll("tr")].map(tr => {
    const entry = {};
    for (const field of ["day","start","end","class_name","subject"]) {
      entry[field] = tr.querySelector('[data-field="' + field + '"]').value.trim();
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
      makeTimetableInput("text","subject",row.subject),
    ];
    for (const el of fields) {
      const td=document.createElement("td");td.append(el);tr.append(td);
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
    const last=document.createElement("td");last.append(action);tr.append(last);
    timetableBody.append(tr);
  }
  document.getElementById("timetable-empty").hidden=entries.length>0;
}

function setTeacherProfileButtons(enabled) {
  profileSaveButton.disabled=!enabled;
  timetableSaveButton.disabled=!enabled;
  timetableAddButton.disabled=!enabled;
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

async function loadTeacherProfile() {
  teacherProfileState.loaded=false;
  setTeacherProfileButtons(false);
  profileMessage.textContent="Memuatkan profil daripada Supabase…";
  timetableMessage.textContent="Memuatkan jadual daripada Supabase…";
  try {
    const result=await teacherApi("/api/web/teacher/profile","GET");
    if(!result.profile || !result.timetable || !Array.isArray(result.profile.class_names)
       || !Array.isArray(result.timetable.entries))throw new Error("Data profil tidak sah.");
    const profile=result.profile, timetable=result.timetable;
    document.getElementById("profile-name").value=profile.display_name || "Cikgu";
    document.getElementById("profile-school").value=profile.school_name || "";
    document.getElementById("profile-state").value=profile.state_name || "";
    document.getElementById("profile-classes").value=profile.class_names.join("\n");
    teacherProfileState.classNames=[...profile.class_names];
    teacherProfileState.profileVersion=profile.version || "";
    teacherProfileState.timetableVersion=timetable.version || "";
    teacherProfileState.savedPeriods=timetable.entries.length;
    renderTeacherTimetable(timetable.entries);
    teacherProfileState.loaded=true;
    setTeacherProfileButtons(true);
    profileMessage.textContent="Maklumat guru tersedia untuk disunting.";
    timetableMessage.textContent=timetable.entries.length+" waktu dimuatkan.";
  }catch(err){
    profileMessage.textContent=err.message;
    timetableMessage.textContent="Tidak dapat memuatkan jadual. Simpan dimatikan untuk melindungi rekod lama.";
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
  const body={
    display_name:document.getElementById("profile-name").value.trim(),
    school_name:document.getElementById("profile-school").value.trim(),
    state_name:document.getElementById("profile-state").value,
    class_names,
    version:teacherProfileState.profileVersion,
  };
  profileSaveButton.disabled=true;
  profileMessage.textContent="Menyimpan maklumat guru…";
  try {
    const result=await teacherApi("/api/web/teacher/profile","PUT",body);
    if(!result.saved || typeof result.version!=="string")throw new Error("Pengesahan simpan tidak lengkap.");
    teacherProfileState.profileVersion=result.version;
    teacherProfileState.classNames=class_names;
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
  timetableMessage.textContent="Isi hari, masa, kelas dan subjek. Kemudian tekan Simpan Jadual Waktu.";
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
    teacherProfileState.savedPeriods=entries.length;
    timetableMessage.textContent=entries.length+" waktu berjaya disimpan dalam Supabase.";
  }catch(err){
    timetableMessage.textContent=err.message;
  }finally{
    timetableSaveButton.disabled=!teacherProfileState.loaded;
  }
});
