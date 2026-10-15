# Security policy / 安全说明

## Threat model

Unofficial customization for a trusted single-user Windows machine, not a security boundary against local malware, other users or processes.

- CDP can execute JavaScript in the application. Loopback remains accessible to other local software. Never forward or expose it; do not use on an untrusted/shared machine.
- `manage.ps1` verifies loopback binding and Store Codex process ownership. Direct developer tools validate URLs but do not replace owner verification: run Status/Doctor first.
- The bridge allows only local renderer WebSockets on the selected port, rejects credentials/queries/remote endpoints, and disables HTTP redirects. Recognized app URLs are not cryptographic identity checks.
- Trust the project directory and executable overrides: local Python is executed and local `header.js` injected. Shared/untrusted writable locations are unsafe.
- No sandbox disabling, app-package patches, global execution-policy changes or forced Codex restarts.

## Data handling

- Headless reader sends only initialize/initialized and `account/rateLimits/read`: no prompts, subscription changes, credit purchases, credential/session-file reads.
- Installed app-server manages its own authentication and service calls. This is not offline software; upstream behavior is outside the project's control.
- Bridge receives remaining percentages, reset/loading/error/refresh state. No remote telemetry or persistent quota history.
- Mounting inspects chrome geometry/visibility and native control text for collision avoidance, not conversation messages. Keep diagnostics free of chat inspection.
- Local logs may contain paths/errors. `runtime/` is excluded from Git and release ZIPs. Optional screenshots can include header/account information; review before sharing.
- Legacy float remains unchanged for rollback, including its older reader. Prefer embedded mode; audit legacy changes separately.

## Reporting

Never include credentials, cookies, account/chat data or live debugging access in public issues. Use GitHub private vulnerability reporting if enabled; otherwise request a private channel without public exploit details. No response SLA is guaranteed. Initially only the latest source version is maintained.

## Removal

Stop removes only the component and its verified helper. Uninstall also archives own startup/desktop links and retains source/local data. Neither closes the app CDP port: manually fully quit Codex and reopen normally. If compromise is suspected, stop using the tool and follow provider/account incident procedures.
