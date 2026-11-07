/* Test the actual browser original-cover stamping function with all 56
 * authentic source RPT PDFs and synthetic teacher details only.
 * The original page count and internal links MUST be retained.
 */
"use strict";
const fs=require("fs");
const path=require("path");
const assert=require("assert");
const crypto=require("crypto");
const PDF=require("../web_v1_static_preview/pdf-lib.min.js");
const {fillOriginalCover,validatedLayout,fitText}=require("../web_v1_static_preview/rpt-personalize.js");
const root=path.join(__dirname,"..","rpt_2027","web_2027_pdfs");
const manifest=JSON.parse(fs.readFileSync(path.join(root,"manifest.json"),"utf8"));
const layout=JSON.parse(fs.readFileSync(path.join(root,"original_cover_layout_verified.json"),"utf8"));
const tinyPng=Buffer.from("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGP4z8DwHwAFAAH/iZk9HQAAAABJRU5ErkJggg==","base64");
const outputDir=process.argv[2]||"";
const write=!!outputDir;

async function main(){
  assert.strictEqual(manifest.count,56);
  assert.strictEqual(Object.keys(layout.source_sha256_by_subject_year).length,56);
  if(write)fs.mkdirSync(outputDir,{recursive:true});
  let files=0,outputs=0,callCount=0;
  const observed=new Set();
  for(const [key,entry] of Object.entries(manifest.files)){
    const subject=key.split(":")[0];
    const source=fs.readFileSync(path.join(root,entry.path));
    const originalHash=crypto.createHash("sha256").update(source).digest("hex");
    assert.strictEqual(originalHash,entry.sha256,key);
    validatedLayout(layout,key,entry.sha256);
    const doc=await PDF.PDFDocument.load(source);
    const pages=doc.getPageCount();
    assert.strictEqual(pages,entry.pages,key);
    const originalSize=doc.getPage(0).getSize();
    const texts=[];
    const res=await fillOriginalCover(doc,{
      display_name:"Cikgu Contoh",
      school_name:"Sekolah Kebangsaan Laju"
    },tinyPng,layout,{
      PDFLib:PDF,
      textPng:async(value,box)=>{
        assert.ok(["Cikgu Contoh","Sekolah Kebangsaan Laju"].includes(value));
        assert.strictEqual(box.length,4);
        texts.push(value);
        callCount++;
        return tinyPng;
      }
    });
    assert.strictEqual(res.pages,pages);
    assert.strictEqual(doc.getPageCount(),pages,key);
    assert.strictEqual(res.hasLogo,true);
    assert.strictEqual(res.hasSchool,true);
    assert.strictEqual(res.hasTeacher,true);
    assert.deepStrictEqual(texts,["Sekolah Kebangsaan Laju","Cikgu Contoh"]);
    const output=await doc.save({useObjectStreams:false});
    const reopened=await PDF.PDFDocument.load(output);
    assert.strictEqual(reopened.getPageCount(),pages,key);
    assert.deepStrictEqual(reopened.getPage(0).getSize(),originalSize,key);
    // Validate 12 different subject examples visually outside stamped boxes.
    if(write&&!observed.has(subject)){
      fs.writeFileSync(path.join(outputDir,subject+".pdf"),output);
      fs.writeFileSync(path.join(outputDir,subject+".source.pdf"),source);
      observed.add(subject);outputs++;
    }
    // Filenames and original SHA are never mutated by our browser overlay.
    assert.strictEqual(crypto.createHash("sha256").update(
      fs.readFileSync(path.join(root,entry.path))).digest("hex"),entry.sha256);
    files++;
  }
  assert.strictEqual(files,56);
  assert.strictEqual(callCount,112);
  if(write)assert.strictEqual(outputs,12);

  // Unfilled private profile must not create invented names or add a page.
  const key="english:2",entry=manifest.files[key];
  const raw=fs.readFileSync(path.join(root,entry.path));
  const empty=await PDF.PDFDocument.load(raw);
  const before=empty.getPageCount();
  const blank=await fillOriginalCover(empty,{display_name:"",school_name:""},null,layout,{
    PDFLib:PDF,textPng:()=>{throw Error("No name overlay for empty profile");}
  });
  assert.strictEqual(blank.hasSchool,false);
  assert.strictEqual(blank.hasTeacher,false);
  assert.strictEqual(blank.hasLogo,false);
  assert.strictEqual(empty.getPageCount(),before);

  const context={font:"",measureText(text){
    const size=parseInt(this.font.match(/(\d+)px/)?.[1]||"16",10);
    return {width:text.length*size*.56};
  }};
  assert.deepStrictEqual(fitText(context,"SEKOLAH LAJU",465,27,2).lines,["SEKOLAH LAJU"]);
  console.log("ORIGINAL_COVER_56_REAL_PDFS_ZERO_EXTRA_PAGES_SUCCESS",files,
    "PDFs",callCount,"label fills",outputs,"render samples");
}
main().catch(e=>{console.error(e);process.exitCode=1;});
