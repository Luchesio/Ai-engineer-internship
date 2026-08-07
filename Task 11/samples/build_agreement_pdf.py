from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer

OUTPUT = Path(__file__).parent / "vendor_agreement.pdf"

styles = getSampleStyleSheet()
TITLE = ParagraphStyle("title", parent=styles["Title"], fontSize=15, spaceAfter=6)
HEAD = ParagraphStyle("head", parent=styles["Heading2"], fontSize=11, spaceBefore=10, spaceAfter=4)
BODY = ParagraphStyle("body", parent=styles["BodyText"], fontSize=9.5, leading=13.5, spaceAfter=5)

CONTENT = [
    ("title", "MASTER SERVICES AGREEMENT"),
    ("body", "Between Northwind Systems Ltd (company number 09214477, registered at 18 Bevis Marks, "
             "London EC3A 7BA) (the \"Supplier\") and Kestrel Financial Group plc (the \"Client\"). "
             "Effective Date: 1 April 2026. Agreement reference NW-KFG-2026-014."),
    ("head", "1. Scope of Services"),
    ("body", "1.1 The Supplier shall provide the Northwind Ledger Platform, a hosted reconciliation "
             "service, together with the implementation, configuration, and support services described "
             "in Schedule A."),
    ("body", "1.2 The Platform shall be made available to a maximum of 400 named users. Additional "
             "users may be added at a rate of 22 per user per month, invoiced in arrears."),
    ("body", "1.3 Implementation shall be completed no later than 30 June 2026. The Client shall "
             "nominate a project sponsor within 10 business days of the Effective Date."),
    ("head", "2. Charges and Payment"),
    ("body", "2.1 The Client shall pay a platform fee of 7,500 GBP per month and a support fee of "
             "1,250 GBP per month, giving a combined monthly charge of 8,750 GBP exclusive of VAT."),
    ("body", "2.2 A one-off implementation charge of 24,000 GBP is payable in two equal instalments: "
             "the first on the Effective Date and the second on acceptance of the Platform."),
    ("body", "2.3 Invoices are issued monthly in advance and payable within 30 days of receipt. "
             "Overdue sums carry interest at 4% above the Bank of England base rate."),
    ("body", "2.4 Charges are fixed for the Initial Term. On each renewal the Supplier may increase "
             "charges by the annual change in the Consumer Prices Index plus 3 percentage points."),
    ("pagebreak", None),
    ("head", "3. Term"),
    ("body", "3.1 This Agreement commences on the Effective Date and continues for an Initial Term of "
             "24 months."),
    ("body", "3.2 On expiry of the Initial Term this Agreement shall renew automatically for successive "
             "periods of 12 months unless either party gives written notice of non-renewal in accordance "
             "with clause 4.2."),
    ("head", "4. Termination"),
    ("body", "4.1 Either party may terminate this Agreement immediately on written notice if the other "
             "party commits a material breach that is not remedied within 20 business days of notice."),
    ("body", "4.2 Either party may terminate this Agreement for convenience, or give notice of "
             "non-renewal, by providing not less than 90 days written notice to the other party."),
    ("body", "4.3 Termination for convenience during the Initial Term triggers an early exit charge "
             "equal to 50% of the charges that would have fallen due for the remainder of that term."),
    ("head", "5. Service Levels"),
    ("body", "5.1 The Supplier warrants Platform availability of 99.5% measured monthly, excluding "
             "scheduled maintenance notified at least 5 business days in advance."),
    ("body", "5.2 Where monthly availability falls below the warranted level, the Client is entitled to "
             "a service credit of 5% of that month's platform fee for each 0.5 percentage point shortfall, "
             "capped at 25% of the monthly platform fee."),
    ("body", "5.3 Service credits are the Client's sole remedy for availability failures and must be "
             "claimed within 30 days of the end of the affected month."),
    ("body", "5.4 Priority 1 incidents shall receive a response within 1 hour and a resolution target of "
             "8 hours. Priority 2 incidents shall receive a response within 4 business hours."),
    ("pagebreak", None),
    ("head", "6. Data Protection"),
    ("body", "6.1 The Client is the controller and the Supplier the processor in respect of all Client "
             "personal data. The Data Processing Addendum at Schedule C forms part of this Agreement."),
    ("body", "6.2 Client data shall be hosted in the United Kingdom and the Republic of Ireland only. "
             "The Supplier shall not appoint a subprocessor outside those territories without the "
             "Client's prior written consent."),
    ("body", "6.3 On termination the Supplier shall return Client data in a machine-readable format "
             "within 15 days of request and shall delete all remaining copies, including backups, within "
             "30 days thereafter, certifying deletion in writing."),
    ("body", "6.4 The Supplier shall notify the Client of any personal data breach without undue delay "
             "and in any event within 24 hours of becoming aware of it."),
    ("head", "7. Security"),
    ("body", "7.1 The Supplier shall maintain ISO 27001 certification for the duration of this Agreement "
             "and shall provide the current certificate on request."),
    ("body", "7.2 The Supplier shall commission an independent penetration test of the Platform at least "
             "once every 12 months and shall share the executive summary with the Client."),
    ("body", "7.3 The Supplier shall support SAML 2.0 single sign-on and enforce multi-factor "
             "authentication for all administrative access to Client environments."),
    ("head", "8. Liability"),
    ("body", "8.1 Neither party excludes liability for death or personal injury caused by negligence, "
             "fraud, or any other liability that cannot lawfully be excluded."),
    ("body", "8.2 Subject to clause 8.1, each party's total aggregate liability under this Agreement is "
             "limited to the total charges paid in the 12 months preceding the claim, being 105,000 GBP "
             "at the date of this Agreement."),
    ("body", "8.3 Neither party is liable for loss of profit, loss of anticipated savings, or indirect or "
             "consequential loss."),
    ("pagebreak", None),
    ("head", "9. Client Obligations"),
    ("body", "9.1 The Client shall provide test data, environment access, and named business contacts "
             "sufficient for the Supplier to meet the implementation date in clause 1.3."),
    ("body", "9.2 The Client shall complete user acceptance testing within 15 business days of the "
             "Platform being made available for testing. The Platform is deemed accepted if the Client "
             "raises no material defect within that period."),
    ("head", "10. Audit"),
    ("body", "10.1 The Client may audit the Supplier's compliance with clauses 6 and 7 once in any "
             "12 month period, on 30 days written notice, at the Client's cost."),
    ("head", "11. General"),
    ("body", "11.1 Neither party may assign this Agreement without the other's written consent, such "
             "consent not to be unreasonably withheld."),
    ("body", "11.2 This Agreement is governed by the laws of England and Wales and the parties submit "
             "to the exclusive jurisdiction of the English courts."),
    ("body", "11.3 Either party may terminate this Agreement at any time by giving 30 days written "
             "notice to the other party."),
    ("body", "11.4 This Agreement, together with its Schedules, constitutes the entire agreement between "
             "the parties and supersedes all prior discussions."),
    ("body", "Signed for Northwind Systems Ltd: T. Okafor, Commercial Director, 24 March 2026."),
    ("body", "Signed for Kestrel Financial Group plc: M. Halvorsen, Chief Operating Officer, "
             "26 March 2026."),
]


def build() -> Path:
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=22 * mm,
        rightMargin=22 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title="Master Services Agreement NW-KFG-2026-014",
    )
    story = []
    for kind, text in CONTENT:
        if kind == "pagebreak":
            story.append(PageBreak())
        elif kind == "title":
            story.append(Paragraph(text, TITLE))
            story.append(Spacer(1, 4))
        elif kind == "head":
            story.append(Paragraph(text, HEAD))
        else:
            story.append(Paragraph(text, BODY))
    doc.build(story)
    return OUTPUT


if __name__ == "__main__":
    print(f"Wrote {build()}")