# Security Policy

LSAD is a security tool, and we hold it to the standard we'd expect of one. Thank you for helping keep the project and its users safe.

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 4.x     | ✅ Active development |
| < 4.0   | ❌ No longer supported |

## Reporting a Vulnerability

**Please do not open a public issue for security vulnerabilities.**

Instead, use one of these private channels:

1. **GitHub private vulnerability reporting** (preferred): go to the repository's **Security** tab → **Report a vulnerability**. This opens a private advisory visible only to maintainers.
2. **Email**: [tribhuwan.singh1108@gmail.com](mailto:tribhuwan.singh1108@gmail.com) with the subject line `[LSAD SECURITY]`.

Please include:

- A description of the vulnerability and its impact
- Steps to reproduce (proof-of-concept code or requests are welcome)
- The affected component (API, dashboard, endpoint agent, detection pipeline, etc.)
- Any suggested remediation, if you have one

## What to Expect

- **Acknowledgement** within 72 hours of your report
- **Assessment and triage** within 7 days
- **A fix or mitigation plan** communicated to you before public disclosure
- **Credit** in the release notes once the fix ships (unless you prefer to remain anonymous)

## Scope

In scope:

- Authentication/authorization bypass (JWT, RBAC, device API keys)
- Injection of any kind (log ingestion parsers are an explicit attack surface)
- IDOR or cross-user data exposure in the API or dashboard
- Secrets exposure in code, images, or build artifacts
- Vulnerabilities in the endpoint agents and their install path

Out of scope:

- Vulnerabilities requiring physical access to an already-compromised host
- Denial of service via volumetric traffic
- Findings in third-party dependencies with no demonstrated impact on LSAD (report those upstream, but feel free to notify us too)

## Hardening Guidance for Deployments

- Always set strong, unique values for the JWT secret in `.env` — never ship defaults
- Run the API behind TLS (`REQUIRE_TLS`) in any non-local deployment
- Scope device API keys per device and revoke unused ones
- Keep the database file readable only by the service user
