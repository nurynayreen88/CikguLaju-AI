import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
API = f'https://api.telegram.org/bot{BOT_TOKEN}'
state = {}

def send(cid, text, kb=None):
    p={'chat_id':cid,'text':text,'parse_mode':'HTML'}
    if kb: p['reply_markup']={'inline_keyboard':kb}
    requests.post(f'{API}/sendMessage',json=p,timeout=20)

def menu(cid):
    send(cid,"👩‍🏫 <b>CIKGULAJU AI</b>\n<i>Bahan mengajar siap dengan lebih pantas ⚡</i>\n\nPilih cara cikgu nak mula:\n\n⚡ <b>Cara Pantas</b> — pilih tahun/tingkatan, subjek dan tajuk.\n📚 <b>Guna Bahan Cikgu</b> — upload PDF atau gambar nota.",[[{'text':'⚡ CARA PANTAS','callback_data':'quick'}],[{'text':'📚 GUNA BAHAN CIKGU','callback_data':'material'}],[{'text':'⭐ Cikgu PRO','callback_data':'pro'},{'text':'👤 Akaun Saya','callback_data':'account'}]])

def quick(cid):
    send(cid,'⚡ <b>Apa yang cikgu nak hasilkan?</b>',[[{'text':'📝 Jana Soalan','callback_data':'task_questions'},{'text':'📋 Worksheet','callback_data':'task_worksheet'}],[{'text':'📚 RPH','callback_data':'task_rph'},{'text':'🧠 Soalan KBAT','callback_data':'task_kbat'}],[{'text':'⬅️ Menu Utama','callback_data':'home'}]])

def level(cid,task):
    state.setdefault(cid,{})['task']=task
    send(cid,'🏫 <b>Pilih tahap:</b>',[[{'text':'🏫 Sekolah Rendah','callback_data':'level_primary'}],[{'text':'🏫 Sekolah Menengah','callback_data':'level_secondary'}],[{'text':'⬅️ Kembali','callback_data':'quick'}]])

def year(cid,lv):
    state.setdefault(cid,{})['level']=lv
    vals=range(1,7) if lv=='primary' else range(1,6)
    prefix='year_' if lv=='primary' else 'form_'; label='Tahun' if lv=='primary' else 'Tingkatan'
    kb=[]
    vals=list(vals)
    for i in range(0,len(vals),2): kb.append([{'text':f'{label} {n}','callback_data':f'{prefix}{n}'} for n in vals[i:i+2]])
    kb.append([{'text':'⬅️ Menu Utama','callback_data':'home'}]); send(cid,'🎓 <b>Pilih Tahun / Tingkatan:</b>',kb)

def subjects(cid,label):
    state.setdefault(cid,{})['year']=label
    send(cid,f'📘 <b>{label}</b>\n\nPilih subjek:',[[{'text':'🇲🇾 Bahasa Melayu','callback_data':'sub_Bahasa Melayu'},{'text':'🇬🇧 Bahasa Inggeris','callback_data':'sub_Bahasa Inggeris'}],[{'text':'➗ Matematik','callback_data':'sub_Matematik'},{'text':'🔬 Sains','callback_data':'sub_Sains'}],[{'text':'🏛️ Sejarah','callback_data':'sub_Sejarah'},{'text':'☪️ Pendidikan Islam','callback_data':'sub_Pendidikan Islam'}],[{'text':'✏️ Subjek Lain','callback_data':'sub_Subjek Lain'}],[{'text':'⬅️ Menu Utama','callback_data':'home'}]])

def topic(cid,sub):
    s=state.setdefault(cid,{}); s['subject']=sub; s['waiting']='topic'
    send(cid,f'📚 <b>{sub}</b>\n\nTaip <b>tajuk / tema</b> yang cikgu mahu.\n\nContoh: Pecahan, Elektrik, Kata Adjektif.')

def qtype(cid):
    send(cid,'📝 <b>Pilih jenis soalan:</b>',[[{'text':'🔘 Objektif','callback_data':'qt_Objektif'},{'text':'✍️ Struktur','callback_data':'qt_Struktur'}],[{'text':'🧠 KBAT','callback_data':'qt_KBAT'},{'text':'🔀 Campuran','callback_data':'qt_Campuran'}]])

