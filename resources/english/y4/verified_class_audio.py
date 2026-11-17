"""Get Smart Plus 4 Class CD recordings checked against the printed activities.

See audits/english_y4_y5_october_audio_content_20261117.md for the spoken
content match, Teacher's Book page, activity, and source provenance.
"""

RECORDINGS = {
    "CD1 Track 9": ("1RCIp86VNulrP6AfPsA-Bt3wfksyQh55h",
                    "db22363201828814f068d0f46c490ea1ff42a27f1a05f3f3b46104227cf05044"),
    "CD1 Track 19": ("1I_6yoZHAyY7LQwsoJFNzr_m92aIQ4ETr",
                     "94e4c571df1b14ed9a88fabae344f69fdc8c147cd35abaa2e8a95236458332a9"),
    "CD2 Track 21": ("1ZjFEfvJuagEtcEAZuCzRs3AXrqUMMw",
                     "68a9923b2ceb054cd0e47210d69987819da27bd0bb6d7b5f9482ed97180ca692"),
    "CD2 Track 22": ("1sI2jDn8otlgH4pK_dyztrwuMY3azWlYl",
                     "c14c7937dfb39f587bba6fd172866014573d9375bd887b0f954d98c5b1850991"),
    "CD2 Track 25": ("1Lz-BPqFM6g0dLLe0MPxnM3CqTwvZh5yk",
                     "fb691b7199cc437150e773f0e3e849b94f06c0fdb16f8438ef981e5bda4349ae"),
    "CD2 Track 26": ("1PmJHMo3mOxKxUMJ145BpsmjypzhxJkHl",
                     "5521206e51d6970e77e8384fbacada40b07a27c0cb81e0f0e5ec114e82bebd4d"),
}

LESSON_TRACKS = {
    7: ("CD1 Track 9",),
    17: ("CD1 Track 19",),
    98: ("CD2 Track 21", "CD2 Track 22"),
    102: ("CD2 Track 25",),
    103: ("CD2 Track 26",),
}
