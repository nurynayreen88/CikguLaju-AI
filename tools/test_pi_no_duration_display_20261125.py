"""Check actual native display titles and retain teacher timetable metadata."""
from web.pi_rph_no_duration_display_20261125 import display_topic,display_state,display_rows

def main():
    assert display_topic("القرءان ١ جم + تسميع")=="القرءان + تسميع"
    assert display_topic("Al-Quran (60 minit)")=="Al-Quran"
    assert display_topic("Masa dan Waktu")=="Masa dan Waktu"
    state={"task":"rph","subject":"Pendidikan Islam","topic":"القرءان ١ جم + تسميع","rph_time":"08:00-09:00"}
    changed=display_state(state)
    assert changed["rph_time"]==state["rph_time"]
    assert state["topic"]!=changed["topic"]
    rows={"TAJUK":state["topic"],"AKTIVITI UTAMA":"Murid membaca selama 5 minit.","MASA":"08:00-09:00"}
    result=display_rows(state,rows)
    assert result["MASA"]==rows["MASA"] and result["AKTIVITI UTAMA"]==rows["AKTIVITI UTAMA"]
    print("PI_DURATION_DISPLAY_PASS",flush=True)

if __name__=="__main__":
    main()
