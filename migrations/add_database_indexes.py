"""
Database Optimization: Add Indexes
Migration script to add performance indexes to all tables
"""
from app import create_app, db
from sqlalchemy import Index, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def add_indexes():
    """
    Add performance indexes to database tables

    Indexes are added for frequently queried columns:
    - Foreign keys
    - Status columns
    - Timestamp columns (for sorting/filtering)
    - Search columns
    """
    app = create_app('production')

    with app.app_context():
        engine = db.engine

        # Get current indexes
        inspector = db.inspect(engine)

        def index_exists(table_name, index_name):
            """Check if index already exists"""
            existing_indexes = {idx['name'] for idx in inspector.get_indexes(table_name)}
            return index_name in existing_indexes

        indexes_to_create = []

        # ==================== ImportTask Indexes ====================
        if not index_exists('import_task', 'idx_import_task_status'):
            indexes_to_create.append(
                ('import_task', 'idx_import_task_status', ['status'])
            )

        if not index_exists('import_task', 'idx_import_task_created'):
            indexes_to_create.append(
                ('import_task', 'idx_import_task_created', ['created_at'])
            )

        if not index_exists('import_task', 'idx_import_task_completed'):
            indexes_to_create.append(
                ('import_task', 'idx_import_task_completed', ['completed_at'])
            )

        # ==================== Link Indexes ====================
        if not index_exists('link', 'idx_link_task_id'):
            indexes_to_create.append(
                ('link', 'idx_link_task_id', ['task_id'])
            )

        if not index_exists('link', 'idx_link_source'):
            indexes_to_create.append(
                ('link', 'idx_link_source', ['source'])
            )

        if not index_exists('link', 'idx_link_validation_status'):
            indexes_to_create.append(
                ('link', 'idx_link_validation_status', ['validation_status'])
            )

        if not index_exists('link', 'idx_link_imported_at'):
            indexes_to_create.append(
                ('link', 'idx_link_imported_at', ['imported_at'])
            )

        if not index_exists('link', 'idx_link_priority'):
            indexes_to_create.append(
                ('link', 'idx_link_priority', ['priority'])
            )

        # Composite index for common query pattern
        if not index_exists('link', 'idx_link_task_status'):
            indexes_to_create.append(
                ('link', 'idx_link_task_status', ['task_id', 'validation_status'])
            )

        # ==================== ParsedContent Indexes ====================
        if not index_exists('parsed_content', 'idx_parsed_content_link_id'):
            indexes_to_create.append(
                ('parsed_content', 'idx_parsed_content_link_id', ['link_id'])
            )

        if not index_exists('parsed_content', 'idx_parsed_content_active'):
            indexes_to_create.append(
                ('parsed_content', 'idx_parsed_content_active', ['is_active'])
            )

        if not index_exists('parsed_content', 'idx_parsed_content_created'):
            indexes_to_create.append(
                ('parsed_content', 'idx_parsed_content_created', ['created_at'])
            )

        # ==================== AIProcessedContent Indexes ====================
        if not index_exists('ai_processed_content', 'idx_ai_content_parsed_id'):
            indexes_to_create.append(
                ('ai_processed_content', 'idx_ai_content_parsed_id', ['parsed_content_id'])
            )

        if not index_exists('ai_processed_content', 'idx_ai_content_active'):
            indexes_to_create.append(
                ('ai_processed_content', 'idx_ai_content_active', ['is_active'])
            )

        if not index_exists('ai_processed_content', 'idx_ai_content_category'):
            indexes_to_create.append(
                ('ai_processed_content', 'idx_ai_content_category', ['category'])
            )

        if not index_exists('ai_processed_content', 'idx_ai_content_sentiment'):
            indexes_to_create.append(
                ('ai_processed_content', 'idx_ai_content_sentiment', ['sentiment'])
            )

        if not index_exists('ai_processed_content', 'idx_ai_content_created'):
            indexes_to_create.append(
                ('ai_processed_content', 'idx_ai_content_created', ['created_at'])
            )

        # ==================== NotionPage Indexes ====================
        if not index_exists('notion_page', 'idx_notion_page_ai_content_id'):
            indexes_to_create.append(
                ('notion_page', 'idx_notion_page_ai_content_id', ['ai_content_id'])
            )

        if not index_exists('notion_page', 'idx_notion_page_database_id'):
            indexes_to_create.append(
                ('notion_page', 'idx_notion_page_database_id', ['database_id'])
            )

        if not index_exists('notion_page', 'idx_notion_page_created'):
            indexes_to_create.append(
                ('notion_page', 'idx_notion_page_created', ['created_at'])
            )

        # ==================== Backup Indexes ====================
        if not index_exists('backup', 'idx_backup_type'):
            indexes_to_create.append(
                ('backup', 'idx_backup_type', ['type'])
            )

        if not index_exists('backup', 'idx_backup_created'):
            indexes_to_create.append(
                ('backup', 'idx_backup_created', ['created_at'])
            )

        # ==================== Create Indexes ====================
        if not indexes_to_create:
            logger.info("All indexes already exist. No changes needed.")
            return

        logger.info(f"Creating {len(indexes_to_create)} indexes...")

        with db.session.begin():
            for table_name, index_name, columns in indexes_to_create:
                try:
                    # Create index using raw SQL for compatibility
                    columns_str = ', '.join(columns)
                    sql = f"CREATE INDEX {index_name} ON {table_name} ({columns_str})"

                    logger.info(f"Creating index: {index_name} on {table_name}({columns_str})")
                    db.session.execute(text(sql))

                except Exception as e:
                    logger.error(f"Failed to create index {index_name}: {e}")
                    raise

        logger.info("✓ All indexes created successfully")

        # Display index statistics
        display_index_stats()


