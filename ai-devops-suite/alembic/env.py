"""Alembic environment configuration."""

from alembic import context

from devops_suite.models.telemetry import Base

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url="sqlite:///./test.db", target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    raise NotImplementedError("Use async migration runner for production")


if context.is_offline_mode():
    run_migrations_offline()
