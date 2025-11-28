"""
Database connection and session management.
"""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(
    f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}",
    echo=False,  # Set to True for SQL query logging
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,
    max_overflow=20
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """
    Dependency function to get database session.
    Used with FastAPI's Depends().
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_and_create_tables():
    """
    Check if required tables exist, and create them if they don't.
    This function is called during application startup.
    """
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        
        # Check if sentiment_analysis table exists
        if 'sentiment_analysis' not in existing_tables:
            logger.info("sentiment_analysis table not found. Creating table...")
            create_sentiment_analysis_table()
            logger.info("sentiment_analysis table created successfully")
        else:
            logger.info("sentiment_analysis table already exists")
            # Migrate source_id column type from BIGINT to VARCHAR if needed
            migrate_source_id_column_type()
        
        # Check if indexes exist
        check_and_create_indexes()
        
    except Exception as e:
        logger.error(f"Error checking/creating tables: {e}", exc_info=True)
        raise


def create_sentiment_analysis_table():
    """
    Create the sentiment_analysis table if it doesn't exist.
    """
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS sentiment_analysis (
        id VARCHAR PRIMARY KEY,
        source_id VARCHAR NOT NULL,
        source_type VARCHAR(20) NOT NULL,
        sentiment VARCHAR(20) NOT NULL,
        sentiment_score DECIMAL(5,4),
        top_emotion VARCHAR(50),
        emotion_scores JSONB,
        analyzed_text TEXT,
        created_at TIMESTAMP DEFAULT NOW() NOT NULL
    );
    """
    
    with engine.connect() as connection:
        connection.execute(text(create_table_sql))
        connection.commit()
        logger.info("Created sentiment_analysis table")


def migrate_source_id_column_type():
    """
    Migrate source_id column from BIGINT to VARCHAR if it's currently BIGINT.
    This migration handles the change to store original string IDs instead of hashed integers.
    """
    try:
        with engine.connect() as connection:
            # Check current column type
            check_column_type_sql = """
            SELECT data_type 
            FROM information_schema.columns 
            WHERE table_name = 'sentiment_analysis' 
            AND column_name = 'source_id';
            """
            
            result = connection.execute(text(check_column_type_sql))
            row = result.fetchone()
            
            if row and row[0] == 'bigint':
                logger.info("Migrating source_id column from BIGINT to VARCHAR...")
                # Drop indexes that depend on source_id first
                drop_indexes_sql = [
                    "DROP INDEX IF EXISTS idx_sentiment_analysis_source_id;",
                    "DROP INDEX IF EXISTS idx_sentiment_analysis_source;"
                ]
                
                for sql in drop_indexes_sql:
                    try:
                        connection.execute(text(sql))
                        connection.commit()
                    except Exception as e:
                        logger.warning(f"Error dropping index (may not exist): {e}")
                
                # Convert existing numeric source_id values to strings
                # Since we can't reverse the hash, we'll convert them to string representation
                convert_data_sql = """
                UPDATE sentiment_analysis 
                SET source_id = CAST(source_id AS VARCHAR)
                WHERE source_id IS NOT NULL;
                """
                connection.execute(text(convert_data_sql))
                connection.commit()
                
                # Alter column type to VARCHAR
                alter_column_sql = """
                ALTER TABLE sentiment_analysis 
                ALTER COLUMN source_id TYPE VARCHAR USING source_id::VARCHAR;
                """
                connection.execute(text(alter_column_sql))
                connection.commit()
                
                logger.info("Successfully migrated source_id column to VARCHAR")
            elif row and row[0] == 'character varying':
                logger.info("source_id column is already VARCHAR, no migration needed")
            else:
                logger.info(f"source_id column type is {row[0] if row else 'unknown'}, skipping migration")
                
    except Exception as e:
        logger.warning(f"Error migrating source_id column type: {e}. This is safe to ignore if column type is already correct.")


def check_and_create_indexes():
    """
    Check if indexes exist and create them if they don't.
    """
    indexes_sql = [
        "CREATE INDEX IF NOT EXISTS idx_sentiment_analysis_source_id ON sentiment_analysis(source_id);",
        "CREATE INDEX IF NOT EXISTS idx_sentiment_analysis_source_type ON sentiment_analysis(source_type);",
        "CREATE INDEX IF NOT EXISTS idx_sentiment_analysis_created_at ON sentiment_analysis(created_at);",
        "CREATE INDEX IF NOT EXISTS idx_sentiment_analysis_source ON sentiment_analysis(source_id, source_type);"
    ]
    
    try:
        with engine.connect() as connection:
            for index_sql in indexes_sql:
                try:
                    connection.execute(text(index_sql))
                    connection.commit()
                except Exception as e:
                    logger.warning(f"Error creating index (may already exist): {e}")
            logger.info("Indexes checked/created successfully")
    except Exception as e:
        logger.warning(f"Error checking/creating indexes: {e}")

