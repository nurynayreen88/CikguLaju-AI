/* PDF-lib build smoke test on 12 authentic RPT sources.
 * Synthetic transparent logo PNG and no private user data.
 * Validate the cover is inserted, not replacing any source page.
 */
const fs=require("fs");
const path=require("path");
const assert=require("assert");
const PDFLib=require("../web_v1_static_preview/pdf-lib.min.js");
const root=path.join(__dirname,"..","rpt_2027","web_2027_pdfs");
const manifest=JSON.parse(fs.readFileSync(path.join(root,"manifest.json"),"utf8"));
const png=Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9WlJeuAAAAAASUVORK5CYII=","base64");
async function main(){
  assert.strictEqual(manifest.count,56);
  const subjects=new Set(Object.keys(manifest.files).map(x=>x.split(":")[0]));
  assert.strictEqual(subjects.size,12);
  let count=0;
  for(const subject of subjects){
    const entry=manifest.files[subject+":"+(subject==="rbt"||subject==="sejarah"?4:2)];
    assert.ok(entry,subject);
    const source=fs.readFileSync(path.join(root,entry.path));
    const loaded=await PDFLib.PDFDocument.load(source);
    const before=loaded.getPageCount();
    const first=loaded.getPage(0).getSize();
    assert.ok(first.width>first.height);
    const cover=loaded.insertPage(0,[first.width,first.height]);
    const embedded=await loaded.embedPng(png);
    cover.drawImage(embedded,{x:15,y:15,width:25,height:25});
    const output=await loaded.save({useObjectStreams:false});
    const checked=await PDFLib.PDFDocument.load(output);
    assert.strictEqual(checked.getPageCount(),before+1);
    assert.strictEqual(fs.readFileSync(path.join(root,entry.path)).length,source.length);
    count++;
  }
  assert.strictEqual(count,12);
  console.log("RPT2027_PDFLIB_AUTHENTIC_12_SUBJECTS_PERSONAL_COVER_PASS");
}
main().catch(error=>{console.error(error);process.exitCode=1;});
