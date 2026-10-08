
# === v26.16 PJPK staging-only verified PdP activation ===
try:
    from scripts.activate_pjpk_v26_16 import install as _pjpk_v2616_install
    _pjpk_v2616_install(globals())
    CIKGULAJU_PJPK_V2616_STAGING_ACTIVE = True
except Exception as _pjpk_v2616_error:
    CIKGULAJU_PJPK_V2616_STAGING_ACTIVE = False
    print('PJPK v26.16 staging fallback:', repr(_pjpk_v2616_error), flush=True)
# === END v26.16 ===
