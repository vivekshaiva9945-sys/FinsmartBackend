from decimal import Decimal, ROUND_HALF_UP
from typing import Any

# Standard minor unit precision for INR (1 Rupee = 100 Paise)
PAISE_UNIT = Decimal("0.01")


def to_paise(rupees: Decimal | float | str | int) -> int:
    """Convert rupee value to exact integer paise minor units."""
    if isinstance(rupees, float):
        rupees = str(rupees)
    d = Decimal(str(rupees))
    return int((d * 100).quantize(Decimal(1), rounding=ROUND_HALF_UP))


def to_rupees(paise: int) -> Decimal:
    """Convert integer paise back to Decimal rupees."""
    return (Decimal(paise) / Decimal(100)).quantize(PAISE_UNIT, rounding=ROUND_HALF_UP)


def format_inr(paise: int) -> str:
    """Format paise into Indian Rupee representation (e.g. ₹1,50,000.00)."""
    rupees = to_rupees(paise)
    parts = f"{rupees:.2f}".split(".")
    integer_part = parts[0]
    decimal_part = parts[1]
    
    # Format according to Indian numbering system (lakhs, crores)
    if len(integer_part) > 3:
        last_three = integer_part[-3:]
        remaining = integer_part[:-3]
        groups = []
        while len(remaining) > 2:
            groups.append(remaining[-2:])
            remaining = remaining[:-2]
        if remaining:
            groups.append(remaining)
        groups.reverse()
        formatted_int = ",".join(groups) + "," + last_three
    else:
        formatted_int = integer_part
        
    return f"₹{formatted_int}.{decimal_part}"


def calculate_emi(principal: Decimal, annual_interest_pct: Decimal, tenure_months: int) -> dict[str, Any]:
    """
    Calculate Equated Monthly Installment (EMI) using standard formula:
    EMI = P * r * (1 + r)^n / ((1 + r)^n - 1)
    """
    if principal <= 0 or tenure_months <= 0:
        raise ValueError("Principal and tenure must be strictly positive.")
    if annual_interest_pct < 0 or annual_interest_pct > 100:
        raise ValueError("Interest rate must be between 0% and 100%.")

    monthly_rate = annual_interest_pct / Decimal(12) / Decimal(100)
    
    if monthly_rate == 0:
        emi = (principal / Decimal(tenure_months)).quantize(PAISE_UNIT, rounding=ROUND_HALF_UP)
    else:
        factor = (Decimal(1) + monthly_rate) ** tenure_months
        emi = (principal * monthly_rate * factor / (factor - Decimal(1))).quantize(PAISE_UNIT, rounding=ROUND_HALF_UP)
        
    total_payable = (emi * Decimal(tenure_months)).quantize(PAISE_UNIT, rounding=ROUND_HALF_UP)
    total_interest = (total_payable - principal).quantize(PAISE_UNIT, rounding=ROUND_HALF_UP)
    
    return {
        "monthly_emi": str(emi),
        "principal": str(principal.quantize(PAISE_UNIT)),
        "total_interest": str(total_interest),
        "total_payable": str(total_payable),
        "tenure_months": tenure_months,
        "annual_interest_pct": str(annual_interest_pct),
        "interest_ratio_pct": str(((total_interest / total_payable) * Decimal(100)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
    }


def calculate_sip(monthly_investment: Decimal, annual_expected_return_pct: Decimal, tenure_months: int) -> dict[str, Any]:
    """
    Calculate Systematic Investment Plan (SIP) wealth creation:
    FV = P * [((1 + i)^n - 1) / i] * (1 + i)
    """
    if monthly_investment <= 0 or tenure_months <= 0:
        raise ValueError("Monthly investment and tenure must be strictly positive.")
    if annual_expected_return_pct < 0 or annual_expected_return_pct > 60:
        raise ValueError("Expected return rate must be between 0% and 60%.")

    monthly_rate = annual_expected_return_pct / Decimal(12) / Decimal(100)
    total_invested = (monthly_investment * Decimal(tenure_months)).quantize(PAISE_UNIT, rounding=ROUND_HALF_UP)
    
    if monthly_rate == 0:
        future_value = total_invested
    else:
        factor = (Decimal(1) + monthly_rate) ** tenure_months
        future_value = (monthly_investment * ((factor - Decimal(1)) / monthly_rate) * (Decimal(1) + monthly_rate)).quantize(PAISE_UNIT, rounding=ROUND_HALF_UP)
        
    wealth_gain = (future_value - total_invested).quantize(PAISE_UNIT, rounding=ROUND_HALF_UP)
    
    return {
        "monthly_investment": str(monthly_investment.quantize(PAISE_UNIT)),
        "total_invested": str(total_invested),
        "wealth_gain": str(wealth_gain),
        "future_value": str(future_value),
        "tenure_months": tenure_months,
        "annual_expected_return_pct": str(annual_expected_return_pct),
        "note": "Mutual fund investments are subject to market risks. Calculations are illustrative."
    }


def calculate_emergency_fund(monthly_mandatory_expenses: Decimal, target_months: int = 6) -> dict[str, Any]:
    """Calculate recommended emergency fund buffer based on mandatory monthly expenses."""
    if monthly_mandatory_expenses <= 0 or target_months <= 0:
        raise ValueError("Expenses and target months must be strictly positive.")
        
    conservative_fund = (monthly_mandatory_expenses * Decimal(target_months)).quantize(PAISE_UNIT, rounding=ROUND_HALF_UP)
    minimum_fund = (monthly_mandatory_expenses * Decimal(3)).quantize(PAISE_UNIT, rounding=ROUND_HALF_UP)
    
    return {
        "monthly_mandatory_expenses": str(monthly_mandatory_expenses.quantize(PAISE_UNIT)),
        "target_months": target_months,
        "recommended_fund": str(conservative_fund),
        "minimum_safe_fund": str(minimum_fund),
        "allocation_guideline": "Keep 50% in instant savings account, 50% in high-liquidity sweep FD / overnight fund."
    }


def calculate_compound_interest(principal: Decimal, annual_rate_pct: Decimal, tenure_years: Decimal, compounding_frequency: int = 1) -> dict[str, Any]:
    """Calculate compound interest: A = P(1 + r/n)^(nt)."""
    if principal <= 0 or tenure_years <= 0 or compounding_frequency <= 0:
        raise ValueError("Principal, years, and frequency must be strictly positive.")
        
    r = annual_rate_pct / Decimal(100)
    n = Decimal(compounding_frequency)
    t = tenure_years
    
    final_amount = (principal * (Decimal(1) + (r / n)) ** int(n * t)).quantize(PAISE_UNIT, rounding=ROUND_HALF_UP)
    interest_earned = (final_amount - principal).quantize(PAISE_UNIT, rounding=ROUND_HALF_UP)
    
    return {
        "principal": str(principal.quantize(PAISE_UNIT)),
        "annual_rate_pct": str(annual_rate_pct),
        "tenure_years": str(tenure_years),
        "final_amount": str(final_amount),
        "interest_earned": str(interest_earned)
    }

