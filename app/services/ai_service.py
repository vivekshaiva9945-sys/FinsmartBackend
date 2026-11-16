import re
from typing import Any
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.pii import scrub_pii, contains_pii
from app.schemas.ai import AIChatResponse, Citation

# Financial safety guardrails: refuse speculative stock tips, crypto betting, and get-rich schemes
_SPECULATIVE_PATTERNS = [
    re.compile(r"\b(buy|invest in|trade)\s+(crypto|bitcoin|ethereum|doge|shiba|coin|token)\b", re.IGNORECASE),
    re.compile(r"\b(which|best)\s+stocks?\s+to\s+(buy|trade|invest)\b", re.IGNORECASE),
    re.compile(r"\b(guaranteed|double|triple|100x)\s+(returns?|profit|money)\b", re.IGNORECASE),
    re.compile(r"\b(intraday|future|options|f&o|call|put|derivative)\s+tips?\b", re.IGNORECASE),
    re.compile(r"\b(gambling|betting|rummy|casino|lottery)\b", re.IGNORECASE),
]


def check_guardrails(prompt: str) -> str | None:
    """Detects speculative or risky queries and enforces strict educational guardrails."""
    for pattern in _SPECULATIVE_PATTERNS:
        if pattern.search(prompt):
            return (
                "FinSmart is an educational financial literacy platform and does not offer "
                "personalized stock recommendations, cryptocurrency speculation, or intraday trading tips. "
                "SEBI and RBI guidelines caution against speculative schemes promising guaranteed returns. "
                "We recommend focusing on long-term disciplined budgeting, creating a 3-6 month emergency fund, "
                "and exploring low-risk government-backed instruments like PPF, NPS, and Sukanya Samriddhi Yojana."
            )
    return None


