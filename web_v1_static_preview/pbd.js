(() => {
  "use strict";
  const $ = id => document.getElementById("pbd-" + id);
  if (!$("editor")) return;
  const statuses = ["Belum dinilai", "Boleh sendiri", "Dengan bimbingan", "Belum menguasai"];
  const methods = ["Pemerhatian", "Lisan", "Penulisan", "Pelbagai kaedah"];
  const levels = Array.from({length: 6}, (_, i) => "TP" + (i + 1));
  const fields = ["date", "subject", "lesson", "sk", "sp", "criteria1", "criteria2", "period"];
  let students = [], rosterVersion = "", active = null, current = null, page = 1, busy = false;
  let rosterDirty = false, recordDirty = false, pendingLesson = null;
  function today() {
    return new Intl.DateTimeFormat("sv-SE", {timeZone:"Asia/Kuala_Lumpur",
      year:"numeric",month:"2-digit",day:"2-digit"}).format(new Date());
  }
  $("year").value = today().slice(0, 4);
  const element = (tag, value = "") => {
    const node = document.createElement(tag);
    node.textContent = value;
    return node;
  };
  function notify(value) { $("message").textContent = value; }
  function query(extra = {}) {
    return "?" + new URLSearchParams({class:active.cls,year:active.year,...extra});
  }
  async function api(path, options = {}) {
    const response = await fetch("/api/web/pbd/" + path, {
      credentials:"same-origin",cache:"no-store",redirect:"error",...options,
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw Error(result.error || "Rekod PBD tidak dapat dihubungi.");
    return result;
  }
  function json(method, data) {
    return {method,headers:{"Content-Type":"application/json"},body:JSON.stringify(data)};
  }
  async function run(fn) {
    if (busy) return;
    busy = true;
    $("controls").disabled = true;
    $("work").disabled = true;
    try { await fn(); }
    catch (error) { notify(error.message || "Rekod PBD belum dapat diproses."); }
    finally {
      busy = false;
      $("controls").disabled = false;
      $("work").disabled = false;
    }
  }
  function selector(options, value, blank) {
    const select = element("select");
    if (blank) select.add(new Option(blank, ""));
    for (const option of options) select.add(new Option(option, option));
    if (value) select.value = value;
    return select;
  }
  function label(text, input) {
    const node = element("label", text);
    node.append(input);
    return node;
  }
  function input(value, max) {
    const node = element("input");
    node.value = value || "";
    node.maxLength = max;
    return node;
  }
  function updateRosterSummary() {
    const count = students.filter(student => student.name.trim()).length;
    $("roster-summary").textContent = "Senarai murid (" + count + ")" +
      (rosterDirty ? " · Belum disimpan" : "");
  }
  function renderRoster() {
    const host = $("roster-rows");
    host.replaceChildren();
    students.forEach((student, index) => {
      const row = element("div");
      row.className = "pbd-student pbd-student-fields";
      const name = input(student.name, 120), code = input(student.code, 20);
      const remove = element("button", "Buang dari senarai");
      remove.type = "button";
      name.addEventListener("input", () => {
        student.name = name.value;
        rosterDirty = true;
        updateRosterSummary();
      });
      code.addEventListener("input", () => {
        student.code = code.value;
        rosterDirty = true;
        updateRosterSummary();
      });
      remove.addEventListener("click", () => {
        students.splice(index,1);
        rosterDirty = true;
        renderRoster();
      });
      row.append(label("Nama murid",name),label("Kod murid (pilihan)",code),remove);
      host.append(row);
    });
    if (!students.length) host.append(element("p","Belum ada nama dalam senarai ini."));
    updateRosterSummary();
  }
  function editAllowed() {
    if (rosterDirty || $("paste-input").value.trim()) {
      notify("Selesaikan perubahan senarai murid dahulu.");
      return false;
    }
    return !recordDirty || window.confirm("Buang perubahan rekod yang belum disimpan?");
  }
  function newEditor(kind, seed = {}, record = null) {
    if (!students.length && !record) {
      if (seed.lesson) pendingLesson = seed;
      $("roster").open = true;
      notify("Simpan senarai murid sebelum merekod PBD.");
      return;
    }
    pendingLesson = null;
    const report = kind === "report";
    const details = record?.details || {};
    current = {id:record?.id || crypto.randomUUID(),version:record?.version || "",kind};
    $("editor-heading").textContent = report ? "Rekod Tahap Penguasaan" : "Rekod pentaksiran";
    $("lesson-label").textContent = report ? "Bidang / Tema / Kemahiran" : "Lesson/PdP";
    $("assessment-fields").hidden = report;
    $("report-fields").hidden = !report;
    $("bulk").hidden = report;
    $("delete").hidden = !record;
    $("criteria1").required = !report;
    $("period").required = report;
    for (const key of fields) $(key).value = details[key] || seed[key] || "";
    $("date").value = record?.record_date || seed.date || today();
    $("subject").value = record?.subject || seed.subject || "";
    const assessed = new Map((details.entries || []).map(s => [s.id,s]));
    const shown = new Map(students.map(s => [s.id,s]));
    for (const [id, row] of assessed) if (!shown.has(id)) shown.set(id,row);
    $("entry-rows").replaceChildren();
    for (const [id, student] of shown) {
      const saved = assessed.get(id) || {};
      const row = element("div");
      row.className = "pbd-student";
      row.dataset.id = id;
      const checkbox = element("input");
      checkbox.type = "checkbox";
      checkbox.dataset.field = "selected";
      const title = element("label");
      title.append(checkbox," " + student.name + (student.code ? " ("+student.code+")" : ""));
      const inputs = element("div");
      inputs.className = "pbd-student-fields";
      const controls = report
        ? [["tp","Tahap Penguasaan",selector(levels,saved.tp,"Belum ditetapkan")]]
        : [["status1","Kriteria 1",selector(statuses,saved.status1)],
           ["status2","Kriteria 2",selector(statuses,saved.status2)],
           ["method","Kaedah",selector(methods,saved.method,"Pilih kaedah")],
           ["followup","Tindakan susulan",input(saved.followup,350)]];
      controls.push(["note","Bukti / Catatan",input(saved.note,350)]);
      for (const [key, caption, control] of controls) {
        control.dataset.field = key;
        inputs.append(label(caption,control));
      }
      row.append(title,inputs);
      $("entry-rows").append(row);
    }
    setSecondCriterion();
    $("editor").hidden = false;
    recordDirty = false;
    $("editor-heading").scrollIntoView({block:"nearest"});
  }
  function setSecondCriterion() {
    const enabled = Boolean($("criteria2").value.trim());
    for (const control of $("entry-rows").querySelectorAll('[data-field="status2"]')) {
      control.parentElement.hidden = !enabled;
    }
    $("bulk-criterion").options[1].disabled = !enabled;
    if (!enabled) $("bulk-criterion").value = "status1";
  }
  function historyFilter() {
    const selected = $("history-student").value;
    $("history-student").replaceChildren(new Option("Semua murid",""));
    for (const student of students) {
      $("history-student").add(new Option(student.name + (student.code ? " ("+student.code+")" : ""),student.id));
    }
    if (students.some(s => s.id === selected)) $("history-student").value = selected;
  }
  async function history() {
    const result = await api("records" + query({page,student:$("history-student").value}));
    const host = $("history");
    host.replaceChildren();
    if (!result.records.length) host.append(element("li","Tiada rekod untuk pilihan ini."));
    for (const record of result.records) {
      const row = element("li");
      const caption = [record.record_date,record.subject,record.kind === "report" ? record.period : record.lesson].filter(Boolean).join(" · ");
      const open = element("button",caption);
      open.type = "button";
      open.addEventListener("click", () => {
        if (!editAllowed()) return;
        void run(async () => {
          const data = await api("records/" + record.id + query());
          newEditor(data.kind,{},data);
        });
      });
      const download = element("a","CSV");
      download.href = "/api/web/pbd/records/" + record.id + query({format:"csv"});
      download.download = "Rekod_PBD_CikguLaju.csv";
      download.setAttribute("aria-label","Muat turun CSV " + caption);
      row.append(open,download);
      host.append(row);
    }
    $("prev").hidden = page <= 1;
    $("next").hidden = !result.more;
  }
  async function openClass(cls, year) {
    if (!cls || !/^(20[2-9][0-9]|2100)$/.test(year)) throw Error("Pilih kelas dan sesi akademik dahulu.");
    let result;
    try {
      result = await api("roster?" + new URLSearchParams({class:cls,year}));
    } catch (error) {
      if (active) {
        $("class").value = active.cls;
        $("year").value = active.year;
      }
      throw error;
    }
    pendingLesson = null;
    active = {cls,year};
    $("editor").hidden = true;
    current = null;
    $("paste-input").value = "";
    $("paste-panel").open = false;
    $("file").value = "";
    students = result.students;
    rosterVersion = result.version;
    rosterDirty = recordDirty = false;
    $("scope").textContent = cls + " · " + year;
    renderRoster();
    $("history-student").value = "";
    historyFilter();
    page = 1;
    $("history").replaceChildren();
    $("prev").hidden = $("next").hidden = true;
    $("roster").open = students.length === 0;
    $("work").hidden = false;
    notify("Rekod kelas dibuka.");
    try {
      await history();
    } catch {
      $("history").append(element("li","Sejarah belum dapat dimuatkan. Pilih penapis murid untuk cuba lagi."));
    }
  }
  async function loadClasses(selected) {
    const result = await api("classes");
    $("class").replaceChildren(new Option("Pilih kelas",""));
    for (const cls of result.classes) $("class").add(new Option(cls,cls));
    if (result.classes.includes(selected)) $("class").value = selected;
    if (!result.classes.length) notify("Tambah kelas dalam Profil & Akses dahulu.");
  }
  window.cikgulajuPbdLoad = () => {void run(() => loadClasses(active?.cls || $("class").value));};
  function confirmClassChange() {
    if ((rosterDirty || $("paste-input").value.trim()) &&
        !window.confirm("Buang perubahan senarai murid yang belum disimpan?")) return false;
    return !recordDirty || window.confirm("Buang perubahan rekod yang belum disimpan?");
  }
  function focusRoster() {
    $("roster").open = true;
    $("roster-summary").focus();
  }
  window.cikgulajuPbdOpenRoster = (cls, year) => {
    if (busy) return;
    const alreadyOpen = active?.cls === cls && active.year === year;
    if (!alreadyOpen && !confirmClassChange()) return;
    showWebView("pbd");
    if (alreadyOpen) {
      $("class").value = cls;
      $("year").value = year;
      focusRoster();
      return;
    }
    void run(async () => {
      await loadClasses(cls);
      $("year").value = year;
      await openClass(cls,year);
      focusRoster();
    });
  };
  window.cikgulajuPbdFromRph = (seed, selection) => {
    if (busy || !editAllowed()) return;
    document.querySelector('[data-web-view="pbd"]').focus();
    showWebView("pbd");
    void run(async () => {
      await loadClasses(seed.className);
      const year = seed.date.slice(0,4);
      $("year").value = year;
      await openClass(seed.className,year);
      let defaults = {};
      try {
        const response = await fetch("/api/web/rph/pbd-context?" + new URLSearchParams(selection),
          {credentials:"same-origin",cache:"no-store",redirect:"error"});
        if (response.ok) defaults = await response.json();
      } catch { /* The teacher can enter criteria from their RPH. */ }
      newEditor("assessment",{...seed,...defaults});
      if (students.length && !defaults.criteria1) notify("Isi kriteria pentaksiran daripada RPH yang digunakan.");
    });
  };
  $("open").addEventListener("click",() => {
    if (!confirmClassChange()) return;
    void run(() => openClass($("class").value,$("year").value));
  });
  $("add").addEventListener("click",() => {
    if (students.length >= 100) {notify("Maksimum 100 murid bagi setiap kelas.");return;}
    students.push({id:"",name:"",code:""});
    rosterDirty = true;
    renderRoster();
    $("roster-rows").lastElementChild?.querySelector("input")?.focus();
  });
  async function previewImport(file) {
    const form = new FormData();
    form.append("file",file);
    const result = await api("import",{method:"POST",body:form});
    const key = s => s.name.trim().toLocaleLowerCase("ms") + "\u0000" + s.code.trim().toLocaleLowerCase("ms");
    const existing = new Set(students.map(key));
    const additions = result.students.filter(s => {
      const id = key(s);
      if (existing.has(id)) return false;
      existing.add(id);
      return true;
    });
    if (students.length + additions.length > 100) throw Error("Senarai melebihi 100 murid.");
    if (additions.length) {
      students.push(...additions.map(s => ({id:"",...s})));
      rosterDirty = true;
      renderRoster();
    }
    notify(additions.length ? additions.length + " nama ditambah pada pratonton. Tekan Simpan senarai selepas semakan." : "Semua nama yang dimasukkan sudah ada dalam senarai.");
  }
  function pastedRoster(text) {
    const rows = text.split(/\r\n|\n|\r/).filter(line => line.trim())
      .map(line => line.split("\t").map(cell => cell.trim()));
    const header = value => value.toLowerCase().replace(/[^a-z0-9]/g,"");
    const nameHeadings = ["namamurid","namapenuhmurid","nama","namapenuh","studentname"];
    if (rows.length && nameHeadings.includes(header(rows[0][0]))) {
      const headings = rows.shift();
      if (headings.length > 2 ||
          (headings[1] && !["kodmurid","kodmuridpilihan"].includes(header(headings[1])))) {
        throw Error("Salin lajur Nama Murid dan Kod Murid sahaja.");
      }
    }
    if (!rows.length) throw Error("Tampal sekurang-kurangnya satu nama murid.");
    if (rows.length > 100) throw Error("Pilih satu kelas sahaja dengan maksimum 100 murid.");
    if (rows.some(row => row.length > 2 || !row[0])) {
      throw Error("Tampal satu nama setiap baris. Jika ada kod, tampal kod di lajur kedua.");
    }
    const quote = cell => '"' + cell.replace(/"/g,'""') + '"';
    return "Nama Murid,Kod Murid\n" +
      rows.map(([name,code = ""]) => [quote(name),quote(code)].join(",")).join("\n");
  }
  $("import").addEventListener("click",() => {void run(async () => {
    const file = $("file").files[0];
    if (!file) throw Error("Pilih fail Excel atau CSV dahulu.");
    await previewImport(file);
    $("file").value = "";
  });});
  $("paste-preview").addEventListener("click",() => {void run(async () => {
    const csv = pastedRoster($("paste-input").value);
    await previewImport(new File([csv],"senarai-murid.csv",{type:"text/csv"}));
    $("paste-input").value = "";
    $("paste-panel").open = false;
  });});
  $("save-roster").addEventListener("click",() => {void run(async () => {
    if ($("paste-input").value.trim()) {
      $("paste-panel").open = true;
      $("paste-input").focus();
      throw Error("Pratonton senarai yang ditampal sebelum menyimpan.");
    }
    const result = await api("roster" + query(),json("PUT",{version:rosterVersion,students}));
    students = result.students;
    rosterVersion = result.version;
    rosterDirty = false;
    renderRoster();
    historyFilter();
    notify(students.length + " murid disimpan untuk " + active.cls + " (" + active.year + ").");
    if (students.length && pendingLesson) newEditor("assessment",pendingLesson);
  });});
  for (const [control,kind] of [["new","assessment"],["report","report"]]) {
    $(control).addEventListener("click",() => {if (editAllowed()) newEditor(kind);});
  }
  $("criteria2").addEventListener("input",setSecondCriterion);
  $("editor").addEventListener("input",() => {recordDirty = true;});
  $("apply").addEventListener("click",() => {
    const chosen = [...$("entry-rows").querySelectorAll('[data-field="selected"]:checked')];
    if (!chosen.length) {notify("Tandakan kotak di sebelah nama murid dahulu.");return;}
    for (const box of chosen) {
      box.closest("[data-id]").querySelector('[data-field="' + $("bulk-criterion").value + '"]').value = $("bulk-status").value;
    }
    recordDirty = true;
    notify("Status " + chosen.length + " murid dikemas kini dalam rekod ini.");
  });
  $("editor").addEventListener("submit",event => {
    event.preventDefault();
    if (!current) return;
    void run(async () => {
      const body = {...current};
      for (const field of fields) body[field] = $(field).value;
      body.entries = [...$("entry-rows").children].map(row => {
        const entry = {id:row.dataset.id};
        for (const key of ["status1","status2","method","followup","note","tp"]) {
          entry[key] = row.querySelector('[data-field="'+key+'"]')?.value || "";
        }
        return entry;
      });
      const result = await api("records" + query(),json("POST",body));
      current.version = result.version;
      $("delete").hidden = false;
      recordDirty = false;
      notify("Rekod disimpan.");
      page = 1;
      await history();
    });
  });
  $("close").addEventListener("click",() => {
    if (recordDirty && !window.confirm("Buang perubahan rekod yang belum disimpan?")) return;
    $("editor").hidden = true;
    current = null;
    recordDirty = false;
  });
  $("delete").addEventListener("click",() => {
    if (!current?.version || !window.confirm("Padam rekod ini?")) return;
    void run(async () => {
      await api("records/" + current.id + query(),json("DELETE",{version:current.version}));
      $("editor").hidden = true;
      current = null;
      recordDirty = false;
      notify("Rekod dipadam.");
      page = 1;
      await history();
    });
  });
  $("history-student").addEventListener("change",() => {page = 1;void run(history);});
  $("prev").addEventListener("click",() => {page--;void run(history);});
  $("next").addEventListener("click",() => {page++;void run(history);});
})();
