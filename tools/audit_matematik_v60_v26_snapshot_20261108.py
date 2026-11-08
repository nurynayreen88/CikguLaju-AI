"""RETIRED — INCORRECT SOURCE for CikguLaju Matematik; do not use.

Historical experiment in PR #460 mistakenly treated v26.00 Science/curriculum
master as Telegram Matematik's source. The real Telegram _sm2542_rows() reads
verified_pdp_sequence_v2 from the checksum-pinned v25.99 Maths canonical DB.

Kept only as a fail-closed compatibility entrypoint so no audit accidentally
asserts 0/585 based on the wrong database. It makes NO database changes.
Use: python -m tools.audit_matematik_v60_v2599_native_source_20261108
"""


class WrongMathematicsSource(RuntimeError):
    pass


def audit_snapshot(*_args, **_kwargs):
    raise WrongMathematicsSource(
        "RETIRED: v26.00 is not Telegram Matematik's native PdP source. "
        "Use tools.audit_matematik_v60_v2599_native_source_20261108 "
        "(v25.99 verified_pdp_sequence_v2); never infer Maths lesson identity "
        "from the separate v26.00 Science master."
    )


if __name__ == "__main__":
    audit_snapshot()
