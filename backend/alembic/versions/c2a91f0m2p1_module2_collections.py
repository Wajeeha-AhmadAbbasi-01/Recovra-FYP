"""module 2 collections and mock inbox tables

Revision ID: c2a91f0m2p1
Revises: b313838edb42
Create Date: 2026-11-22

NOT APPLIED. Operator must approve before `alembic upgrade head`.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c2a91f0m2p1"
down_revision: Union[str, None] = "b313838edb42"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TS = sa.text("now()")


def upgrade() -> None:
    op.add_column("audit_events", sa.Column("origin", sa.String(length=32), nullable=True))
    op.add_column("audit_events", sa.Column("correlation_id", sa.String(length=64), nullable=True))

    op.create_table(
        "collection_cases",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("invoice_id", sa.UUID(), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_TS, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_TS, nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "invoice_id", name="uq_collection_cases_tenant_invoice"),
    )
    op.create_index("ix_collection_cases_tenant_id", "collection_cases", ["tenant_id"])

    op.create_table(
        "follow_up_tasks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("invoice_id", sa.UUID(), nullable=False),
        sa.Column("task_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("assignee_id", sa.UUID(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("dedupe_key", sa.String(length=255), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_TS, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_TS, nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_by", sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(["assignee_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["case_id"], ["collection_cases.id"]),
        sa.ForeignKeyConstraint(["completed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "dedupe_key", name="uq_follow_up_tasks_tenant_dedupe"),
    )
    op.create_index("ix_follow_up_tasks_tenant_id", "follow_up_tasks", ["tenant_id"])
    op.create_index("ix_follow_up_tasks_invoice_id", "follow_up_tasks", ["invoice_id"])

    op.create_table(
        "reminder_policies",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("grace_days", sa.Integer(), nullable=False),
        sa.Column("timezone_name", sa.String(length=64), nullable=False),
        sa.Column("risk_level", sa.String(length=32), nullable=False),
        sa.Column("policy_version", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_TS, nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", name="uq_reminder_policies_tenant"),
    )

    op.create_table(
        "payment_promises",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("invoice_id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("promised_date", sa.Date(), nullable=False),
        sa.Column("follow_up_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("recorded_by", sa.UUID(), nullable=False),
        sa.Column("confirmed_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_TS, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_TS, nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["collection_cases.id"]),
        sa.ForeignKeyConstraint(["confirmed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_payment_promises_tenant_id", "payment_promises", ["tenant_id"])
    op.create_index("ix_payment_promises_invoice_id", "payment_promises", ["invoice_id"])

    op.create_table(
        "disputes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("invoice_id", sa.UUID(), nullable=False),
        sa.Column("case_id", sa.UUID(), nullable=False),
        sa.Column("challenged_amount", sa.Numeric(precision=18, scale=2), nullable=True),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("recorded_by", sa.UUID(), nullable=False),
        sa.Column("confirmed_by", sa.UUID(), nullable=True),
        sa.Column("resolved_by", sa.UUID(), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_TS, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_TS, nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["collection_cases.id"]),
        sa.ForeignKeyConstraint(["confirmed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.ForeignKeyConstraint(["recorded_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["resolved_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_disputes_tenant_id", "disputes", ["tenant_id"])
    op.create_index("ix_disputes_invoice_id", "disputes", ["invoice_id"])

    op.create_table(
        "reminder_holds",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("invoice_id", sa.UUID(), nullable=False),
        sa.Column("hold_reason", sa.String(length=32), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_TS, nullable=False),
        sa.Column("released_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reminder_holds_tenant_id", "reminder_holds", ["tenant_id"])
    op.create_index("ix_reminder_holds_invoice_id", "reminder_holds", ["invoice_id"])

    op.create_table(
        "mailboxes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("folder", sa.String(length=128), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_TS, nullable=False),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "provider", name="uq_mailboxes_tenant_provider"),
    )
    op.create_index("ix_mailboxes_tenant_id", "mailboxes", ["tenant_id"])

    op.create_table(
        "inbound_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("mailbox_id", sa.UUID(), nullable=False),
        sa.Column("folder", sa.String(length=128), nullable=False),
        sa.Column("uidvalidity", sa.Integer(), nullable=False),
        sa.Column("uid", sa.Integer(), nullable=False),
        sa.Column("rfc_message_id", sa.String(length=512), nullable=True),
        sa.Column("sender", sa.String(length=320), nullable=False),
        sa.Column("recipient", sa.String(length=320), nullable=False),
        sa.Column("subject", sa.String(length=998), nullable=False),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sanitized_body", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(length=128), nullable=False),
        sa.Column("ingestion_state", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_TS, nullable=False),
        sa.ForeignKeyConstraint(["mailbox_id"], ["mailboxes.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "tenant_id",
            "mailbox_id",
            "folder",
            "uidvalidity",
            "uid",
            name="uq_inbound_messages_uid",
        ),
    )
    op.create_index("ix_inbound_messages_tenant_id", "inbound_messages", ["tenant_id"])

    op.create_table(
        "message_invoice_links",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("tenant_id", sa.UUID(), nullable=False),
        sa.Column("message_id", sa.UUID(), nullable=False),
        sa.Column("invoice_id", sa.UUID(), nullable=False),
        sa.Column("link_state", sa.String(length=32), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("confirmed_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=_TS, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=_TS, nullable=False),
        sa.ForeignKeyConstraint(["confirmed_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoices.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["inbound_messages.id"]),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "message_id", "invoice_id", name="uq_message_invoice_link"),
    )
    op.create_index("ix_message_invoice_links_tenant_id", "message_invoice_links", ["tenant_id"])
    op.create_index("ix_message_invoice_links_message_id", "message_invoice_links", ["message_id"])


def downgrade() -> None:
    op.drop_index("ix_message_invoice_links_message_id", table_name="message_invoice_links")
    op.drop_index("ix_message_invoice_links_tenant_id", table_name="message_invoice_links")
    op.drop_table("message_invoice_links")
    op.drop_index("ix_inbound_messages_tenant_id", table_name="inbound_messages")
    op.drop_table("inbound_messages")
    op.drop_index("ix_mailboxes_tenant_id", table_name="mailboxes")
    op.drop_table("mailboxes")
    op.drop_index("ix_reminder_holds_invoice_id", table_name="reminder_holds")
    op.drop_index("ix_reminder_holds_tenant_id", table_name="reminder_holds")
    op.drop_table("reminder_holds")
    op.drop_index("ix_disputes_invoice_id", table_name="disputes")
    op.drop_index("ix_disputes_tenant_id", table_name="disputes")
    op.drop_table("disputes")
    op.drop_index("ix_payment_promises_invoice_id", table_name="payment_promises")
    op.drop_index("ix_payment_promises_tenant_id", table_name="payment_promises")
    op.drop_table("payment_promises")
    op.drop_table("reminder_policies")
    op.drop_index("ix_follow_up_tasks_invoice_id", table_name="follow_up_tasks")
    op.drop_index("ix_follow_up_tasks_tenant_id", table_name="follow_up_tasks")
    op.drop_table("follow_up_tasks")
    op.drop_index("ix_collection_cases_tenant_id", table_name="collection_cases")
    op.drop_table("collection_cases")
    op.drop_column("audit_events", "correlation_id")
    op.drop_column("audit_events", "origin")
