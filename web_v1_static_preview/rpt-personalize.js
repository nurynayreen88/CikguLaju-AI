"use strict";
/* CikguLaju RPT 2027 browser-side school cover.
 * The teacher profile, private logo, and source PDF all stay on the same
 * authenticated first-party origin. PDF-lib is SELF-HOSTED in /assets;
 * this code never sends profile content to another server.
 * The source PDF isn't modified, uploaded or re-saved on the server.
 */
(function () {
  const ROOT="/api/rpt/2027/all/";
  const PROFILE="/api/web/teacher/profile";
  const LOGO="/api/web/teacher/school-logo";
  const MAX_PDF=25*1024*1024;

  function textValue(value,max) {
    return typeof value==="string" ? value.replace(/[\u0000-\u001f\u007f]/g," ").trim().slice(0,max) : "";
  }
  function lines(ctx,text,maxWidth,maxLines=2) {
    const words=text.split(/\s+/).filter(Boolean),result=[];
    let line="";
    for(const word of words) {
      const next=line ? line+" "+word : word;
      if(ctx.measureText(next).width<=maxWidth){line=next;continue;}
      if(line)result.push(line);
      line=word;
      if(result.length===maxLines-1)break;
    }
    if(result.length<maxLines&&line)result.push(line);
    if(result.length===0)result.push(text);
    const consumed=result.join(" ").split(/\s+/).filter(Boolean).length;
    if(consumed<words.length) {
      let last=result[result.length-1];
      while(last.length>1&&ctx.measureText(last+"…").width>maxWidth)last=last.slice(0,-1);
      result[result.length-1]=last+"…";
    }
    return result;
  }
  function paragraph(ctx,s,mid,y,maxWidth,lineHeight,maxLines=2) {
    const result=lines(ctx,s,maxWidth,maxLines);
    result.forEach((line,i)=>ctx.fillText(line,mid,y+i*lineHeight,maxWidth));
  }
  function drawCover(profile,logo,subject,year,ratio) {
    const W=1190,H=Math.round(W*ratio),mid=W/2;
    if(H<650||H>1200)throw Error("Saiz muka depan RPT tidak disokong.");
    const canvas=document.createElement("canvas");
    canvas.width=W;canvas.height=H;
    const ctx=canvas.getContext("2d");
    if(!ctx)throw Error("Pelayar tidak menyokong muka depan RPT.");
    ctx.fillStyle="#f5f9fb";ctx.fillRect(0,0,W,H);
    ctx.fillStyle="#153e5c";ctx.fillRect(0,0,W,98);
    ctx.fillStyle="#0c7669";ctx.fillRect(0,98,W,7);
    ctx.textAlign="center";ctx.textBaseline="middle";
    ctx.fillStyle="#fff";ctx.font="bold 34px system-ui,Arial,sans-serif";
    ctx.fillText("RANCANGAN PENGAJARAN TAHUNAN",mid,52,W-130);
    ctx.fillStyle="#0c7669";ctx.font="bold 52px system-ui,Arial,sans-serif";
    ctx.fillText("RPT 2027",mid,150);
    ctx.fillStyle="#173e60";ctx.font="bold 27px system-ui,Arial,sans-serif";
    paragraph(ctx,subject,mid,194,W-190,32,2);
    ctx.fillStyle="#56738c";ctx.font="bold 25px system-ui,Arial,sans-serif";
    ctx.fillText("TAHUN "+year,mid,252);

    const heightScale=H/840;
    const imageY=278*heightScale,imageSize=Math.min(155,158*heightScale);
    if(logo) {
      const iw=logo.naturalWidth||logo.width,ih=logo.naturalHeight||logo.height;
      if(iw<=0||ih<=0)throw Error("Logo sekolah tidak sah.");
      const factor=Math.min(imageSize/iw,imageSize/ih);
      ctx.drawImage(logo,mid-iw*factor/2,imageY+(imageSize-ih*factor)/2,iw*factor,ih*factor);
    } else {
      ctx.strokeStyle="#cddde5";ctx.lineWidth=2;
      ctx.strokeRect(mid-imageSize/2,imageY,imageSize,imageSize);
      ctx.fillStyle="#647c89";ctx.font="17px system-ui,Arial,sans-serif";
      ctx.fillText("Logo belum",mid,imageY+imageSize/2-12);
      ctx.fillText("dimuat naik",mid,imageY+imageSize/2+14);
    }
    let school=textValue(profile.school_name,160),teacher=textValue(profile.display_name,100);
    const schoolY=imageY+imageSize+44;
    ctx.fillStyle="#56738c";ctx.font="bold 17px system-ui,Arial,sans-serif";
    ctx.fillText("NAMA SEKOLAH",mid,schoolY);
    ctx.fillStyle="#173e60";ctx.font="bold 35px system-ui,Arial,sans-serif";
    paragraph(ctx,school||"Nama sekolah belum diisi",mid,schoolY+48,W-170,42,2);
    const teacherY=Math.min(H-112,schoolY+150);
    ctx.fillStyle="#56738c";ctx.font="bold 17px system-ui,Arial,sans-serif";
    ctx.fillText("DISEDIAKAN OLEH",mid,teacherY);
    ctx.fillStyle="#173e60";ctx.font="bold 25px system-ui,Arial,sans-serif";
    paragraph(ctx,teacher||"Nama guru belum diisi",mid,teacherY+35,W-170,28,2);
    ctx.fillStyle="#647c89";ctx.font="19px system-ui,Arial,sans-serif";
    const state=textValue(profile.state_name,40);
    if(state)ctx.fillText(state,mid,Math.min(H-54,teacherY+72));
    ctx.strokeStyle="#ccdde5";ctx.beginPath();ctx.moveTo(85,H-57);ctx.lineTo(W-85,H-57);ctx.stroke();
    ctx.fillStyle="#647c89";ctx.font="16px system-ui,Arial,sans-serif";
    ctx.fillText("CikguLaju AI • Maklumat Profil Guru • RPT DRAF (semak sebelum guna)",mid,H-30,W-120);
    return canvas;
  }
  async function fetchProfile() {
    const response=await fetch(PROFILE,{credentials:"same-origin",cache:"no-store",redirect:"error"});
    if(response.status===401)throw Error("Sila log masuk semula untuk mendapatkan maklumat guru.");
    if(!response.ok)throw Error("Profil Guru belum dapat dibaca. Buka Profil Guru, simpan dan cuba semula.");
    const body=await response.json();
    if(!body||typeof body.profile!=="object"||!body.profile)throw Error("Profil Guru tidak lengkap.");
    return body.profile;
  }
  async function fetchLogo() {
    const response=await fetch(LOGO,{credentials:"same-origin",cache:"no-store",redirect:"error"});
    if(response.status===404)return null;
    if(!response.ok)throw Error("Logo sekolah tidak dapat dibaca. Semak logo di Profil Guru.");
    const blob=await response.blob();
    if(blob.type!=="image/png"||blob.size<16||blob.size>460800)throw Error("Format logo tersimpan tidak sah.");
    const url=URL.createObjectURL(blob);
    try {
      const image=new Image();image.src=url;await image.decode();
      return image;
    }finally{URL.revokeObjectURL(url);}
  }
  async function sourcePdf(code,year) {
    if(!/^[a-z_]{2,36}$/.test(code)||!Number.isInteger(year)||year<2||year>6)
      throw Error("Pilihan RPT tidak sah.");
    const response=await fetch(ROOT+encodeURIComponent(code)+"/"+year+".pdf",{
      credentials:"same-origin",cache:"no-store",redirect:"error",
    });
    if(response.status===401)throw Error("Sila log masuk semula untuk muat turun RPT.");
    if(response.status===403)throw Error("Muat turun RPT memerlukan Rakan Pembangun atau langganan aktif.");
    if(!response.ok)throw Error("Fail RPT belum boleh dimuat turun (HTTP "+response.status+").");
    if(!response.headers.get("content-type")?.toLowerCase().startsWith("application/pdf"))
      throw Error("Pelayan tidak memulangkan fail PDF.");
    const pdf=await response.arrayBuffer();
    if(pdf.byteLength<8000||pdf.byteLength>MAX_PDF||
       String.fromCharCode(...new Uint8Array(pdf.slice(0,5)))!=="%PDF-")
      throw Error("Fail PDF sumber RPT tidak sah.");
    return pdf;
  }
  async function personalize(code,year,name) {
    const PDF=window.PDFLib;
    if(!PDF||!PDF.PDFDocument)throw Error("Modul PDF tidak dapat dimuatkan. Sila refresh halaman dan cuba semula.");
    const bytes=await sourcePdf(code,year);
    const profile=await fetchProfile();
    const logo=await fetchLogo();
    const original=await PDF.PDFDocument.load(bytes,{ignoreEncryption:false});
    const originalCount=original.getPageCount();
    if(originalCount<2||originalCount>300)
      throw Error("Bilangan halaman PDF sumber tidak sah.");
    const first=original.getPage(0).getSize();
    if(first.width<=first.height||first.width<400||first.width>1200||first.height<300||first.height>1000)
      throw Error("RPT perlu dalam susun atur A4 landskap.");
    const cover=drawCover(profile,logo,name,year,first.height/first.width);
    const coverBlob=await new Promise(resolve=>cover.toBlob(resolve,"image/png"));
    if(!coverBlob)throw Error("Muka depan tidak dapat disediakan.");
    // Insert into the loaded document itself. This retains the original
    // PDF page objects and existing link annotations, including internal
    // DSKP source jumps, instead of copying pages to another document.
    const page=original.insertPage(0,[first.width,first.height]);
    const image=await original.embedPng(await coverBlob.arrayBuffer());
    page.drawImage(image,{x:0,y:0,width:first.width,height:first.height});
    if(original.getPageCount()!==originalCount+1)
      throw Error("Muka depan RPT gagal digabungkan.");
    const output=await original.save({useObjectStreams:false});
    const filename="CIKGULAJU_RPT_"+code.toUpperCase()+"_TAHUN_"+year+"_2027_DRAF_SEKOLAH.pdf";
    const download=new Blob([output],{type:"application/pdf"});
    const url=URL.createObjectURL(download),link=document.createElement("a");
    try {
      link.href=url;link.download=filename;document.body.appendChild(link);link.click();link.remove();
    }finally {
      setTimeout(()=>URL.revokeObjectURL(url),30000);
    }
    return {
      hasSchool:!!textValue(profile.school_name,160),
      hasTeacher:!!textValue(profile.display_name,100),
      hasLogo:!!logo
    };
  }

  window.downloadCikguLajuRPT=async function(code,year,name,output,button) {
    if(!Number.isInteger(year)||year===1){
      if(output)output.textContent="Tahun 1 KP2027 belum dibuka untuk muat turun.";
      return false;
    }
    if(button)button.disabled=true;
    if(output)output.textContent="Menyediakan RPT dengan logo, nama sekolah dan nama guru daripada Profil Guru…";
    try {
      const status=await personalize(code,year,name);
      if(output)output.textContent="RPT berjaya disediakan dengan muka depan Profil Guru."+
        ((!status.hasLogo||!status.hasSchool||!status.hasTeacher) ?
          " Maklumat yang belum disimpan: "+
          [!status.hasLogo&&"logo",!status.hasSchool&&"nama sekolah",!status.hasTeacher&&"nama guru"].filter(Boolean).join(", ")+". Lengkapkannya dalam Profil Guru.":"");
      return true;
    } catch(error) {
      if(output)output.textContent=error?.message||"Muat turun RPT tidak berjaya. Sila cuba semula.";
      return false;
    } finally {
      if(button) {
        // Do not accidentally re-enable the main dropdown button if the
        // user selected disabled KP2027 Year1 during the async download.
        button.disabled=button.id==="rpt-download"
          ? (document.getElementById("rpt-subject")?.value!==code ||
             Number(document.getElementById("rpt-year")?.value)!==year)
          : false;
      }
    }
  };
})();
