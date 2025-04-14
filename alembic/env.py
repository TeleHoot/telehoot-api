import time
from typing import Callable
from logging.config import fileConfig
from pathlib import Path
import logging

from sqlalchemy import engine_from_config, pool, inspect, Integer, Column, String, TIMESTAMP, text
from alembic import context  # type: ignore
import src.core as core
import os
import yaml
from alembic import context
from sqlalchemy import MetaData, Table
from sqlalchemy.orm import sessionmaker
import src.app.models # !needed for alembic to detect models

# This is the Alembic Config object, which provides
# access to the values within the .ini file in use.
alembic_config = context.config
settings = core.config.get_settings()

section = alembic_config.config_ini_section
alembic_config.set_section_option(section, "DATABASE_URL", settings.POSTGRES.URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if alembic_config.config_file_name is not None:
    fileConfig(alembic_config.config_file_name)

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = core.models.sqlalchemy.Base.metadata

def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well. By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = alembic_config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def ensure_seed_history_table_exists(connection):
    """
    Creates the `seed_history` table if it does not exist.

    :param connection: The database connection object.
    """
    metadata = MetaData()

    # Define the structure of the `seed_history` table
    seed_history_table = Table(
        'seed_history',
        metadata,
        Column('id', Integer, primary_key=True, autoincrement=True),  # Auto-incrementing service field
        Column('seed_id', String(255), nullable=False, unique=True),  # Unique seed identifier
        Column('table_name', String(255), nullable=False),
        Column('applied_at', TIMESTAMP, server_default=text('CURRENT_TIMESTAMP'))
    )

    # Check if the table exists
    inspector = inspect(connection)
    if 'seed_history' not in inspector.get_table_names():
        # Create the table
        metadata.create_all(bind=connection)
        logger.info("Table `seed_history` created.")

def run_seeds_after_migrate(connection):
    """
    Applies seeds from the `seeds.yml` file, skipping already applied records.

    :param connection: The database connection object.
    """
    ensure_seed_history_table_exists(connection)

    # Create a session
    Session = sessionmaker(bind=connection)
    session = Session()

    seeds_file_path = os.path.join(Path(__file__).resolve().parent, 'seeds.yml')
    if not os.path.exists(seeds_file_path):
        logger.error(f"File `seeds.yml` not found: {seeds_file_path}")
        return

    with open(seeds_file_path, 'r') as f:
        seeds_data = yaml.safe_load(f)

    if not seeds_data:
        logger.warning("File `seeds.yml` is empty.")
        return

    metadata = MetaData()
    metadata.reflect(bind=connection)

    # Apply seeds in the order they appear in the file
    for table_name, rows in seeds_data.items():
        if table_name not in metadata.tables:
            logger.error(f"Table `{table_name}` not found in the database.")
            continue

        table = metadata.tables[table_name]
        # Get a list of already applied `seed_id`s for this table
        applied_seeds = {
            row.seed_id for row in session.execute(
                text("SELECT seed_id FROM seed_history WHERE table_name = :table_name"),
                {'table_name': table_name}
            )
        }

        # Filter records, keeping only those that haven't been applied yet
        new_rows = []
        for row in rows:
            seed_id = row.get('seed_id')  # Unique seed identifier
            if not seed_id:
                logger.warning(f"Record in table `{table_name}` does not contain 'seed_id'. Skipping.")
                continue
            if seed_id in applied_seeds:
                continue
            new_rows.append(row)

        if not new_rows:
            continue

        # Insert new records
        session.execute(table.insert(), new_rows)

        # Record the application of data for each record
        for row in new_rows:
            seed_id = row.get('seed_id')
            session.execute(
                text("INSERT INTO seed_history (seed_id, table_name) VALUES (:seed_id, :table_name)"),
                {'seed_id': seed_id, 'table_name': table_name}
            )

        logger.info(f"Data for table `{table_name}` applied. Added {len(new_rows)} records.")

    session.commit()

def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario, we need to create an Engine
    and associate a connection with the context.
    """
    connectable = engine_from_config(
        alembic_config.get_section(alembic_config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        def include_object(object, name, type_, reflected, compare_to):
            if type_ == "table" and name == "seed_history":
                return False
            return True

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,  # Добавляем фильтр
        )

        with context.begin_transaction():
            context.run_migrations()

            # Apply seeds only if the `run_seeds` x-argument is present
            x_args = context.get_x_argument(as_dictionary=True)
            if x_args.get('run_seeds', 'false').lower() == 'true':
                run_seeds_after_migrate(connection)

def retry_with_backoff(
    func: Callable,
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
):
    """
    Executes a function with retries and exponential backoff.

    :param func: The function to execute.
    :param max_attempts: Maximum number of attempts.
    :param initial_delay: Initial delay in seconds.
    :param backoff_factor: Multiplier for increasing delay after each failed attempt.
    """
    attempt = 1
    delay = initial_delay

    while attempt <= max_attempts:
        try:
            func()
            break  # Successful execution, exit the loop
        except Exception as e:
            logger.error(f"Attempt {attempt} of {max_attempts} failed: {e}")
            if attempt == max_attempts:
                raise  # If attempts are exhausted, re-raise the exception

            # Increase delay exponentially
            time.sleep(delay)
            delay *= backoff_factor
            attempt += 1

if context.is_offline_mode():
    run_migrations_offline()
else:
    retry_with_backoff(
        run_migrations_online,
        max_attempts=5,
        initial_delay=1.5,
        backoff_factor=2.0,
    )