def display_index_stats():
    """Display index statistics for verification"""
    app = create_app('production')

    with app.app_context():
        engine = db.engine
        inspector = db.inspect(engine)

        logger.info("\n=== Index Statistics ===")

        tables = ['import_task', 'link', 'parsed_content', 'ai_processed_content', 'notion_page', 'backup']

        for table_name in tables:
            try:
                indexes = inspector.get_indexes(table_name)
                logger.info(f"\n{table_name}: {len(indexes)} indexes")
                for idx in indexes:
                    columns = ', '.join(idx['column_names'])
                    logger.info(f"  - {idx['name']}: ({columns})")
            except Exception as e:
                logger.warning(f"Could not get indexes for {table_name}: {e}")


def analyze_query_performance():
    """
    Analyze query performance with EXPLAIN

    Run common queries and display execution plans
    """
    app = create_app('production')

    with app.app_context():
        logger.info("\n=== Query Performance Analysis ===")

        # Common queries to analyze
        queries = [
            ("Get links by task", "SELECT * FROM link WHERE task_id = 1 LIMIT 10"),
            ("Get links by status", "SELECT * FROM link WHERE validation_status = 'valid' LIMIT 10"),
            ("Get recent links", "SELECT * FROM link ORDER BY imported_at DESC LIMIT 10"),
            ("Get parsed content", "SELECT * FROM parsed_content WHERE link_id IN (1,2,3)"),
            ("Get AI content by category", "SELECT * FROM ai_processed_content WHERE category = 'Technology' LIMIT 10"),
        ]

        for description, query in queries:
            try:
                logger.info(f"\n{description}:")
                logger.info(f"Query: {query}")

                # Run EXPLAIN (works for SQLite and PostgreSQL)
                explain_query = f"EXPLAIN QUERY PLAN {query}"
                result = db.session.execute(text(explain_query))

                logger.info("Execution plan:")
                for row in result:
                    logger.info(f"  {row}")

            except Exception as e:
                logger.warning(f"Could not analyze query: {e}")


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'analyze':
        # Run query analysis only
        analyze_query_performance()
    else:
        # Create indexes
        add_indexes()

        # Display statistics
        logger.info("\n" + "="*50)
        logger.info("Database optimization complete!")
        logger.info("="*50)

        # Optionally analyze queries
        if '--analyze' in sys.argv:
            analyze_query_performance()
