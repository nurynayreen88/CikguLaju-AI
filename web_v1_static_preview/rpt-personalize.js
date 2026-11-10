"use strict";
/* Fill ONLY the three existing placeholders on RPT2027 PDF PAGE 1.
 * No extra cover, page insertion or source upload; original PDF source is
 * immutable and unchanged. The teacher's private profile/logo never leave
 * this first-party browser session. Layout is locked to all 56 source SHAs.
 */
(function () {
  const ROOT="/api/rpt/2027/all/";
  const PROFILE="/api/web/teacher/profile";
  const LOGO="/api/web/teacher/school-logo";
  const LAYOUT="/assets/rpt-original-cover-layout.json";
  const MAX_PDF=25*1024*1024;

  function profileText(value,max,label){
    if(typeof value!=="string")return "";
    const clean=value.replace(/[\u0000-\u001f\u007f]/g," ").trim();
    if(clean.length>max)throw Error(label+" terlalu panjang untuk muka depan asal.");
    return clean;
  }
  function fitText(ctx,value,width,height,scale){
    const maxWidth=(width-8)*scale;
    // Prefer one line in the exact original blank field. Only a long name
    // may require two lines; never silently truncate identity information.
    for(let size=16;size>=10;size--){
      ctx.font="600 "+(size*scale)+"px system-ui,'Segoe UI',Arial,sans-serif";
      if(ctx.measureText(value).width<=maxWidth)return {size,lines:[value]};
    }
    const words=value.split(/\s+/).filter(Boolean);
    for(let size=14;size>=8;size--){
      ctx.font="600 "+(size*scale)+"px system-ui,'Segoe UI',Arial,sans-serif";
      const rows=[""];
      for(const word of words){
        const row=rows.length-1,next=rows[row]?rows[row]+" "+word:word;
        if(ctx.measureText(next).width<=maxWidth){
          rows[row]=next;continue;
        }
        if(ctx.measureText(word).width>maxWidth){rows.length=3;break;}
        rows.push(word);
        if(rows.length>2)break;
      }
      if(rows.length<=2 && rows.every(row=>row && ctx.measureText(row).width<=maxWidth)
          && size*2+3<=height) return {size,lines:rows};
    }
    throw Error("Nama terlalu panjang untuk ruang muka depan asal. Ringkaskan dalam Profil Guru.");
  }
  async function textPng(value,box){
    const width=box[2]-box[0],height=box[3]-box[1],scale=2;
    if(width<200||height<22||height>35)throw Error("Ruang nama dalam RPT tidak sah.");
    const canvas=document.createElement("canvas");
    canvas.width=Math.round(width*scale);
    canvas.height=Math.round(height*scale);
    const ctx=canvas.getContext("2d");
    if(!ctx)throw Error("Pelayar tidak menyokong isian muka depan RPT.");
    ctx.clearRect(0,0,canvas.width,canvas.height);
    ctx.textBaseline="middle";
    ctx.textAlign="left";
    ctx.fillStyle="#173d37";
    const fit=fitText(ctx,value,width,height,scale);
    const y=fit.lines.length===1 ? [height/2] : [height*0.29,height*0.74];
    ctx.font="600 "+(fit.size*scale)+"px system-ui,'Segoe UI',Arial,sans-serif";
    fit.lines.forEach((line,i)=>ctx.fillText(line,4*scale,y[i]*scale));
    const blob=await new Promise(resolve=>canvas.toBlob(resolve,"image/png"));
    if(!blob || blob.type!=="image/png")throw Error("Teks profil gagal dilukis pada RPT.");
    return new Uint8Array(await blob.arrayBuffer());
  }
  function dimensionsValid(first,layout){
    const w=first.width,h=first.height;
    return Number.isFinite(w)&&Number.isFinite(h)&&
      Math.abs(w-layout.page_width)<=layout.tolerance_pt&&
      Math.abs(h-layout.page_height)<=layout.tolerance_pt&&w>h;
  }
  function boxSafe(box,w,h){
    return Array.isArray(box)&&box.length===4&&
      box.every(x=>typeof x==="number"&&Number.isFinite(x))&&
      box[0]>=0&&box[1]>=0&&box[2]<=w&&box[3]<=h&&
      box[0]<box[2]&&box[1]<box[3];
  }
  function validatedLayout(layout,key,hash){
    if(!layout||layout.version!==1||
       layout.status!=="ORIGINAL_COVER_TEMPLATE_LOCKED_TO_56_SOURCE_PDF_SHA256" ||
       !layout.source_sha256_by_subject_year||
       Object.keys(layout.source_sha256_by_subject_year).length!==56||
       layout.source_sha256_by_subject_year[key]!==hash||
       !/^[a-f0-9]{64}$/.test(hash)||
       !Array.isArray(layout.identity_background_rgb)||
       layout.identity_background_rgb.length!==3||
       !layout.identity_background_rgb.every(x=>typeof x==="number"&&x>=0&&x<=1)){
      throw Error("Templat muka depan asal tidak sepadan dengan PDF RPT. Fail asal tidak diubah.");
    }
    for(const field of ["logo_interior_top_left","logo_image_safe_top_left",
                         "school_row_top_left","teacher_row_top_left"]){
      if(!boxSafe(layout[field],layout.page_width,layout.page_height))
        throw Error("Kedudukan ruang muka depan RPT tidak disahkan.");
    }
    return layout;
  }
  async function fillOriginalCover(doc,profile,logoBytes,layout,options={}){
    const PDF=options.PDFLib||(typeof window!=="undefined"?window.PDFLib:null);
    if(!PDF||!PDF.PDFDocument)throw Error("Modul PDF tidak tersedia.");
    const before=doc.getPageCount();
    if(before<2||before>300)throw Error("Bilangan halaman RPT tidak sah.");
    const page=doc.getPage(0),size=page.getSize();
    if(!dimensionsValid(size,layout))throw Error("Susun atur muka depan RPT tidak sepadan.");
    const school=profileText(profile?.school_name,160,"Nama sekolah");
    const teacher=profileText(profile?.display_name,100,"Nama guru");
    const fillImage=options.textPng||textPng;
    if(logoBytes){
      const image=await doc.embedPng(logoBytes);
      const interior=layout.logo_interior_top_left;
      const region=layout.logo_image_safe_top_left;
      const maxW=region[2]-region[0],maxH=region[3]-region[1];
      const scale=Math.min(maxW/image.width,maxH/image.height);
      if(!Number.isFinite(scale)||scale<=0)throw Error("Dimensi logo tidak sah.");
      const width=image.width*scale,height=image.height*scale;
      // Cover only the words "LOGO SEKOLAH" inside its original frame,
      // leaving all four outer frame lines entirely untouched.
      page.drawRectangle({x:interior[0],y:size.height-interior[3],
        width:interior[2]-interior[0],height:interior[3]-interior[1],
        color:PDF.rgb(1,1,1)});
      page.drawImage(image,{
        x:(region[0]+region[2]-width)/2,
        y:size.height-(region[1]+region[3]+height)/2,
        width,height
      });
    }
    for(const [value,field] of [[school,"school_row_top_left"],[teacher,"teacher_row_top_left"]]){
      if(!value)continue; // no fabricated placeholder identity
      const box=layout[field];
      // Draw only over original underscores, within the ORIGINAL colored
      // identity panel. Preserve "NAMA SEKOLAH"/"NAMA GURU" on the left.
      const image=await doc.embedPng(await fillImage(value,box));
      page.drawRectangle({x:box[0],y:size.height-box[3],
        width:box[2]-box[0],height:box[3]-box[1],
        color:PDF.rgb(...layout.identity_background_rgb)});
      page.drawImage(image,{x:box[0],y:size.height-box[3],
        width:box[2]-box[0],height:box[3]-box[1]});
    }
    if(doc.getPageCount()!==before)throw Error("Bilangan halaman RPT telah berubah.");
    return {hasLogo:!!logoBytes,hasSchool:!!school,hasTeacher:!!teacher,
            pages:before,document:doc};
  }
  async function fetchProfile(){
    const response=await fetch(PROFILE,{
      credentials:"same-origin",cache:"no-store",redirect:"error"
    });
    if(response.status===401)throw Error("Sila log masuk semula untuk mendapatkan Profil Guru.");
    if(!response.ok)throw Error("Profil Guru belum dapat dibaca. Simpan Profil Guru dan cuba lagi.");
    const body=await response.json();
    if(!body||!body.profile||typeof body.profile!=="object")throw Error("Profil Guru belum tersedia.");
    return body.profile;
  }
  async function fetchLogo(){
    const response=await fetch(LOGO,{
      credentials:"same-origin",cache:"no-store",redirect:"error"
    });
    if(response.status===404)return null;
    if(!response.ok)throw Error("Logo sekolah tidak dapat dibaca. Semak Profil Guru.");
    const blob=await response.blob();
    if(blob.type!=="image/png"||blob.size<16||blob.size>460800)
      throw Error("Logo sekolah tersimpan tidak sah.");
    return new Uint8Array(await blob.arrayBuffer());
  }
  async function coverLayout(){
    const response=await fetch(LAYOUT,{
      credentials:"same-origin",cache:"no-store",redirect:"error"
    });
    if(!response.ok)throw Error("Ruang muka depan RPT belum dapat disahkan.");
    return response.json();
  }
  async function sourcePdf(code,year){
    if(!/^[a-z_]{2,36}$/.test(code)||!Number.isInteger(year)||year<2||year>6)
      throw Error("Pilihan RPT tidak sah.");
    const response=await fetch(ROOT+encodeURIComponent(code)+"/"+year+".pdf",{
      credentials:"same-origin",cache:"no-store",redirect:"error"
    });
    if(response.status===401)throw Error("Sila log masuk semula untuk muat turun RPT.");
    if(response.status===403)throw Error("Akses fail RPT tidak dibenarkan.");
    if(!response.ok)throw Error("Fail RPT belum tersedia (HTTP "+response.status+").");
    if(!response.headers.get("content-type")?.toLowerCase().startsWith("application/pdf"))
      throw Error("Pelayan tidak memulangkan PDF RPT.");
    const bytes=await response.arrayBuffer();
    if(bytes.byteLength<8000||bytes.byteLength>MAX_PDF||
       String.fromCharCode(...new Uint8Array(bytes.slice(0,5)))!=="%PDF-")
      throw Error("Fail PDF asal tidak sah.");
    const declaredSha=response.headers.get("X-RPT-Source-SHA256");
    if(!declaredSha||!/^[a-f0-9]{64}$/.test(declaredSha))
      throw Error("PDF belum disahkan untuk pengisian ruang asal.");
    if(!crypto.subtle)throw Error("Pelayar perlu sambungan HTTPS untuk semakan PDF.");
    const actualSha=Array.from(new Uint8Array(
      await crypto.subtle.digest("SHA-256",bytes)
    )).map(b=>b.toString(16).padStart(2,"0")).join("");
    if(actualSha!==declaredSha)throw Error("Checksum PDF tidak sepadan. Muat turun dibatalkan.");
    return {bytes,sha:actualSha,paidCover:response.headers.get("X-RPT-Personalization-Allowed")==="1"};
  }
  async function downloadWithOriginalCover(code,year,openedViewer=null,mobileRequest=false){
    const source=await sourcePdf(code,year);
    // Entitlement is evaluated on the server for this PDF request.
    // Without an active paid entitlement, never fetch private profile or logo
    // and never invoke the PDF stamping library. Keep source bytes untouched.
    let output=source.bytes;
    let result={hasLogo:false,hasSchool:false,hasTeacher:false,
                personalized:false};
    if(source.paidCover){
      const PDF=window.PDFLib;
      if(!PDF||!PDF.PDFDocument)
        throw Error("Modul PDF tidak dapat dimuatkan. Refresh laman Web dan cuba semula.");
      const layout=validatedLayout(await coverLayout(),code+":"+year,source.sha);
      const profile=await fetchProfile();
      const logo=await fetchLogo();
      const original=await PDF.PDFDocument.load(source.bytes,{ignoreEncryption:false});
      result=await fillOriginalCover(original,profile,logo,layout,{PDFLib:PDF});
      result.personalized=true;
      output=await original.save({useObjectStreams:false});
    }
    const download=new Blob([output],{type:"application/pdf"});
    const url=URL.createObjectURL(download);
    const filename="CIKGULAJU_RPT_"+code.toUpperCase()+"_TAHUN_"+year+
      (result.personalized?"_2027_ISI_PROFIL.pdf":"_2027_PERCUMA.pdf");
    function downloadLink(doc){
      const link=doc.createElement("a");
      link.href=url;
      link.download=filename;
      link.textContent="Simpan PDF RPT";
      link.style.cssText="display:inline-block;background:#087568;color:white;padding:14px 20px;border-radius:12px;font:bold 17px system-ui;text-decoration:none;";
      return link;
    }
    // Chrome may treat navigating to blob: PDF as a download and leave the
    // preopened phone tab empty. Keep a visible, user-activated save link in
    // that same tab instead. This also works when Safari blocks async clicks.
    if(openedViewer && !openedViewer.closed){
      try{
        const doc=openedViewer.document;
        const title=doc.createElement("h1");
        title.textContent="RPT 2027 siap";
        const note=doc.createElement("p");
        note.textContent=result.personalized?"PDF bersama profil sekolah sudah disediakan. Tekan Simpan PDF RPT. Pautan sah selama 10 minit.":"PDF percuma tanpa nama guru, nama sekolah dan logo sudah disediakan. Tekan Simpan PDF RPT. Pautan sah selama 10 minit.";
        doc.body.style.cssText="margin:0;min-height:100vh;padding:28px 18px;box-sizing:border-box;font-family:system-ui,Arial,sans-serif;background:#f0f7f5;color:#174353;";
        doc.body.replaceChildren(title,note,downloadLink(doc));
        setTimeout(()=>URL.revokeObjectURL(url),600000);
        result.delivery="phone-tab-link";
        return result;
      }catch(error){
        try{openedViewer.close();}catch(_ignored){}
      }
    }
    if(mobileRequest){
      // Popup-blocked browser: show a link that the teacher can tap with a
      // fresh gesture, not an async synthetic click that may silently fail.
      const previous=document.getElementById("rpt-prepared-manual-link");
      if(previous)previous.remove();
      const manual=downloadLink(document);
      manual.id="rpt-prepared-manual-link";
      const status=document.getElementById("rpt-status");
      if(status)status.insertAdjacentElement("afterend",manual);
      else document.body.appendChild(manual);
      setTimeout(()=>{manual.remove();URL.revokeObjectURL(url);},600000);
      result.delivery="phone-inline-link";
      return result;
    }
    const link=downloadLink(document);
    try{
      document.body.appendChild(link);link.click();link.remove();
    }finally{setTimeout(()=>URL.revokeObjectURL(url),30000);}
    result.delivery="desktop-auto";
    return result;
  }
  if(typeof window!=="undefined"){
    window.downloadCikguLajuRPT=async function(code,year,name,output,button,openedViewer=null,mobileRequest=false){
      if(!Number.isInteger(year)||year===1){
        if(output)output.textContent="Tahun 1 KP2027 belum dibuka untuk muat turun.";
        return false;
      }
      if(button)button.disabled=true;
      if(output)output.textContent="Menyediakan RPT 2027. Identiti sekolah hanya dicetak untuk akaun berbayar aktif…";
      try{
        const status=await downloadWithOriginalCover(code,year,openedViewer,mobileRequest);
        if(output)output.textContent=(status.delivery==="phone-tab-link"?"PDF siap pada tab baharu. Tekan Simpan PDF RPT di tab itu. ":status.delivery==="phone-inline-link"?"PDF siap. Tekan Simpan PDF RPT di bawah untuk menyimpan. ":"PDF RPT berjaya dimuat turun. ")+
          (status.personalized
           ? "Muka depan asal diisi untuk akaun berbayar aktif, tiada halaman tambahan."+
             ((!status.hasLogo||!status.hasSchool||!status.hasTeacher)
               ? " Maklumat belum diisi: "+
                 [!status.hasLogo&&"logo sekolah",!status.hasSchool&&"nama sekolah",
                  !status.hasTeacher&&"nama guru"].filter(Boolean).join(", ")+
                 ". Lengkapkan dalam Profil Guru.":"")
           : "Versi percuma tanpa nama guru, nama sekolah atau logo. Maklumat Profil Guru tetap disimpan.");
        return true;
      }catch(error){
        if(openedViewer && !openedViewer.closed){
          try{openedViewer.close();}catch(_ignored){}
        }
        if(output)output.textContent=error?.message||"Muat turun RPT tidak berjaya.";
        return false;
      }finally{
        if(button)button.disabled=button.id==="rpt-download"
          ?(document.getElementById("rpt-subject")?.value!==code||
            Number(document.getElementById("rpt-year")?.value)!==year):false;
      }
    };
  }
  // CI can test the EXACT function used by the browser, with a synthetic
  // PNG text generator and no real user credentials.
  if(typeof module!=="undefined"&&module.exports){
    module.exports={fillOriginalCover,validatedLayout,profileText,fitText};
  }
})();
