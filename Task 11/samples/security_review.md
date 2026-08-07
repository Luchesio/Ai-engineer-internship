# Third-Party Security Review — Northwind Systems Ltd

**Reviewer:** P. Lindqvist, Head of Risk
**Reference:** TPR-2026-041
**Issued:** 14 April 2026
**Status:** Draft for Technology Committee
**Overall rating:** Amber — proceed with conditions

## Scope

This review covers the Northwind Ledger Platform against the Group's Third-Party Security
Standard v4.2. It is based on Northwind's completed questionnaire, their ISO 27001 certificate,
a two-hour architecture walkthrough held on 8 April 2026, and a documentation request that was
partially fulfilled. It does not include independent technical testing.

## Summary of Findings

Seven findings were raised: two high, three medium, two low. None are considered blocking on
their own, but findings TPR-01 and TPR-02 must be closed before production data is loaded.

## High Findings

### TPR-01 — Subprocessor outside the contracted territory

Northwind uses a log analytics provider hosted in the Frankfurt region. Northwind's position is
that log data contains no personal data. We have not been able to confirm this: sample log lines
supplied on 9 April 2026 included account identifiers and full request URLs.

The Master Services Agreement states that Client data shall be hosted in the United Kingdom and
the Republic of Ireland only. On the evidence seen, the current architecture does not meet that
clause.

**Required:** written confirmation of the log contents, and either removal of the Frankfurt
dependency or a formal consent request under clause 6.2. Owner: Northwind. Due 8 May 2026.

### TPR-02 — Penetration test out of date

The most recent independent penetration test supplied is dated 11 September 2024, which is
19 months old. The contract requires a test at least once every 12 months. Northwind has
confirmed a test is booked but could not give a date.

**Required:** a completed test with the executive summary shared, before any Client data is
loaded. Owner: Northwind. Due 29 May 2026.

## Medium Findings

### TPR-03 — SSO not enabled by default

SAML 2.0 is supported but is not enabled on the tenant provisioned for us. Until it is,
platform access will rely on local passwords, outside the Group identity estate.

**Required:** enable SAML 2.0 during implementation. Owner: S. Bello. Due 30 June 2026.

### TPR-04 — Deletion certification process undefined

The contract requires certified deletion of all copies, including backups, within 30 days of
return. Northwind's backup retention is 90 days and their runbook has no step for early backup
expiry. There is a gap between the contractual commitment and the operational reality.

**Required:** a documented deletion procedure that meets the contractual window, or an agreed
variation. Owner: Northwind, with J. Moreau. Due 12 June 2026.

### TPR-05 — Breach notification window

Northwind's standard incident policy commits to notifying customers within 72 hours. The
contract requires notification within 24 hours. Northwind's security lead was not aware of the
shorter contractual window during the walkthrough.

**Required:** update the customer notification runbook to reflect the contracted 24 hours.
Owner: Northwind. Due 12 June 2026.

## Low Findings

### TPR-06 — Admin MFA enforced but not evidenced

Northwind states that multi-factor authentication is enforced for administrative access. No
configuration evidence or attestation was provided. Requested again on 10 April 2026.

### TPR-07 — Starter and leaver process

Northwind's access review runs quarterly. The Group standard is monthly for systems holding
customer records. This is a deviation, not a breach, and is accepted for the initial term.

## Open Questions

- Does the Frankfurt log pipeline hold personal data? Northwind and the Group disagree on this,
  and the sample evidence supports the Group's reading.
- Who bears the cost if the penetration test finds issues requiring remediation before go-live?
  This is not addressed in the contract.
- Should the 30-day exit route be relied on operationally, given the Committee minuted it as the
  reason no break-cost analysis was needed?

## Recommendation

Proceed with implementation, but do not load Client data until TPR-01 and TPR-02 are closed.
Given the 30 June 2026 go-live and a due date of 29 May 2026 for the penetration test, the
schedule has under five weeks of contingency. Recommend the Committee treat 29 May 2026 as a
formal gate rather than a target.