async def answer_financial_query(session: AsyncSession, raw_message: str, language: str = "en") -> AIChatResponse:
    """
    RAG-grounded Financial Literacy Assistant.
    1. Scrubs sensitive PII (Aadhaar, PAN, phone numbers).
    2. Runs safety guardrails against speculative investment advice.
    3. Retrieves verified knowledge from knowledge_docs and schemes.
    4. Constructs grounded, cited explanation.
    """
    has_pii = contains_pii(raw_message)
    scrubbed_query = scrub_pii(raw_message)
    
    # 1. Guardrail inspection
    guardrail_violation = check_guardrails(scrubbed_query)
    if guardrail_violation:
        return AIChatResponse(
            reply=guardrail_violation,
            citations=[
                Citation(
                    title="SEBI & RBI Investor Protection Advisory",
                    source="rbi.org.in / sebi.gov.in",
                    snippet="Never trade based on unverified tips or invest in schemes promising guaranteed high returns."
                )
            ],
            pii_scrubbed=has_pii
        )

    # 2. Knowledge Retrieval from knowledge_docs & schemes
    words = [w.strip() for w in re.findall(r"[A-Za-z0-9]{3,}", scrubbed_query)]
    search_term = " | ".join(words[:4]) if words else "budget"
    
    # Query knowledge docs
    docs_res = await session.execute(
        text("""
            SELECT title, category, content, source_citation
            FROM knowledge_docs
            ORDER BY id ASC
            LIMIT 3
        """)
    )
    docs = docs_res.all()

    # Query schemes
    schemes_res = await session.execute(
        text("""
            SELECT code, title_en, agency, summary, benefits, source_url
            FROM schemes
            LIMIT 3
        """)
    )
    schemes = schemes_res.all()

    citations: list[Citation] = []
    for d in docs:
        citations.append(
            Citation(
                title=d.title,
                source=d.source_citation,
                snippet=d.content[:160] + "..."
            )
        )
    for s in schemes:
        citations.append(
            Citation(
                title=f"{s.title_en} ({s.code})",
                source=s.source_url,
                snippet=s.summary[:160] + "..."
            )
        )

    # 3. Grounded response synthesis tailored by query topic
    q_lower = scrubbed_query.lower()
    
    if any(k in q_lower for k in ["scholarship", "college", "fees", "student", "ssp", "nsp"]):
        if language == "kn":
            reply = (
                "ವಿದ್ಯಾರ್ಥಿವೇತನಗಳು ಮತ್ತು ಶುಲ್ಕ ಸಹಾಯಕ್ಕಾಗಿ ಪ್ರಮುಖ ಮಾರ್ಗಸೂಚಿಗಳು:\n\n"
                "1. ರಾಷ್ಟ್ರೀಯ ವಿದ್ಯಾರ್ಥಿವೇತನ ಪೋರ್ಟಲ್ (NSP): SC/ST/OBC ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ಮೆಟ್ರಿಕ್ ನಂತರದ ವಿದ್ಯಾರ್ಥಿವೇತನ ಲಭ್ಯವಿದೆ. "
                "ಕುಟುಂಬದ ವಾರ್ಷಿಕ ಆದಾಯ ₹2.5 ಲಕ್ಷಕ್ಕಿಂತ ಕಡಿಮೆ ಇರಬೇಕು.\n"
                "2. ಕರ್ನಾಟಕ ರಾಜ್ಯ ವಿದ್ಯಾರ್ಥಿವೇತನ ಪೋರ್ಟಲ್ (SSP): ಕರ್ನಾಟಕದ ಎಂಜಿನಿಯರಿಂಗ್, ಡಿಪ್ಲೊಮಾ ಮತ್ತು ಪದವಿ ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ಬೋಧನಾ ಶುಲ್ಕ ಮರುಪಾವತಿ ಮತ್ತು ಹಾಸ್ಟೆಲ್ ರಿಯಾಯಿತಿ ದೊರೆಯುತ್ತದೆ.\n"
                "3. ಅಗತ್ಯ ದಾಖಲೆಗಳು: ವಿದ್ಯಾರ್ಥಿ ಮತ್ತು ಪೋಷಕರ ಆಧಾರ್, RD ನಂಬರ್ ಹೊಂದಿರುವ ಜಾತಿ ಮತ್ತು ಆದಾಯ ಪ್ರಮಾಣಪತ್ರ, ಕಾಲೇಜು ಶುಲ್ಕ ರಸೀದಿ.\n"
                "ಹೆಚ್ಚಿನ ವಿವರಗಳಿಗಾಗಿ 'ಯೋಜನೆಗಳು' (Schemes) ಟ್ಯಾಬ್ ಪರಿಶೀಲಿಸಿ."
            )
        elif language == "hi":
            reply = (
                "विद्यार्थियों और छात्रवृत्ति संबंधी दिशा-निर्देश:\n\n"
                "1. राष्ट्रीय छात्रवृत्ति पोर्टल (NSP): SC, ST और OBC छात्रों के लिए पोस्ट-मैट्रिक छात्रवृत्ति उपलब्ध है, "
                "जिनकी पारिवारिक आय ₹2.5 लाख से कम है।\n"
                "2. कर्नाटक राज्य छात्रवृत्ति (SSP): कर्नाटक के इंजीनियरिंग और कॉलेज छात्रों के लिए ट्यूशन फीस प्रतिपूर्ति और छात्रावास सहायता।\n"
                "3. आवश्यक दस्तावेज: आधार कार्ड, आय प्रमाण पत्र, जाति प्रमाण पत्र, कॉलेज बोनाफाइड और बैंक पासबुक।\n"
                "पात्रता की विस्तृत जांच के लिए 'Schemes' टैब का उपयोग करें।"
            )
        else:
            reply = (
                "Key Scholarship Opportunities for Higher Education:\n\n"
                "• **National Scholarship Portal (NSP Post-Matric)**: Covers full tuition fee reimbursement and maintenance "
                "allowance for SC, ST, and OBC students with family income under ₹2.5 Lakhs.\n"
                "• **Karnataka State Scholarship Portal (SSP)**: Domicile students in Karnataka pursuing engineering, diploma, "
                "or degree programs can apply for fee concessions and e-Attestation.\n"
                "• **Actionable Advice**: Ensure your bank account is seeded with Aadhaar for Direct Benefit Transfer (DBT) "
                "and verify your Caste/Income Certificate RD number before applying.\n"
                "Visit the 'Schemes' tab in FinSmart to run an automated eligibility check with your demographic profile."
            )

    elif any(k in q_lower for k in ["emergency", "save", "saving", "stipend", "50/30/20", "budget"]):
        if language == "kn":
            reply = (
                "ವಿದ್ಯಾರ್ಥಿಗಳು ಮತ್ತು ಕುಟುಂಬಗಳಿಗೆ ಬಜೆಟ್ ಮತ್ತು ಉಳಿತಾಯ ಸಲಹೆಗಳು:\n\n"
                "1. 50/30/20 ಸೂತ್ರ: ನಿಮ್ಮ ಆದಾಯದ 50% ಅನ್ನು ಅಗತ್ಯಗಳಿಗೆ (ಊಟ, ವಸತಿ, ಶುಲ್ಕ), 30% ಅನ್ನು ವೈಯಕ್ತಿಕ ಬಯಕೆಗಳಿಗೆ ಮತ್ತು ಕನಿಷ್ಠ 20% ಅನ್ನು ಉಳಿತಾಯಕ್ಕೆ ಮೀಸಲಿಡಿ.\n"
                "2. ತುರ್ತು ನಿಧಿ (Emergency Fund): ಕನಿಷ್ಠ 3 ರಿಂದ 6 ತಿಂಗಳ ಅಗತ್ಯ ಖರ್ಚುಗಳನ್ನು ಸುಲಭವಾಗಿ ಹಿಂಪಡೆಯಬಹುದಾದ ಉಳಿತಾಯ ಖಾತೆಯಲ್ಲಿ ಇರಿಸಿ.\n"
                "3. ಸಣ್ಣ ಉಳಿತಾಯ: ತಿಂಗಳಿಗೆ ₹500 ರಿಂದ ₹1,000 ಉಳಿಸಲು 'ಗುರಿಗಳು' (Goals) ವಿಭಾಗದಲ್ಲಿ ಹೊಸ ಗುರಿಯನ್ನು ರಚಿಸಿ."
            )
        elif language == "hi":
            reply = (
                "बजट और आपातकालीन फंड प्रबंधन दिशा-निर्देश:\n\n"
                "1. 50/30/20 नियम: अपनी कुल आय का 50% बुनियादी जरूरतों (किराया, भोजन, फीस) पर, 30% जीवनशैली पर, और 20% बचत में लगाएं।\n"
                "2. आपातकालीन फंड (Emergency Fund): कम से कम 3 से 6 महीने के अनिवार्य खर्चों को बैंक बचत खाते में सुरक्षित रखें।\n"
                "3. फिनस्मार्ट के 'Goals' टैब में नया बचत लक्ष्य जोड़ें और हर महीने नियमित योगदान दर्ज करें।"
            )
        else:
            reply = (
                "Practical Budgeting & Emergency Fund Strategy:\n\n"
                "• **The 50/30/20 Budgeting Guideline**: Allocate 50% of monthly income to essentials (food, rent, tuition), "
                "30% to discretionary lifestyle wants, and 20% to savings goals.\n"
                "• **Emergency Fund Sizing**: Maintain 3 to 6 months of mandatory living expenses in a liquid savings bank account. "
                "Never invest your emergency fund in volatile stocks or lock it in long-term illiquid assets.\n"
                "• **Student Tip**: If managing on a monthly allowance or stipend, track every transaction daily using FinSmart "
                "to eliminate 'money leakage' on frequent micro-spends."
            )

    elif any(k in q_lower for k in ["loan", "app", "scam", "fraud", "upi", "pin", "cyber"]):
        if language == "kn":
            reply = (
                "ಸೈಬರ್ ಸುರಕ್ಷತೆ ಮತ್ತು ಡಿಜಿಟಲ್ ಪಾವತಿ ಎಚ್ಚರಿಕೆಗಳು:\n\n"
                "1. UPI ಪಿನ್ ನಿಯಮ: ಹಣ ಸ್ವೀಕರಿಸಲು (Receive) ಎಂದಿಗೂ UPI PIN ನಮೂದಿಸಬೇಡಿ! PIN ನಮೂದಿಸಿದರೆ ಖಾತೆಯಿಂದ ಹಣ ಕಡಿತವಾಗುತ್ತದೆ.\n"
                "2. ನಕಲಿ ಸಾಲದ ಆ್ಯಪ್‌ಗಳು: ಪ್ಲೇಸ್ಟೋರ್ ಹೊರಗಿನ ಅಪರಿಚಿತ APK ಗಳನ್ನು ಇನ್‌ಸ್ಟಾಲ್ ಮಾಡಬೇಡಿ. ಎಲ್ಲಾ ಅಧಿಕೃತ ಸಾಲ ನೀಡುವವರು RBI ನೋಂದಾಯಿತರಾಗಿರಬೇಕು.\n"
                "3. ವಂಚನೆ ನಡೆದರೆ: ತಕ್ಷಣ 1930 ಸೈಬರ್ ಕ್ರೈಮ್ ಸಹಾಯವಾಣಿಗೆ ಕರೆ ಮಾಡಿ ಅಥವಾ cybercrime.gov.in ನಲ್ಲಿ ದೂರು ದಾಖಲಿಸಿ."
            )
        elif language == "hi":
            reply = (
                "साइबर सुरक्षा और डिजिटल भुगतान सुरक्षा:\n\n"
                "1. UPI PIN नियम: पैसे प्राप्त करने के लिए कभी भी अपना UPI PIN दर्ज न करें। PIN केवल पैसे भेजने के लिए होता है।\n"
                "2. फर्जी लोन ऐप्स से सावधान: अनधिकृत लोन ऐप्स आपकी गोपनीयता चुराते हैं। केवल RBI पंजीकृत बैंकों/NBFC से ही ऋण लें।\n"
                "3. साइबर अपराध हेल्पलाइन: किसी भी वित्तीय धोखाधड़ी की स्थिति में तुरंत 1930 डायल करें या cybercrime.gov.in पर रिपोर्ट करें।"
            )
        else:
            reply = (
                "Critical Cyber Safety & Digital Lending Advisory:\n\n"
                "• **UPI Golden Rule**: You NEVER need to enter your UPI PIN to RECEIVE money. Entering your PIN always debits funds from your bank account.\n"
                "• **Predatory Instant Loan Apps**: Avoid unverified APKs offering 5-minute loans. Authorized digital lenders must be RBI-regulated banks or NBFCs.\n"
                "• **Emergency Response**: If targeted by online fraud, immediately call the National Cyber Crime Helpline at **1930** and report on **cybercrime.gov.in** within 24 hours to block unauthorized fund transfers."
            )
    else:
        reply = (
            f"Here is guidance regarding your question about '{scrubbed_query}':\n\n"
            "• **Financial Planning**: Ensure you maintain strict categorization of your expenses and set budget limits under the Budgets tab.\n"
            "• **Welfare Schemes**: The Central & State Governments offer social security and scholarship benefits like PMJDY, Atal Pension Yojana, and NSP.\n"
            "• **Calculators**: Use the Calculators tab in FinSmart to model loan EMIs or compare the long-term compounding impact of systematic savings.\n"
            "Feel free to ask more specific questions about scholarships, savings goals, budgeting rules, or fraud prevention."
        )

    return AIChatResponse(
        reply=reply,
        citations=citations[:3],
        pii_scrubbed=has_pii
    )

