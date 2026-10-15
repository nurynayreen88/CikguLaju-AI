# PJPK Private V5 regression report — 15 October 2026

Corrected the stale V3/V4 legacy smoke test to account for V4's 10-record collision quarantine. This report corresponds to a locally generated private test bundle; it does not claim the bundle's app.py or DB was deployed or committed.

## Local test results
- `py_compile`: app.py, pjpk_rph_engine.py, preview_server.py and all test modules — PASS
- `test_direct_preview_gate.py` — PASS: 137 preview entries, both direct endpoints deny all 24 blocked IDs, sample PDF generated
- `test_collision_integration.py` — PASS: 137 mock PDF deliveries, 24 blocked, Telegram negative acknowledgement rejected
- `test_same_bot_integration.py` — PASS after updating stale assertions: 137 mock PDF deliveries, 24 blocked, original menu preserved
- DB `PRAGMA integrity_check` — PASS (`ok`)
- ZIP CRC — PASS

These are local unit/integration simulations. They are not proof of live Telegram delivery, Render deployment, official RPH template compatibility, or curriculum approval. Do not deploy as production.