# Security Policy

## Supported versions

| Version | Supported |
| ------- | --------- |
| 0.2.x   | yes       |
| < 0.2   | no        |

`0.2.0` fixes a set of availability, data-integrity and injection issues listed in
[CHANGELOG.md](CHANGELOG.md); earlier versions should not be used.

## Reporting a vulnerability

Please **do not** open a public issue for a security problem.

1. Use GitHub's private vulnerability reporting:
   <https://github.com/BernieHuang2008/MercurySQL/security/advisories/new>
   (or *Security* → *Report a vulnerability* on this repository).
2. Include: the version, a minimal reproduction, the impact you see, and any
   suggested fix.

You can expect an acknowledgement within 7 days. Please give us a reasonable
window to publish a fix before disclosing the issue publicly.

## What is in scope

- SQL injection that reaches the database **without** the caller opting into raw
  SQL (`selection=..., raw=True` is documented as "trusted input only").
- Data corruption / silent data loss caused by a public API call.
- Bypasses of the identifier quoting (`quote_ident`) or of the SQL type
  validation (`check_type_sql`).
- Denial of service reachable from the library itself (e.g. a call that can
  block its caller forever).

## What is out of scope

- Problems that require a malicious local attacker (e.g. editing the database
  file directly).
- Vulnerabilities in the database server or in `mysql-connector-python`; report
  those upstream.
- Passing untrusted strings as table/column names while also relying on them as
  an authorization boundary. Quoting prevents injection, not access control;
  keep your own allow-list.
- Hangs caused by a database server that never answers the initial connection
  (the driver call itself blocks; use the driver's own connection timeout).
