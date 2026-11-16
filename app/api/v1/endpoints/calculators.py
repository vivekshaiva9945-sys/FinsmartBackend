from typing import Any
from fastapi import APIRouter, HTTPException, status
from app.core.money import calculate_compound_interest, calculate_emergency_fund, calculate_emi, calculate_sip
from app.schemas.calculator import CompoundInterestIn, EMICalculatorIn, EmergencyFundIn, SIPCalculatorIn

router = APIRouter()


@router.post("/emi", response_model=dict[str, Any])
async def emi_endpoint(payload: EMICalculatorIn):
    """Calculate loan equated monthly installment (EMI), total interest, and total payable amount."""
    try:
        return calculate_emi(
            principal=payload.principal,
            annual_interest_pct=payload.annual_rate,
            tenure_months=payload.months
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/sip", response_model=dict[str, Any])
async def sip_endpoint(payload: SIPCalculatorIn):
    """Calculate future value of systematic investment plan (SIP) and total wealth gained."""
    try:
        return calculate_sip(
            monthly_investment=payload.monthly,
            annual_expected_return_pct=payload.annual_rate,
            tenure_months=payload.months
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/emergency-fund", response_model=dict[str, Any])
async def emergency_fund_endpoint(payload: EmergencyFundIn):
    """Calculate emergency fund size based on monthly essential expenses and safety buffer target."""
    try:
        return calculate_emergency_fund(
            monthly_mandatory_expenses=payload.monthly_expenses,
            target_months=payload.target_months
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/compound", response_model=dict[str, Any])
async def compound_endpoint(payload: CompoundInterestIn):
    """Calculate compound interest accumulation across years."""
    try:
        return calculate_compound_interest(
            principal=payload.principal,
            annual_rate_pct=payload.annual_rate,
            tenure_years=payload.years,
            compounding_frequency=payload.compounding_frequency
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

