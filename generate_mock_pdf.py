from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

def create_mock_contract(filename):
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    def draw_page(page_num, lines):
        text = c.beginText(50, height - 50)
        text.setFont("Helvetica", 11)
        for line in lines:
            text.textLine(line)
        c.drawText(text)
        c.drawCentredString(width / 2.0, 30, f"- Page {page_num} -")
        c.showPage()
    
    # Page 1
    page1_lines = [
        "COMMERCIAL LEASE AND MASTER SERVICE AGREEMENT",
        "",
        "This Commercial Lease and Master Service Agreement (the 'Agreement') is made and entered into",
        "on this 5th day of May, 2026, by and between Nexus Properties LLC, a limited liability company",
        "organized under the laws of Delaware ('Landlord' or 'Lessor'), and TechSolutions Inc, a",
        "corporation organized under the laws of California ('Tenant' or 'Lessee').",
        "",
        "WHEREAS, Landlord is the legal owner of certain real property located at 123 Innovation Drive,",
        "Silicon Valley, CA (the 'Premises'); and",
        "",
        "WHEREAS, Tenant desires to lease the Premises for the purpose of operating a software",
        "development and data processing facility, and Landlord is willing to lease the Premises",
        "subject to the terms, covenants, and conditions herein set forth.",
        "",
        "1. DEMISE AND PREMISES:",
        "Landlord hereby demises and leases to Tenant, and Tenant hereby takes and leases from",
        "Landlord, the Premises, consisting of approximately 25,000 square feet of office and",
        "laboratory space. The Premises shall be delivered in 'AS-IS' condition, without any",
        "representations or warranties regarding fitness for a particular purpose.",
        "",
        "2. TERM AND COMMENCEMENT:",
        "The initial term of this Lease shall be for a period of ten (10) years (the 'Initial Term'),",
        "commencing on June 1, 2026 (the 'Commencement Date') and expiring on May 31, 2036. Tenant",
        "shall have the option to renew this Lease for two (2) consecutive periods of five (5) years",
        "each, provided Tenant is not in default of any material provision of this Agreement.",
        "",
        "3. RENT, CAM CHARGES, AND FINANCIAL OBLIGATIONS:",
        "Tenant agrees to pay Landlord a Base Monthly Rent of $75,000. Rent is due in advance on the",
        "first day of each calendar month. In addition to the Base Rent, this is a Triple Net (NNN)",
        "lease. Tenant shall be responsible for paying its pro-rata share of Common Area Maintenance",
        "(CAM) charges, property taxes, and building insurance. CAM charges are currently estimated at",
        "$12,500 per month.",
        "",
        "A late penalty fee of five percent (5%) of the outstanding balance will be applied if rent is",
        "not received by the 5th day of the month. Tenant shall also deposit with Landlord the sum of",
        "$250,000 as a Security Deposit upon execution of this Agreement."
    ]
    draw_page(1, page1_lines)
    
    # Page 2
    page2_lines = [
        "4. MAINTENANCE, REPAIRS, AND ALTERATIONS:",
        "Tenant, at its sole cost and expense, shall keep and maintain the interior of the Premises in",
        "good order and repair, including all plumbing, HVAC systems, electrical systems, and fixtures.",
        "Landlord shall only be responsible for structural elements of the building, specifically the",
        "roof and exterior walls. Any alterations, additions, or improvements to the Premises require",
        "the prior written consent of the Landlord.",
        "",
        "5. INDEMNIFICATION AND HOLD HARMLESS:",
        "To the fullest extent permitted by law, Tenant agrees to indemnify, defend, and hold harmless",
        "the Landlord, its officers, agents, and employees from and against any and all claims,",
        "damages, losses, liabilities, and expenses, including reasonable attorneys' fees, arising out",
        "of or resulting from Tenant's use or occupancy of the Premises, or the conduct of Tenant's",
        "business, or from any activity, work, or thing done, permitted, or suffered by Tenant in or",
        "about the Premises.",
        "",
        "6. SUBROGATION AND WAIVER:",
        "Landlord and Tenant each hereby waive any and all rights of recovery against the other, or",
        "against the officers, employees, agents, and representatives of the other, for loss of or",
        "damage to such waiving party or its property or the property of others under its control to",
        "the extent that such loss or damage is insured against under any insurance policy in force",
        "at the time of such loss or damage. The waiving party shall, upon obtaining policies of",
        "insurance required hereunder, give notice to the insurance carrier that the foregoing mutual",
        "waiver of subrogation is contained in this Lease.",
        "",
        "7. INSURANCE REQUIREMENTS:",
        "Tenant shall procure and maintain throughout the Term, at its sole cost, Commercial General",
        "Liability insurance with a combined single limit of not less than $5,000,000 per occurrence",
        "for bodily injury and property damage. Landlord must be named as an additional insured.",
        "Failure to maintain this insurance constitutes a material breach of this Agreement, subjecting",
        "Tenant to immediate eviction and liability for all resultant damages."
    ]
    draw_page(2, page2_lines)

    # Page 3
    page3_lines = [
        "8. FORCE MAJEURE:",
        "Neither party shall be liable for any failure or delay in the performance of its obligations",
        "under this Agreement (other than the obligation to pay Rent) if such failure or delay is due",
        "to causes beyond its reasonable control, including but not limited to acts of God, war,",
        "terrorism, riots, embargoes, acts of civil or military authorities, fire, floods, accidents,",
        "strikes, or shortages of transportation facilities, fuel, energy, labor or materials",
        "(collectively, 'Force Majeure'). However, the Tenant's obligation to pay rent shall NOT be",
        "abated due to a Force Majeure event unless the Premises are completely destroyed.",
        "",
        "9. DEFAULT AND REMEDIES:",
        "The occurrence of any of the following shall constitute a material default and breach of this",
        "Lease by Tenant: (a) Any failure by Tenant to pay the Rent or any other monetary sums required",
        "to be paid hereunder; (b) The abandonment or vacation of the Premises by Tenant; (c) A failure",
        "by Tenant to observe and perform any other provision of this Lease to be observed or performed",
        "by Tenant, where such failure continues for thirty (30) days after written notice.",
        "",
        "Upon default, Landlord shall have the right to terminate this Lease, re-enter the Premises,",
        "and remove all persons and property. Tenant shall be liable for all past due rent, the",
        "unamortized portion of any tenant improvement allowances, and an accelerated penalty payment",
        "equal to six (6) months of Base Rent.",
        "",
        "10. SEVERABILITY:",
        "If any term, covenant, condition, or provision of this Agreement is held by a court of",
        "competent jurisdiction to be invalid, void, or unenforceable, the remainder of the provisions",
        "shall remain in full force and effect and shall in no way be affected, impaired, or",
        "invalidated. The parties agree to negotiate in good faith to replace the invalid provision",
        "with a valid provision that most closely approximates the economic effect and intent of the",
        "invalid provision."
    ]
    draw_page(3, page3_lines)

    # Page 4
    page4_lines = [
        "11. ASSIGNMENT AND SUBLETTING:",
        "Tenant shall not voluntarily or by operation of law assign, transfer, mortgage, or encumber",
        "this Lease, or sublet the whole or any part of the Premises, without the prior written consent",
        "of Landlord, which consent shall not be unreasonably withheld. Any attempted assignment or",
        "subletting without such consent shall be void and shall constitute a material default.",
        "",
        "12. HAZARDOUS MATERIALS:",
        "Tenant shall not cause or permit any Hazardous Material to be brought upon, kept, or used in",
        "or about the Premises by Tenant, its agents, employees, contractors, or invitees. 'Hazardous",
        "Material' means any substance regulated by any local governmental authority, the State, or",
        "the Federal Government. Tenant assumes massive financial liability for any environmental",
        "cleanup costs associated with their breach of this clause.",
        "",
        "13. QUIET ENJOYMENT:",
        "Landlord covenants and agrees with Tenant that upon Tenant paying the Rent and observing and",
        "performing all the terms, covenants, and conditions on Tenant's part to be observed and",
        "performed, Tenant may peaceably and quietly enjoy the Premises during the Term.",
        "",
        "14. ESTOPPEL CERTIFICATES:",
        "Tenant shall at any time upon not less than ten (10) days' prior written notice from Landlord",
        "execute, acknowledge, and deliver to Landlord a statement in writing certifying that this",
        "Lease is unmodified and in full force and effect (or, if modified, stating the nature of",
        "such modification) and the date to which the Rent and other charges are paid in advance.",
        "",
        "15. TIME OF ESSENCE:",
        "Time is of the essence with respect to the performance of all obligations to be performed or",
        "observed by the Parties under this Lease."
    ]
    draw_page(4, page4_lines)

    # Page 5
    page5_lines = [
        "16. GOVERNING LAW AND VENUE:",
        "This Agreement shall be governed by, construed, and enforced in accordance with the laws of",
        "the State of California, without regard to its conflict of laws principles. Any legal action",
        "or proceeding arising out of or related to this Agreement shall be brought exclusively in the",
        "state or federal courts located in Santa Clara County, California.",
        "",
        "17. ENTIRE AGREEMENT:",
        "This Agreement, including all Exhibits attached hereto, constitutes the entire agreement",
        "between the parties pertaining to the subject matter hereof and supersedes all prior and",
        "contemporaneous agreements, understandings, negotiations, and discussions, whether oral or",
        "written, of the parties. There are no warranties, representations, or other agreements",
        "between the parties in connection with the subject matter hereof except as specifically set",
        "forth herein.",
        "",
        "18. WAIVER OF JURY TRIAL:",
        "LANDLORD AND TENANT EACH HEREBY WAIVE THEIR RESPECTIVE RIGHTS TO A TRIAL BY JURY IN ANY",
        "ACTION, PROCEEDING, OR COUNTERCLAIM BROUGHT BY EITHER OF THE PARTIES HERETO AGAINST THE",
        "OTHER ON ANY MATTERS WHATSOEVER ARISING OUT OF OR IN ANY WAY CONNECTED WITH THIS LEASE,",
        "THE RELATIONSHIP OF LANDLORD AND TENANT, OR TENANT'S USE OR OCCUPANCY OF THE PREMISES.",
        "",
        "IN WITNESS WHEREOF, Landlord and Tenant have executed this Lease as of the day and year",
        "first above written.",
        "",
        "LANDLORD: Nexus Properties LLC",
        "By: ___________________________",
        "Name: John Sterling",
        "Title: Managing Director",
        "",
        "TENANT: TechSolutions Inc",
        "By: ___________________________",
        "Name: Sarah Jenkins",
        "Title: Chief Executive Officer"
    ]
    draw_page(5, page5_lines)

    c.save()
    print(f"Successfully generated {filename}")

if __name__ == "__main__":
    create_mock_contract("mock_contract.pdf")
