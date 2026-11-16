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

  for(const year of [2,3,4,5,6]){
    const key="bahasa_cina_sjkc:"+year;
    const filename="RPT_2027_Bahasa_Cina_SJKC_Tahun_"+year+".pdf";
    const raw=fs.readFileSync(path.join(root,"..","sjkc","bahasa_cina",filename));
    const hash=crypto.createHash("sha256").update(raw).digest("hex");
    const sjkc=validatedLayout(layout,key,hash);
    assert.throws(()=>validatedLayout(layout,key,"0".repeat(64)));
    const doc=await PDF.PDFDocument.load(raw);
    const before=doc.getPageCount();
    const fills=[];
    const result=await fillOriginalCover(doc,{display_name:"Cikgu Tan",school_name:"SJK(C) Contoh"},
      tinyPng,sjkc,{PDFLib:PDF,textPng:async(value,box)=>{
        assert.ok(box[2]-box[0]>=200);
        assert.strictEqual(box[3]-box[1],30);
        fills.push(value);
        return tinyPng;
    }});
    assert.strictEqual(result.hasLogo,true);
    assert.deepStrictEqual(fills,["SJK(C) Contoh","Cikgu Tan"]);
    const output=await doc.save({useObjectStreams:false});
    const updated=await PDF.PDFDocument.load(output);
    assert.strictEqual(updated.getPageCount(),before);
    if(write){
      fs.writeFileSync(path.join(outputDir,"sjkc-"+year+".pdf"),output);
      fs.writeFileSync(path.join(outputDir,"sjkc-"+year+".source.pdf"),raw);
    }
  }

  for(const year of [2,3,4,5,6]){
    const bmKey="bahasa_melayu_sjk:"+year;
    const filename="RPT_2027_Bahasa_Melayu_SJK_Tahun_"+year+".pdf";
    const bmRaw=fs.readFileSync(path.join(root,"..","sjkc","bahasa_melayu",filename));
    const bmHash=crypto.createHash("sha256").update(bmRaw).digest("hex");
    const bmLayout=validatedLayout(layout,bmKey,bmHash);
    assert.throws(()=>validatedLayout(layout,bmKey,"0".repeat(64)));
    const bmDoc=await PDF.PDFDocument.load(bmRaw);
    const bmResult=await fillOriginalCover(bmDoc,{display_name:"Cikgu Tan",school_name:"SJK(C) Contoh"},
      tinyPng,bmLayout,{PDFLib:PDF,textPng:async()=>tinyPng});
    assert.strictEqual(bmResult.pages,year>=4?22:20);
    assert.ok(bmResult.hasLogo&&bmResult.hasSchool&&bmResult.hasTeacher);
    const bmOutput=await bmDoc.save();
    assert.strictEqual((await PDF.PDFDocument.load(bmOutput)).getPageCount(),year>=4?22:20);
    if(write){
      fs.writeFileSync(path.join(outputDir,"bm-sjk-"+year+".pdf"),bmOutput);
      fs.writeFileSync(path.join(outputDir,"bm-sjk-"+year+".source.pdf"),bmRaw);
    }
  }

  for(const year of [2,3,4,5,6]){
    const sainsKey="sains_sjkc:"+year;
    const sainsRaw=fs.readFileSync(path.join(root,"..","sjkc","sains","RPT_2027_Sains_SJKC_Tahun_"+year+".pdf"));
    const sainsHash=crypto.createHash("sha256").update(sainsRaw).digest("hex");
    const sainsLayout=validatedLayout(layout,sainsKey,sainsHash);
    assert.throws(()=>validatedLayout(layout,sainsKey,"0".repeat(64)));
    const sainsDoc=await PDF.PDFDocument.load(sainsRaw);
    const sainsResult=await fillOriginalCover(sainsDoc,{display_name:"Cikgu Tan",school_name:"SJK(C) Contoh"},
      tinyPng,sainsLayout,{PDFLib:PDF,textPng:async()=>tinyPng});
    assert.ok(sainsResult.hasLogo&&sainsResult.hasSchool&&sainsResult.hasTeacher);
    const sainsOutput=await sainsDoc.save();
    assert.strictEqual((await PDF.PDFDocument.load(sainsOutput)).getPageCount(),year===6?14:11);
    if(write){
      fs.writeFileSync(path.join(outputDir,"sains-sjkc-"+year+".pdf"),sainsOutput);
      fs.writeFileSync(path.join(outputDir,"sains-sjkc-"+year+".source.pdf"),sainsRaw);
    }
  }

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
