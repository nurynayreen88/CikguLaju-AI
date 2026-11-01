# Web V1 — Shared Telegram Account Integration Contract (staging)

This document describes the **planned** integration. No production authentication or database connection is enabled.

## Server-side flow
1. User authenticates through a verified Telegram login flow. Validate Telegram-signed identity **on the server**; never trust a Telegram ID or status sent in a query parameter or form field.
2. Establish a secure, HttpOnly, SameSite session cookie over HTTPS; rotate it at login and expire it at logout.
3. Resolve the authenticated Telegram user ID against the existing shared account store using a read-only lookup. Do not create a second account or a separate free-credit balance.
4. Read the **existing verified** lifetime entitlement, VIP expiry and remaining trial credits. Field/table names must be confirmed against the production schema before mapping; no guessed migrations.
5. Call `display_trusted_account()` with a trusted snapshot and return `status`, `access` and `authenticated` from `GET /api/account/status`. Set `Cache-Control: no-store, private`.
6. All generation, RPT and download authorization must be checked again on the backend. Frontend labels do not grant access.

## Invariants
- Effective access priority: Rakan Pembangun > active VIP > Percuma.
- Trial balance is hidden, not reset, when paid access is active.
- A trial credit is deducted **only after successful generation**, atomically in the shared backend.
- On VIP expiry, restore the original remaining free credits unless lifetime access exists.
- Free accounts may see locked RPT and AI timetable features but cannot use them.
- Failed authentication, missing account records, invalid data or database outages must not grant paid access.
- Avoid writing to Telegram production, changing schema or enabling paid features without explicit review.

## Preview state
The isolated Flask preview's `/api/account/status` intentionally returns HTTP 401. The static Render preview is not an authenticated application. No live payment, credit deduction, downloads or Telegram login are connected.

## Required before enabling
- Confirm production account schema and expiry timezone semantics.
- Implement and independently test Telegram signature verification and session security.
- Test same-user access across Telegram and Web, including 0 credits, expired VIP and lifetime overrides.
- Review authorization and database transactions before deploying to production.
