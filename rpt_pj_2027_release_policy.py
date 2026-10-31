"""Check final KPM/BKPP release evidence without editing the calendar."""
def audit_decision(rows):
    return any(len(row) >= 2 and row[0] == "KEPUTUSAN AUDIT AKHIR"
               and "FINAL VERIFIED" in row[1] for row in rows)

def publication_decision(rows):
    return any(len(row) >= 2 and row[0] == "Penerbitan"
               and "FINAL VERIFIED" in row[1] for row in rows)

def calendar_release_status(records, audit_rows, release_rows):
    legacy_count = sum("BELUM AUDIT" in
                       str(row.get("Status PdP Dikira", "")).upper()
                       for row in records.values())
    approved = (len(records) == 5840 and audit_decision(audit_rows)
                and publication_decision(release_rows))
    return {"approved": approved, "legacy_label_count": legacy_count,
            "requires_disclosure": legacy_count > 0}
