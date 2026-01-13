"""AI processing and Notion import API routes"""
from flask import Blueprint, request
from app.services.ai_processing_service import get_ai_processing_service
from app.services.notion_import_service import get_notion_import_service
from app.utils.response import success_response, error_response
from app.utils.validators import validate_required
import logging

logger = logging.getLogger(__name__)

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')
notion_import_bp = Blueprint('notion_import', __name__, url_prefix='/notion-import')


# ==================== AI Processing Endpoints ====================

@ai_bp.route('/process/<int:parsed_content_id>', methods=['POST'])
def process_content(parsed_content_id):
    """
    Process parsed content with AI

    Path Parameters:
        parsed_content_id: ParsedContent ID to process

    Request Body (optional):
        - model_id: Specific model ID to use
        - config: Processing configuration options
    """
    try:
        data = request.get_json() or {}
        model_id = data.get('model_id')
        processing_config = data.get('config', {})

        ai_service = get_ai_processing_service()
        result = ai_service.process_content(
            parsed_content_id=parsed_content_id,
            model_id=model_id,
            processing_config=processing_config
        )

        if not result['success']:
            return error_response('AI_001', result.get('error', 'Processing failed'), None, 400)

        return success_response(
            data=result,
            message=f"Successfully processed content {parsed_content_id}",
            status=201
        )

    except Exception as e:
        logger.error(f"Failed to process content {parsed_content_id}: {e}", exc_info=True)
        return error_response('SYS_001', f"Processing failed: {str(e)}", None, 500)


@ai_bp.route('/process/batch', methods=['POST'])
def process_batch():
    """
    Process multiple contents in batch

    Request Body:
        - parsed_content_ids: Array of ParsedContent IDs
        - model_id: Optional model ID
        - config: Optional processing configuration
    """
    try:
        data = request.get_json()
        validate_required(data, ['parsed_content_ids'])

        parsed_content_ids = data['parsed_content_ids']
        if not isinstance(parsed_content_ids, list):
            return error_response('VAL_001', "parsed_content_ids must be an array", None, 400)

        model_id = data.get('model_id')
        processing_config = data.get('config', {})

        ai_service = get_ai_processing_service()
        result = ai_service.batch_process(
            parsed_content_ids=parsed_content_ids,
            model_id=model_id,
            processing_config=processing_config
        )

        return success_response(
            data=result,
            message=f"Batch processing completed: {result['completed']}/{result['total']} successful",
            status=201
        )

    except ValueError as e:
        return error_response('VAL_001', str(e), None, 400)
    except Exception as e:
        logger.error(f"Batch processing failed: {e}", exc_info=True)
        return error_response('SYS_001', f"Batch processing failed: {str(e)}", None, 500)


@ai_bp.route('/content/<int:ai_content_id>', methods=['GET'])
def get_ai_content(ai_content_id):
    """
    Get AI processed content by ID

    Path Parameters:
        ai_content_id: AIProcessedContent ID
    """
    try:
        ai_service = get_ai_processing_service()
        content = ai_service.get_ai_content(ai_content_id)

        if not content:
            return error_response('RES_001', f"AI content {ai_content_id} not found", None, 404)

        return success_response(
            data={
                'id': content.id,
                'parsed_content_id': content.parsed_content_id,
                'model_id': content.model_id,
                'summary': content.summary,
                'keywords': content.keywords,
                'insights': content.insights,
                'version': content.version,
                'is_active': content.is_active,
                'tokens_used': content.tokens_used,
                'cost': float(content.cost) if content.cost else 0.0,
                'processed_at': content.processed_at.isoformat() if content.processed_at else None
            }
        )

    except Exception as e:
        logger.error(f"Failed to get AI content {ai_content_id}: {e}", exc_info=True)
        return error_response('SYS_001', f"Failed to retrieve content: {str(e)}", None, 500)


@ai_bp.route('/content/by-parsed/<int:parsed_content_id>', methods=['GET'])
def get_ai_content_by_parsed(parsed_content_id):
    """
    Get AI content by parsed content ID

    Path Parameters:
        parsed_content_id: ParsedContent ID

    Query Parameters:
        version: Optional specific version number
    """
    try:
        version = request.args.get('version', type=int)

        ai_service = get_ai_processing_service()
        content = ai_service.get_ai_content_by_parsed_content(
            parsed_content_id=parsed_content_id,
            version=version
        )

        if not content:
            return error_response('RES_001', f"No AI content found for parsed content {parsed_content_id}", None, 404)

        return success_response(
            data={
                'id': content.id,
                'parsed_content_id': content.parsed_content_id,
                'model_id': content.model_id,
                'summary': content.summary,
                'keywords': content.keywords,
                'insights': content.insights,
                'version': content.version,
                'is_active': content.is_active,
                'tokens_used': content.tokens_used,
                'cost': float(content.cost) if content.cost else 0.0,
                'processed_at': content.processed_at.isoformat() if content.processed_at else None
            }
        )

    except Exception as e:
        logger.error(f"Failed to get AI content for parsed content {parsed_content_id}: {e}", exc_info=True)
        return error_response('SYS_001', f"Failed to retrieve content: {str(e)}", None, 500)


@ai_bp.route('/versions/<int:parsed_content_id>', methods=['GET'])
def get_all_versions(parsed_content_id):
    """
    Get all AI processing versions for a parsed content

    Path Parameters:
        parsed_content_id: ParsedContent ID
    """
    try:
        ai_service = get_ai_processing_service()
        versions = ai_service.get_all_versions(parsed_content_id)

        return success_response(
            data={
                'total': len(versions),
                'versions': [
                    {
                        'id': v.id,
                        'version': v.version,
                        'is_active': v.is_active,
                        'model_id': v.model_id,
                        'tokens_used': v.tokens_used,
                        'processed_at': v.processed_at.isoformat() if v.processed_at else None
                    }
                    for v in versions
                ]
            }
        )

    except Exception as e:
        logger.error(f"Failed to get versions for parsed content {parsed_content_id}: {e}", exc_info=True)
        return error_response('SYS_001', f"Failed to retrieve versions: {str(e)}", None, 500)