def amount(cid,kind):
    state.setdefault(cid,{})['qtype']=kind
    send(cid,'🔢 <b>Berapa soalan cikgu perlukan?</b>',[[{'text':str(n),'callback_data':f'amt_{n}'} for n in (5,10,20,30)]])

def callback(cid,d):
    if d=='home': menu(cid)
    elif d=='quick': quick(cid)
    elif d=='material': state.setdefault(cid,{})['waiting']='material'; send(cid,'📚 <b>GUNA BAHAN CIKGU</b>\n\nHantar 📄 PDF atau 📸 gambar nota.\n\nPembacaan AI akan disambungkan pada langkah seterusnya.')
    elif d=='pro': send(cid,'⭐ <b>CIKGU PRO</b>\n\n💳 <b>RM9.90/bulan</b> — harga pengenalan\n\n📝 Soalan & skema\n📋 Worksheet\n📚 RPH\n🧠 KBAT\n📥 Word/PDF\n⚡ Had lebih tinggi')
    elif d=='account': send(cid,'👤 <b>AKAUN SAYA</b>\n\nPelan: 🎁 Percubaan\nStatus: Aktif')
    elif d.startswith('task_'): level(cid,d[5:])
    elif d=='level_primary': year(cid,'primary')
    elif d=='level_secondary': year(cid,'secondary')
    elif d.startswith('year_'): subjects(cid,'Tahun '+d[5:])
    elif d.startswith('form_'): subjects(cid,'Tingkatan '+d[5:])
    elif d.startswith('sub_'): topic(cid,d[4:])
    elif d.startswith('qt_'): amount(cid,d[3:])
    elif d.startswith('amt_'):
        s=state.setdefault(cid,{}); s['amount']=d[4:]
        send(cid,f"✅ <b>Pilihan Cikgu</b>\n\n🎓 {s.get('year','-')}\n📚 {s.get('subject','-')}\n📖 {s.get('topic','-')}\n📝 {s.get('qtype','-')}\n🔢 {s['amount']} soalan\n\n🤖 Sedia untuk dijana dengan AI.",[[{'text':'✨ Jana Dengan AI','callback_data':'generate'}],[{'text':'🏠 Menu Utama','callback_data':'home'}]])
    elif d=='generate': send(cid,'🤖 <b>Asas bot sudah siap.</b>\n\nLangkah seterusnya kita sambungkan Gemini untuk jana soalan + skema sebenar.')

@app.route('/')
def index(): return jsonify({'status':'ok','app':'CikguLaju AI'})

@app.route('/webhook',methods=['POST'])
def webhook():
    u=request.get_json(silent=True) or {}
    if 'callback_query' in u:
        c=u['callback_query']; requests.post(f'{API}/answerCallbackQuery',json={'callback_query_id':c['id']},timeout=10); callback(c['message']['chat']['id'],c.get('data',''))
    elif 'message' in u:
        m=u['message']; cid=m['chat']['id']
        if m.get('text')=='/start': state[cid]={}; menu(cid)
        elif 'text' in m and state.get(cid,{}).get('waiting')=='topic':
            state[cid]['topic']=m['text'].strip(); state[cid].pop('waiting',None); qtype(cid) if state[cid].get('task') in ('questions','kbat') else send(cid,'✅ Tajuk diterima. Fungsi AI ini akan disambungkan seterusnya.')
        elif 'document' in m or 'photo' in m: send(cid,'✅ Bahan diterima. Pembacaan PDF/gambar oleh AI akan disambungkan seterusnya.')
    return jsonify({'ok':True})

@app.route('/setup-webhook')
def setup_webhook():
    if not BOT_TOKEN or not WEBHOOK_URL: return jsonify({'ok':False,'error':'Tetapkan BOT_TOKEN dan WEBHOOK_URL dahulu'}),500
    url=WEBHOOK_URL.rstrip('/')+'/webhook'; r=requests.post(f'{API}/setWebhook',json={'url':url},timeout=20); return jsonify({'webhook':url,'telegram':r.json()})

if __name__=='__main__': app.run(host='0.0.0.0',port=int(os.getenv('PORT','10000')))
