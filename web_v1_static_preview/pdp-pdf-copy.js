/* Extract the selected pages from the teacher's own PDF in this browser. */
(() => {
 "use strict";

 function createAction(item, status) {
  const spec = item?.pdf;
  const maxPages = 6;
  if (item?.type !== "textbook" || item.action !== "local-pdf" || !spec ||
      !Number.isInteger(spec.size) || spec.size <= 0 || spec.size > 110000000 ||
      !/^[a-f0-9]{64}$/.test(spec.sha256) ||
      !Number.isInteger(spec.start) || !Number.isInteger(spec.end) ||
      spec.start < 0 || spec.end < spec.start || spec.end - spec.start + 1 > maxPages ||
      !/^CikguLaju_Sains_(?:ST[12356]|SCI-Y[23])-PDP-\d{3}_ms_\d{1,2}-\d{1,2}\.pdf$/.test(spec.filename) ||
      typeof spec.source !== "string" || typeof spec.authors !== "string") return null;

  return () => {
   const input = document.createElement("input");
   input.type = "file";
   input.accept = ".pdf,application/pdf";
   input.hidden = true;
   document.body.append(input);
   input.addEventListener("cancel", () => input.remove(), {once:true});
   input.addEventListener("change", async () => {
    const file = input.files[0];
    input.remove();
    if (!file) return;
    const mismatch = "Pilih PDF asal yang sepadan dengan edisi buku ini. " + spec.source;
    try {
     status.textContent = "Menyemak PDF asal…";
     if (file.size !== spec.size) throw new Error(mismatch);
     const raw = await file.arrayBuffer();
     const digest = await crypto.subtle.digest("SHA-256", raw);
     const hex = Array.from(new Uint8Array(digest), n => n.toString(16).padStart(2,"0")).join("");
     if (hex !== spec.sha256) throw new Error(mismatch);

     const {PDFDocument} = window.PDFLib;
     const source = await PDFDocument.load(raw);
     if (spec.end >= source.getPageCount()) throw new Error(mismatch);
     const output = await PDFDocument.create();
     const indexes = Array.from({length:spec.end-spec.start+1}, (_, i) => spec.start+i);
     for (const page of await output.copyPages(source,indexes)) output.addPage(page);
     output.setTitle(spec.source);
     output.setAuthor(spec.authors);
     output.setSubject("Salinan untuk pengajaran dan pembelajaran");

     const pdf = new Blob([await output.save()], {type:"application/pdf"});
     const url = URL.createObjectURL(pdf);
     const link = document.createElement("a");
     link.href = url;
     link.download = spec.filename;
     document.body.append(link);
     link.click();
     link.remove();
     setTimeout(() => URL.revokeObjectURL(url),30000);
     status.textContent = "Salinan PdP sedia dimuat turun. " + spec.source + ". Penulis: " + spec.authors + ".";
    } catch (error) {
     status.textContent = error?.message === mismatch ? mismatch : "PDF belum dapat diproses. Cuba semula.";
    }
   }, {once:true});
   input.click();
  };
 }

 window.cikgulajuPdpPdfCopy = createAction;
})();
