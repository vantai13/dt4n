# Phase G local custody waiver — user-attested offsite backup

Date: 2026-08-30 UTC.

The user explicitly states that a backup exists on another server under their
control and instructs the project to open the data gate. The exact server path
and a remotely verified checksum are not available in this workspace.

This creates a narrow, auditable waiver:

```text
Phase G internal experiments / local RAW capture   OPEN
claim that a public Version DOI exists              FORBIDDEN
untrack/delete/rewrite historical data              FORBIDDEN
claim public reproducibility or archival custody    FORBIDDEN
```

`results/DATA_MANIFEST.json::doi` remains `null`. The waiver is stored under
`custody.phase_g_local_gate`, and `tools/check_phase_g_custody.py` accepts
either a real Version DOI or this exact restricted waiver. The manifest
builder preserves externally supplied custody metadata across rescans.

The waiver can be superseded later by a real public Version DOI. It is not a
DOI substitute outside the local execution gate.
