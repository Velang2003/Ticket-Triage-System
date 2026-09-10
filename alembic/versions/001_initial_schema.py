"""Initial database schema.

Revision: 001
- Enables pgvector extension
- Creates all 5 tables: tickets, classifications, knowledge_articles,
  resolution_suggestions, audit_log
- Adds HNSW index on knowledge_articles.embedding for fast cosine search
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import pgvector.sqlalchemy

revision = "001"
down_revision = None
branch_labels = None
depends_on = None

EMBEDDING_DIM = 768


def upgrade() -> None:
    # pgvector extension is already enabled by env.py, but safe to repeat
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── tickets ───────────────────────────────────────────────
    op.create_table(
        "tickets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("subject", sa.String(200), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("submitter_email", sa.String(255), nullable=False),
        sa.Column(
            "category",
            sa.Enum("Billing", "Technical", "Account", "Other", name="ticket_category"),
            nullable=True,
        ),
        sa.Column(
            "priority",
            sa.Enum("Low", "Medium", "High", "Critical", name="ticket_priority"),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.Enum("Open", "In Progress", "Resolved", "Closed", name="ticket_status"),
            nullable=False,
            server_default="Open",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_tickets_status", "tickets", ["status"])
    op.create_index("ix_tickets_category", "tickets", ["category"])
    op.create_index("ix_tickets_priority", "tickets", ["priority"])
    op.create_index("ix_tickets_created_at", "tickets", ["created_at"])

    # ── classifications ───────────────────────────────────────
    op.create_table(
        "classifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ticket_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tickets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("predicted_category", sa.String(50), nullable=True),
        sa.Column("predicted_priority", sa.String(50), nullable=True),
        sa.Column("confidence_note", sa.Text, nullable=True),
        sa.Column("is_pending", sa.Boolean, nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_classifications_ticket_id", "classifications", ["ticket_id"])

    # ── knowledge_articles ────────────────────────────────────
    op.create_table(
        "knowledge_articles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("embedding", pgvector.sqlalchemy.Vector(EMBEDDING_DIM), nullable=True),
        sa.Column(
            "category",
            sa.Enum("Billing", "Technical", "Account", "Other", name="ticket_category"),
            nullable=True,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_knowledge_articles_category", "knowledge_articles", ["category"])
    # HNSW index for fast approximate nearest-neighbour on cosine distance
    op.execute(
        "CREATE INDEX ix_knowledge_articles_embedding_hnsw "
        "ON knowledge_articles USING hnsw (embedding vector_cosine_ops)"
    )

    # ── resolution_suggestions ────────────────────────────────
    op.create_table(
        "resolution_suggestions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ticket_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tickets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("suggested_text", sa.Text, nullable=False),
        sa.Column(
            "source_article_ids",
            postgresql.JSON,
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_resolution_suggestions_ticket_id", "resolution_suggestions", ["ticket_id"]
    )

    # ── audit_log ─────────────────────────────────────────────
    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "ticket_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tickets.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("details", postgresql.JSON, nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_audit_log_ticket_id", "audit_log", ["ticket_id"])
    op.create_index("ix_audit_log_event_type", "audit_log", ["event_type"])


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_table("resolution_suggestions")
    op.drop_table("knowledge_articles")
    op.drop_table("classifications")
    op.drop_table("tickets")
    op.execute("DROP TYPE IF EXISTS ticket_category")
    op.execute("DROP TYPE IF EXISTS ticket_priority")
    op.execute("DROP TYPE IF EXISTS ticket_status")

