# PJPK Tahun 5 PK — direct DSKP evidence (2026-10-24)

Source: `GuruBesar_DSKP_PJPK_Tahun_5.pdf` (user-owned Drive ID `1gjoKsy8ZHl0XEaXFZOrS2W-UHdRY5Q1l`). The three source-gate entries below were rechecked against actual DSKP text, not inferred from topic names.

| Entry | DSKP printed page | SK | SP verified in source | Remaining gate |
|---|---:|---|---|---|
| 2259 Pencegahan Penyakit Berjangkit | 127 | 6.1 Kemahiran mencegah dan mengurangkan faktor risiko penyakit dalam kehidupan harian | 6.1.1 symptom knowledge for demam campak, rubella, cacar air, beguk; 6.1.2 communicate ways to prevent their spread | exact textbook page, RPT identity, RPH runtime |
| 2260 Pengaruh Rakan Sebaya | 128 | 7.1 Kemahiran kecekapan psikososial untuk menjaga keselamatan diri | 7.1.1 identify peer influence; 7.1.2 evaluate peer influence; 7.1.3 generate ways to handle negative peer influence | exact textbook page, RPT identity, RPH runtime |
| 2261 Nutrien dan Label Makanan | 131 | 8.1 Amalan pemakanan sihat dan selamat | 8.1.1 importance of varied nutrients; 8.1.2 importance of reading nutrition labels; 8.1.3 analyse nutrient information on labels | exact textbook page, RPT identity, RPH runtime |

The textbook PDF `GuruBesar_BukuTeks_T5_PJPK_SEMAKAN_2017.pdf` (Drive ID `1M1kVxL7sliEUbi9vuuZ6llRVtmPjBuJE`) was accessible in metadata but its text fetch returned empty; therefore **no textbook page is asserted** and `production_ready` stays 0. Do not infer textbook pagination from DSKP printed page numbers.

Proposed RPH-specific activities to test, NOT production-ready:
- 2259: compare symptom cards for the four diseases; groups construct and explain practical spread-prevention messages, then peer-assess for accuracy.
- 2260: classify positive/negative peer-pressure scenarios; role-play assertive refusal and evaluate alternatives with a decision rubric.
- 2261: compare two actual food-label examples; identify nutrients, serving information and expiry, justify a choice using evidence from the label.

No database mutation or deployment is authorized by this evidence note alone.

## Direct textbook visual verification (2026-10-24)

The source PDF was fetched as raw binary (36,264,274 bytes; 114 PDF pages), because its text extraction was empty. Visual inspection of the actual pages established the following **printed textbook pages**, distinct from DSKP pages:

| Entry | Textbook printed page(s) | PDF physical page(s) | Visible content and SP cue |
|---|---|---|---|
| 2259 | 88–89 | 96–97 | “Demam Campak, Cacar Air, Rubela dan Beguk”; page 88 displays symptoms and prevention, corresponding to 6.1.1/6.1.2 |
| 2260 | 90–92 | 98–100 | “Pengaruh Rakan Sebaya”; printed page 90 visibly marks SP 7.1.1 and contrasts positive/negative influence |
| 2261 | 96–100 | 104–108 | “Nutrien Kesihatan”; printed page 99 (PDF 107) contains annotated nutrition label and visibly marks SP 8.1.2/8.1.3 |

**Correction to the earlier pending statement:** textbook pages are now verified visually. This resolves only the textbook-page gate for these three editorial entries; RPT lesson identity, end-to-end generation, one-page A4 render, and final teacher review are still pending. Keep `production_ready=0` until the remaining gates pass. Do not alter the 161-row original source CSV or old DB.
