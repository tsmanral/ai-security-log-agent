# Windows Endpoint Agent — Design Document (Future Work)

> **Status**: Design reference only.  No code is implemented in V2.

## Overview
A Windows agent that mirrors the Linux agent's functionality for Windows
Security Event Logs.

## Architecture
1. **Installer** — MSI or EXE built with WiX / Inno Setup.
   - Presents a field for the registration token.
   - Calls `POST /api/devices/register` during install.
   - Drops the agent binary + config into `C:\Program Files\AI-Sentinel\`.
   - Registers a Windows Service via `sc.exe` or `nssm`.

2. **Event Collection** — Uses the Windows Event Log API (`wevtutil` or
   `win32evtlog` from pywin32):
   - Subscribes to the Security channel.
   - Filters for Event IDs `4624` (logon success), `4625` (logon failure),
     `4672` (special privilege logon), `4648` (explicit credential use).

3. **Parsing** — Uses `WindowsLogonParser` from
   `ai_sentinel.ingestion.parsers_windows` to convert XML events into
   `NormalizedEvent` dicts.

4. **Transport** — Same HTTPS batch endpoint as the Linux agent:
   - Headers: `X-Device-Id`, `X-Api-Key`.
   - Payload: `EventBatch` JSON.

5. **Service Lifecycle**:
   - Runs as `LocalService` (least privilege).
   - Auto-starts on boot.
   - Logs to Windows Event Log (Application channel).

## Security Considerations
- The API key stored in the config file should have restricted ACLs
  (readable only by `SYSTEM` and `Administrators`).
- The installer should validate the TLS certificate of the server.

## Dependencies
- Python 3.11+ or compiled with PyInstaller.
- `pywin32` for native Event Log access.
- `httpx` for HTTPS transport.