@ai_bp.route('/statistics', methods=['GET'])
def get_ai_statistics():
    """
    Get AI processing statistics
    """
    try:
        ai_service = get_ai_processing_service()
        stats = ai_service.get_processing_statistics()

        return success_response(data=stats)

    except Exception as e:
        logger.error(f"Failed to get AI statistics: {e}", exc_info=True)
        return error_response('SYS_001', f"Failed to retrieve statistics: {str(e)}", None, 500)


# ==================== Notion Import Endpoints ====================

@notion_import_bp.route('/<int:ai_content_id>', methods=['POST'])
def import_to_notion(ai_content_id):
    """
    Import AI processed content into Notion

    Path Parameters:
        ai_content_id: AIProcessedContent ID to import

    Request Body:
        - database_id: Target Notion database ID
        - properties: Optional additional properties
    """
    try:
        data = request.get_json()
        validate_required(data, ['database_id'])

        database_id = data['database_id']
        properties = data.get('properties', {})

        import_service = get_notion_import_service()
        result = import_service.import_to_notion(
            ai_content_id=ai_content_id,
            database_id=database_id,
            properties=properties
        )

        if not result['success']:
            return error_response('NOTION_001', result.get('error', 'Import failed'), None, 400)

        return success_response(
            data=result,
            message=f"Successfully imported AI content {ai_content_id} into Notion",
            status=201
        )

    except ValueError as e:
        return error_response('VAL_001', str(e), None, 400)
    except Exception as e:
        logger.error(f"Failed to import AI content {ai_content_id}: {e}", exc_info=True)
        return error_response('SYS_001', f"Import failed: {str(e)}", None, 500)


@notion_import_bp.route('/batch', methods=['POST'])
def batch_import_to_notion():
    """
    Import multiple AI contents into Notion in batch

    Request Body:
        - ai_content_ids: Array of AIProcessedContent IDs
        - database_id: Target Notion database ID
    """
    try:
        data = request.get_json()
        validate_required(data, ['ai_content_ids', 'database_id'])

        ai_content_ids = data['ai_content_ids']
        if not isinstance(ai_content_ids, list):
            return error_response('VAL_001', "ai_content_ids must be an array", None, 400)

        database_id = data['database_id']

        import_service = get_notion_import_service()
        result = import_service.batch_import(
            ai_content_ids=ai_content_ids,
            database_id=database_id
        )

        return success_response(
            data=result,
            message=f"Batch import completed: {result['completed']}/{result['total']} successful",
            status=201
        )

    except ValueError as e:
        return error_response('VAL_001', str(e), None, 400)
    except Exception as e:
        logger.error(f"Batch import failed: {e}", exc_info=True)
        return error_response('SYS_001', f"Batch import failed: {str(e)}", None, 500)


@notion_import_bp.route('/import/<int:import_id>', methods=['GET'])
def get_notion_import(import_id):
    """
    Get Notion import record by ID

    Path Parameters:
        import_id: NotionImport ID
    """
    try:
        import_service = get_notion_import_service()
        notion_import = import_service.get_notion_import(import_id)

        if not notion_import:
            return error_response('RES_001', f"Notion import {import_id} not found", None, 404)

        return success_response(
            data={
                'id': notion_import.id,
                'ai_content_id': notion_import.ai_content_id,
                'notion_page_id': notion_import.notion_page_id,
                'notion_url': notion_import.notion_url,
                'status': notion_import.status,
                'error_message': notion_import.error_message,
                'imported_at': notion_import.imported_at.isoformat() if notion_import.imported_at else None
            }
        )

    except Exception as e:
        logger.error(f"Failed to get Notion import {import_id}: {e}", exc_info=True)
        return error_response('SYS_001', f"Failed to retrieve import: {str(e)}", None, 500)


@notion_import_bp.route('/by-ai-content/<int:ai_content_id>', methods=['GET'])
def get_imports_by_ai_content(ai_content_id):
    """
    Get all Notion imports for an AI content

    Path Parameters:
        ai_content_id: AIProcessedContent ID
    """
    try:
        import_service = get_notion_import_service()
        imports = import_service.get_imports_by_ai_content(ai_content_id)

        return success_response(
            data={
                'total': len(imports),
                'imports': [
                    {
                        'id': imp.id,
                        'notion_page_id': imp.notion_page_id,
                        'notion_url': imp.notion_url,
                        'status': imp.status,
                        'imported_at': imp.imported_at.isoformat() if imp.imported_at else None
                    }
                    for imp in imports
                ]
            }
        )

    except Exception as e:
        logger.error(f"Failed to get imports for AI content {ai_content_id}: {e}", exc_info=True)
        return error_response('SYS_001', f"Failed to retrieve imports: {str(e)}", None, 500)


@notion_import_bp.route('/statistics', methods=['GET'])
def get_import_statistics():
    """
    Get Notion import statistics
    """
    try:
        import_service = get_notion_import_service()
        stats = import_service.get_import_statistics()

        return success_response(data=stats)

    except Exception as e:
        logger.error(f"Failed to get import statistics: {e}", exc_info=True)
        return error_response('SYS_001', f"Failed to retrieve statistics: {str(e)}", None, 500)
