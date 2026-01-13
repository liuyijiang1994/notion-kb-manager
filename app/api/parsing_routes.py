"""Content parsing API routes"""
from flask import Blueprint, request, jsonify
from app.services.content_parsing_service import get_content_parsing_service
from app.models.content import ParsedContent
from app.utils.response import success_response, error_response
from app.utils.validators import validate_required
import logging

logger = logging.getLogger(__name__)

parsing_bp = Blueprint('parsing', __name__, url_prefix='/parsing')


@parsing_bp.route('/parse/<int:link_id>', methods=['POST'])
def parse_link(link_id):
    """
    Parse content from a specific link

    Path Parameters:
        link_id: Link ID to parse

    Returns:
        Parsed content result
    """
    try:
        parsing_service = get_content_parsing_service()
        result = parsing_service.fetch_and_parse(link_id)

        if not result['success']:
            return error_response('PARSE_001', result.get('error', 'Parsing failed'), None, 400)

        return success_response(
            data=result,
            message=f"Successfully parsed link {link_id}",
            status=201
        )

    except Exception as e:
        logger.error(f"Failed to parse link {link_id}: {e}", exc_info=True)
        return error_response('SYS_001', f"Parsing failed: {str(e)}", None, 500)


@parsing_bp.route('/parse/batch', methods=['POST'])
def parse_batch():
    """
    Parse multiple links in batch

    Request:
        - link_ids: Array of link IDs to parse
    """
    try:
        data = request.get_json()
        validate_required(data, ['link_ids'])

        link_ids = data['link_ids']
        if not isinstance(link_ids, list):
            return error_response('VAL_001', "link_ids must be an array", None, 400)

        parsing_service = get_content_parsing_service()
        result = parsing_service.parse_batch(link_ids)

        return success_response(
            data=result,
            message=f"Batch parsing completed: {result['completed']}/{result['total']} successful",
            status=201
        )

    except ValueError as e:
        return error_response('VAL_001', str(e), None, 400)
    except Exception as e:
        logger.error(f"Batch parsing failed: {e}", exc_info=True)
        return error_response('SYS_001', f"Batch parsing failed: {str(e)}", None, 500)


@parsing_bp.route('/content/<int:content_id>', methods=['GET'])
def get_parsed_content(content_id):
    """
    Get parsed content by ID

    Path Parameters:
        content_id: ParsedContent ID
    """
    try:
        parsing_service = get_content_parsing_service()
        content = parsing_service.get_parsed_content(content_id)

        if not content:
            return error_response('RES_001', f"Parsed content {content_id} not found", None, 404)

        return success_response(
            data={
                'id': content.id,
                'link_id': content.link_id,
                'formatted_content': content.formatted_content,
                'quality_score': content.quality_score,
                'parsing_method': content.parsing_method,
                'images': content.images,
                'tables': content.tables,
                'paper_info': content.paper_info,
                'status': content.status,
                'parsed_at': content.parsed_at.isoformat() if content.parsed_at else None
            }
        )

    except Exception as e:
        logger.error(f"Failed to get parsed content {content_id}: {e}", exc_info=True)
        return error_response('SYS_001', f"Failed to retrieve content: {str(e)}", None, 500)


@parsing_bp.route('/content/by-link/<int:link_id>', methods=['GET'])
def get_parsed_content_by_link(link_id):
    """
    Get parsed content by link ID

    Path Parameters:
        link_id: Link ID
    """
    try:
        parsing_service = get_content_parsing_service()
        content = parsing_service.get_parsed_content_by_link(link_id)

        if not content:
            return error_response('RES_001', f"No parsed content found for link {link_id}", None, 404)

        return success_response(
            data={
                'id': content.id,
                'link_id': content.link_id,
                'formatted_content': content.formatted_content,
                'quality_score': content.quality_score,
                'parsing_method': content.parsing_method,
                'images': content.images,
                'tables': content.tables,
                'paper_info': content.paper_info,
                'status': content.status,
                'parsed_at': content.parsed_at.isoformat() if content.parsed_at else None
            }
        )

    except Exception as e:
        logger.error(f"Failed to get parsed content for link {link_id}: {e}", exc_info=True)
        return error_response('SYS_001', f"Failed to retrieve content: {str(e)}", None, 500)


@parsing_bp.route('/content/<int:content_id>', methods=['PUT'])
def update_parsed_content(content_id):
    """
    Update parsed content manually

    Request:
        - formatted_content: Updated markdown content (optional)
        - quality_score: Updated quality score (optional)
    """
    try:
        parsing_service = get_content_parsing_service()
        content = parsing_service.get_parsed_content(content_id)

        if not content:
            return error_response('RES_001', f"Parsed content {content_id} not found", None, 404)

        data = request.get_json()

        if 'formatted_content' in data:
            content.formatted_content = data['formatted_content']

        if 'quality_score' in data:
            score = data['quality_score']
            if not isinstance(score, int) or score < 0 or score > 100:
                return error_response('VAL_001', "quality_score must be between 0 and 100", None, 400)
            content.quality_score = score

        from app import db
        db.session.commit()

        return success_response(
            data={'id': content.id},
            message="Parsed content updated successfully"
        )

    except Exception as e:
        from app import db
        db.session.rollback()
        logger.error(f"Failed to update parsed content {content_id}: {e}", exc_info=True)
        return error_response('SYS_001', f"Failed to update content: {str(e)}", None, 500)


@parsing_bp.route('/content/<int:content_id>', methods=['DELETE'])
def delete_parsed_content(content_id):
    """
    Delete parsed content

    Path Parameters:
        content_id: ParsedContent ID
    """
    try:
        from app import db
        content = db.session.query(ParsedContent).get(content_id)
        if not content:
            return error_response('RES_001', f"Parsed content {content_id} not found", None, 404)

        db.session.delete(content)
        db.session.commit()

        return success_response(
            message="Parsed content deleted successfully"
        )

    except Exception as e:
        from app import db
        db.session.rollback()
        logger.error(f"Failed to delete parsed content {content_id}: {e}", exc_info=True)
        return error_response('SYS_001', f"Failed to delete content: {str(e)}", None, 500)


@parsing_bp.route('/statistics', methods=['GET'])
def get_parsing_statistics():
    """
    Get parsing statistics
    """
    try:
        parsing_service = get_content_parsing_service()
        stats = parsing_service.get_parsing_statistics()

        return success_response(data=stats)

    except Exception as e:
        logger.error(f"Failed to get parsing statistics: {e}", exc_info=True)
        return error_response('SYS_001', f"Failed to retrieve statistics: {str(e)}", None, 500)
