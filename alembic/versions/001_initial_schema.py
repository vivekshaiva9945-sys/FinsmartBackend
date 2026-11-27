"""001_initial_schema

Revision ID: 001_initial
Revises: None
Create Date: 2026-11-27

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Tenants
    op.create_table(
        'tenants',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('slug', sa.String(), unique=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('domain', sa.String(), nullable=True),
        sa.Column('subscription_tier', sa.String(), server_default='standard', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 2. Users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('full_name', sa.String(), nullable=False),
        sa.Column('phone_number', sa.String(), nullable=True),
        sa.Column('role', sa.String(), server_default='student', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('tenant_id', 'email', name='uq_users_tenant_email'),
        sa.CheckConstraint("role IN ('student', 'faculty', 'college_admin', 'admin')", name='chk_user_role'),
    )

    # 3. User Profiles
    op.create_table(
        'user_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('age', sa.Integer(), nullable=True),
        sa.Column('gender', sa.String(), nullable=True),
        sa.Column('state', sa.String(), server_default='Karnataka', nullable=False),
        sa.Column('district', sa.String(), nullable=True),
        sa.Column('is_student', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('academic_year', sa.String(), nullable=True),
        sa.Column('department', sa.String(), nullable=True),
        sa.Column('annual_family_income_minor', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('social_category', sa.String(), server_default='GEN', nullable=False),
        sa.Column('has_bank_account', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('has_disability', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('ration_card_type', sa.String(), server_default='None', nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('age >= 0 AND age <= 120', name='chk_profile_age'),
        sa.CheckConstraint("gender IN ('male', 'female', 'other', 'prefer_not_to_say')", name='chk_profile_gender'),
        sa.CheckConstraint("social_category IN ('GEN', 'OBC', 'SC', 'ST', 'EWS')", name='chk_profile_social_cat'),
        sa.CheckConstraint("ration_card_type IN ('BPL', 'APL', 'AAY', 'None')", name='chk_profile_ration_card'),
    )

    # 4. Accounts
    op.create_table(
        'accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('account_type', sa.String(), server_default='BANK', nullable=False),
        sa.Column('balance_minor', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('currency', sa.CHAR(3), server_default='INR', nullable=False),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("account_type IN ('BANK', 'CASH', 'WALLET', 'SAVINGS')", name='chk_account_type'),
    )

    # 5. Transactions
    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('accounts.id', ondelete='SET NULL'), nullable=True),
        sa.Column('client_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount_minor', sa.BigInteger(), nullable=False),
        sa.Column('currency', sa.CHAR(3), server_default='INR', nullable=False),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('payment_mode', sa.String(), server_default='UPI', nullable=False),
        sa.Column('description', sa.String(), server_default='', nullable=False),
        sa.Column('occurred_on', sa.Date(), server_default=sa.func.current_date(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('user_id', 'client_id', name='uq_transactions_user_client_id'),
        sa.CheckConstraint('amount_minor > 0', name='chk_transaction_amount_positive'),
        sa.CheckConstraint("kind IN ('DEBIT', 'CREDIT')", name='chk_transaction_kind'),
        sa.CheckConstraint("payment_mode IN ('CASH', 'UPI', 'CARD', 'BANK', 'WALLET')", name='chk_transaction_payment_mode'),
    )
    op.create_index('idx_transactions_user_date', 'transactions', ['user_id', sa.text('occurred_on DESC')])
    op.create_index('idx_transactions_tenant_user', 'transactions', ['tenant_id', 'user_id'])

    # 6. Budgets
    op.create_table(
        'budgets',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('limit_minor', sa.BigInteger(), nullable=False),
        sa.Column('period', sa.String(), server_default='MONTHLY', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint('user_id', 'category', 'period', name='uq_budgets_user_cat_period'),
        sa.CheckConstraint('limit_minor > 0', name='chk_budget_limit_positive'),
        sa.CheckConstraint("period IN ('MONTHLY', 'SEMESTER', 'YEARLY')", name='chk_budget_period'),
    )

    # 7. Goals
    op.create_table(
        'goals',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('target_minor', sa.BigInteger(), nullable=False),
        sa.Column('saved_minor', sa.BigInteger(), server_default='0', nullable=False),
        sa.Column('target_date', sa.Date(), nullable=True),
        sa.Column('category', sa.String(), server_default='General', nullable=False),
        sa.Column('is_completed', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint('target_minor > 0', name='chk_goal_target_positive'),
    )

    # 8. Consents
    op.create_table(
        'consents',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tenants.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('purpose', sa.String(), nullable=False),
        sa.Column('granted', sa.Boolean(), nullable=False),
        sa.Column('at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # 9. Schemes
    op.create_table(
        'schemes',
        sa.Column('code', sa.String(), primary_key=True),
        sa.Column('title_en', sa.String(), nullable=False),
        sa.Column('title_kn', sa.String(), nullable=True),
        sa.Column('title_hi', sa.String(), nullable=True),
        sa.Column('agency', sa.String(), nullable=False),
        sa.Column('category', sa.String(), server_default='Welfare', nullable=False),
        sa.Column('summary', sa.String(), nullable=False),
        sa.Column('benefits', sa.String(), nullable=False),
        sa.Column('source_url', sa.String(), nullable=False),
        sa.Column('documents_required', sa.ARRAY(sa.String()), server_default='{}', nullable=False),
        sa.Column('application_steps', sa.ARRAY(sa.String()), server_default='{}', nullable=False),
        sa.Column('last_verified_at', sa.Date(), nullable=True),
        sa.Column('rule', postgresql.JSONB(), nullable=False),
    )

    # 10. Learning Modules
    op.create_table(
        'learning_modules',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('lang', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('summary', sa.String(), nullable=False),
        sa.Column('body', sa.String(), nullable=False),
        sa.Column('quiz', postgresql.JSONB(), server_default='[]', nullable=False),
        sa.CheckConstraint("lang IN ('en', 'kn', 'hi')", name='chk_learning_lang'),
    )

    # 11. Knowledge Docs
    op.create_table(
        'knowledge_docs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('source_citation', sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('knowledge_docs')
    op.drop_table('learning_modules')
    op.drop_table('schemes')
    op.drop_table('consents')
    op.drop_table('goals')
    op.drop_table('budgets')
    op.drop_table('transactions')
    op.drop_table('accounts')
    op.drop_table('user_profiles')
    op.drop_table('users')
    op.drop_table('tenants')
