import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token, hash_password, verify_password
from app.core.tenant import AuthenticatedContext, TenantContext, get_current_user, get_tenant_db
from app.schemas.auth import TokenResponse, UserLogin, UserOut, UserRegister

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister, tenant: TenantContext = Depends(get_tenant_db)):
    """
    Registers a new user scoped to the active tenant/college.
    Strictly requires DPDP Act 2023 consent for financial data processing.
    """
    if payload.honeypot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Automated spam bot submission detected."
        )

    if not payload.consent_data_processing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explicit consent for data processing is legally required under India's DPDP Act 2023."
        )

    user_id = uuid.uuid4()
    hashed_pw = hash_password(payload.password)
    
    try:
        await tenant.session.execute(
            text("""
                INSERT INTO users (id, tenant_id, email, password_hash, full_name, phone_number, role)
                VALUES (:id, :tenant_id, :email, :password_hash, :full_name, :phone_number, :role)
            """),
            {
                "id": user_id,
                "tenant_id": tenant.tenant_id,
                "email": payload.email.lower().strip(),
                "password_hash": hashed_pw,
                "full_name": payload.full_name.strip(),
                "phone_number": payload.phone_number,
                "role": payload.role
            }
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"An account with email '{payload.email}' already exists in this institution."
        )

    # Automatically create default primary cash and bank accounts
    await tenant.session.execute(
        text("""
            INSERT INTO accounts (tenant_id, user_id, name, account_type, balance_minor)
            VALUES 
            (:t, :u, 'Bank Account', 'BANK', 0),
            (:t, :u, 'Cash in Hand', 'CASH', 0)
        """),
        {"t": tenant.tenant_id, "u": user_id}
    )

    # Automatically log initial DPDP consent
    await tenant.session.execute(
        text("""
            INSERT INTO consents (tenant_id, user_id, purpose, granted)
            VALUES 
            (:t, :u, 'budget_tracking', true),
            (:t, :u, 'scheme_eligibility', true)
        """),
        {"t": tenant.tenant_id, "u": user_id}
    )

    token = create_access_token(user_id=user_id, tenant_id=tenant.tenant_id, role=payload.role)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user_id,
        tenant_id=tenant.tenant_id,
        role=payload.role,
        full_name=payload.full_name,
        email=payload.email.lower().strip()
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin, tenant: TenantContext = Depends(get_tenant_db)):
    """Authenticate user with email and password within the active tenant or fallback."""
    if payload.honeypot:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Automated spam bot submission detected."
        )

    res = await tenant.session.execute(
        text("""
            SELECT id, email, password_hash, full_name, role, is_active, tenant_id
            FROM users
            WHERE email = :email AND tenant_id = :tenant_id
        """),
        {"email": payload.email.lower().strip(), "tenant_id": tenant.tenant_id}
    )
    user = res.first()
    active_tenant_id = tenant.tenant_id

    # Fallback to locate user by email across tenants if header mismatched
    if not user:
        res_fb = await tenant.session.execute(
            text("""
                SELECT id, email, password_hash, full_name, role, is_active, tenant_id
                FROM users
                WHERE email = :email
            """),
            {"email": payload.email.lower().strip()}
        )
        user = res_fb.first()
        if user:
            active_tenant_id = user.tenant_id
    
    is_verified = verify_password(payload.password, user.password_hash) if user else False

    if not user or not is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deactivated. Please contact your administrator."
        )

    token = create_access_token(user_id=user.id, tenant_id=active_tenant_id, role=user.role)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.id,
        tenant_id=active_tenant_id,
        role=user.role,
        full_name=user.full_name,
        email=user.email
    )


@router.get("/me", response_model=UserOut)
async def get_me(ctx: AuthenticatedContext = Depends(get_current_user)):
    """Fetch current authenticated user profile."""
    res = await ctx.session.execute(
        text("SELECT id, tenant_id, email, full_name, phone_number, role, is_active, created_at FROM users WHERE id = :uid"),
        {"uid": ctx.user_id}
    )
    user = res.first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
    return UserOut(**dict(user._mapping))

