from decimal import Decimal
from pydantic import BaseModel, Field


class EMICalculatorIn(BaseModel):
    principal: Decimal = Field(gt=0, description="Loan amount in rupees", example=100000)
    annual_rate: Decimal = Field(ge=0, le=100, description="Annual interest rate percentage", example=10.5)
    months: int = Field(gt=0, le=600, description="Loan tenure in months", example=12)


class SIPCalculatorIn(BaseModel):
    monthly: Decimal = Field(gt=0, description="Monthly investment in rupees", example=2000)
    annual_rate: Decimal = Field(ge=0, le=50, description="Expected annual return percentage", example=12.0)
    months: int = Field(gt=0, le=600, description="Investment duration in months", example=36)


class EmergencyFundIn(BaseModel):
    monthly_expenses: Decimal = Field(gt=0, description="Essential monthly living costs in rupees", example=15000)
    target_months: int = Field(default=6, ge=1, le=24, description="Target months buffer", example=6)


class CompoundInterestIn(BaseModel):
    principal: Decimal = Field(gt=0, description="Initial principal deposit in rupees", example=50000)
    annual_rate: Decimal = Field(ge=0, le=100, description="Annual interest rate percentage", example=7.5)
    years: Decimal = Field(gt=0, le=50, description="Tenure in years", example=5)
    compounding_frequency: int = Field(default=1, ge=1, le=12, description="Compounding frequency per year")

