"""Link import and task management API routes"""
from flask import Blueprint, request, jsonify
from app import db
from app.services.link_import_service import get_link_import_service
from app.services.link_validation_service import get_link_validation_service
from app.services.task_service import get_task_service
from app.models.link import Link, ImportTask
from app.utils.response import success_response, error_response
from app.utils.validators import validate_required, validate_choice
import logging

logger = logging.getLogger(__name__)

link_bp = Blueprint('links', __name__, url_prefix='/links')


# ==================== Link Import Endpoints ====================

@link_bp.route('/import/favorites', methods=['POST'])
def import_from_favorites():
    """
    Import links from browser favorites/bookmarks file

    Request:
        - file_content: Bookmarks file content (string)
        - file_type: File type (html or json)
        - task_id: Optional import task ID
        - task_name: Optional task name (creates new task if provided)
    """
    try:
        data = request.get_json()
        validate_required(data, ['file_content'])

        file_content = data['file_content']
        file_type = data.get('file_type', 'html')
        task_id = data.get('task_id')
        task_name = data.get('task_name')

        # Validate file_type
        validate_choice(file_type, ['html', 'json'], 'file_type')

        # Create task if task_name provided
        if task_name and not task_id:
            task_service = get_task_service()
            task = task_service.create_import_task(task_name)
            task_id = task.id

        # Import favorites
        import_service = get_link_import_service()
        result = import_service.import_from_favorites(
            file_content=file_content,
            file_type=file_type,
            task_id=task_id
        )

        if not result['success']:
            return error_response('IMP_001', result.get('error', 'Import failed'), None, 400)

        # Update task if exists
        if task_id:
            task_service = get_task_service()
            task_service.update_task_status(
                task_id,
                status='completed',
                total_links=result['total'],
                processed_links=result['imported']
            )

        return success_response(
            data={
                'task_id': task_id,
                'total': result['total'],
                'imported': result['imported'],
                'duplicates': result['duplicates'],
                'failed': result['failed']
            },
            message=f"Imported {result['imported']} links from favorites",
            status=201
        )

    except ValueError as e:
        return error_response('VAL_001', str(e), None, 400)
    except Exception as e:
        logger.error(f"Favorites import failed: {e}", exc_info=True)
        return error_response('SYS_001', f"Import failed: {str(e)}", None, 500)


@link_bp.route('/import/manual', methods=['POST'])
def import_manual():
    """
    Import links from manual text input

    Request:
        - text: Text containing URLs
        - task_id: Optional import task ID
        - task_name: Optional task name (creates new task if provided)
    """
    try:
        data = request.get_json()
        validate_required(data, ['text'])

        text = data['text']
        task_id = data.get('task_id')
        task_name = data.get('task_name')

        # Create task if task_name provided
        if task_name and not task_id:
            task_service = get_task_service()
            task = task_service.create_import_task(task_name)
            task_id = task.id

        # Import manually
        import_service = get_link_import_service()
        result = import_service.import_manual(text=text, task_id=task_id)

        if not result['success']:
            return error_response('IMP_001', result.get('error', 'Import failed'), None, 400)

        # Update task if exists
        if task_id:
            task_service = get_task_service()
            task_service.update_task_status(
                task_id,
                status='completed',
                total_links=result['total'],
                processed_links=result['imported']
            )

        return success_response(
            data={
                'task_id': task_id,
                'total': result['total'],
                'imported': result['imported'],
                'duplicates': result['duplicates']
            },
            message=f"Imported {result['imported']} links manually",
            status=201
        )

    except ValueError as e:
        return error_response('VAL_001', str(e), None, 400)
    except Exception as e:
        logger.error(f"Manual import failed: {e}", exc_info=True)
        return error_response('SYS_001', f"Import failed: {str(e)}", None, 500)


# ==================== Link Management Endpoints ====================

@link_bp.route('', methods=['GET'])
def get_links():
    """
    Get all links with optional filtering

    Query Parameters:
        - source: Filter by source (favorites/manual/history)
        - is_valid: Filter by validation status (true/false)
        - task_id: Filter by task ID
        - limit: Limit number of results
        - offset: Offset for pagination
    """
    try:
        source = request.args.get('source')
        is_valid = request.args.get('is_valid')
        task_id = request.args.get('task_id', type=int)
        limit = request.args.get('limit', type=int, default=100)
        offset = request.args.get('offset', type=int, default=0)

        query = db.session.query(Link)

        if source:
            query = query.filter_by(source=source)

        if is_valid is not None:
            is_valid_bool = is_valid.lower() == 'true'
            query = query.filter_by(is_valid=is_valid_bool)

        if task_id:
            query = query.filter_by(task_id=task_id)

        total = query.count()
        links = query.order_by(Link.imported_at.desc()).offset(offset).limit(limit).all()

        return success_response(
            data={
                'total': total,
                'limit': limit,
                'offset': offset,
                'links': [
                    {
                        'id': link.id,
                        'title': link.title,
                        'url': link.url,
                        'source': link.source,
                        'is_valid': link.is_valid,
                        'validation_status': link.validation_status,
                        'priority': link.priority,
                        'tags': link.tags,
                        'imported_at': link.imported_at.isoformat() if link.imported_at else None,
                        'task_id': link.task_id
                    }
                    for link in links
                ]
            }
        )

    except Exception as e:
        logger.error(f"Failed to get links: {e}", exc_info=True)
        return error_response(f"Failed to retrieve links: {str(e)}", 'SYS_001'), 500


@link_bp.route('/<int:link_id>', methods=['GET'])
def get_link(link_id):
    """
    Get a specific link by ID
    """
    try:
        link = db.session.query(Link).get(link_id)
        if not link:
            return error_response(f"Link {link_id} not found", 'RES_001'), 404

        return success_response(
            data={
                'id': link.id,
                'title': link.title,
                'url': link.url,
                'source': link.source,
                'is_valid': link.is_valid,
                'validation_status': link.validation_status,
                'validation_time': link.validation_time.isoformat() if link.validation_time else None,
                'priority': link.priority,
                'tags': link.tags,
                'notes': link.notes,
                'imported_at': link.imported_at.isoformat() if link.imported_at else None,
                'task_id': link.task_id
            }
        )

    except Exception as e:
        logger.error(f"Failed to get link {link_id}: {e}", exc_info=True)
        return error_response(f"Failed to retrieve link: {str(e)}", 'SYS_001'), 500


@link_bp.route('/<int:link_id>', methods=['PUT'])
def update_link(link_id):
    """
    Update a link

    Request:
        - title: Link title (optional)
        - priority: Link priority (optional)
        - tags: Link tags (optional)
        - notes: Link notes (optional)
    """
    try:
        link = db.session.query(Link).get(link_id)
        if not link:
            return error_response(f"Link {link_id} not found", 'RES_001'), 404

        data = request.get_json()

        if 'title' in data:
            link.title = data['title']
        if 'priority' in data:
            validate_choice(data['priority'], ['low', 'medium', 'high'], 'priority')
            link.priority = data['priority']
        if 'tags' in data:
            link.tags = data['tags']
        if 'notes' in data:
            link.notes = data['notes']

        from app import db
        db.session.commit()

        return success_response(
            data={'id': link.id},
            message="Link updated successfully"
        )

    except ValueError as e:
        return error_response(str(e), 'VAL_001'), 400
    except Exception as e:
        from app import db
        db.session.rollback()
        logger.error(f"Failed to update link {link_id}: {e}", exc_info=True)
        return error_response(f"Failed to update link: {str(e)}", 'SYS_001'), 500


@link_bp.route('/<int:link_id>', methods=['DELETE'])
def delete_link(link_id):
    """
    Delete a link
    """
    try:
        link = db.session.query(Link).get(link_id)
        if not link:
            return error_response(f"Link {link_id} not found", 'RES_001'), 404

        from app import db
        db.session.delete(link)
        db.session.commit()

        return success_response(
            message="Link deleted successfully"
        )

    except Exception as e:
        from app import db
        db.session.rollback()
        logger.error(f"Failed to delete link {link_id}: {e}", exc_info=True)
        return error_response(f"Failed to delete link: {str(e)}", 'SYS_001'), 500


@link_bp.route('/batch', methods=['DELETE'])
def batch_delete_links():
    """
    Batch delete links

    Request:
        - link_ids: Array of link IDs to delete
    """
    try:
        data = request.get_json()
        validate_required(data, ['link_ids'])

        link_ids = data['link_ids']
        if not isinstance(link_ids, list):
            return error_response("link_ids must be an array", 'VAL_001'), 400

        deleted_count = db.session.query(Link).filter(Link.id.in_(link_ids)).delete(synchronize_session=False)

        from app import db
        db.session.commit()

        return success_response(
            data={'deleted': deleted_count},
            message=f"Deleted {deleted_count} links"
        )

    except ValueError as e:
        return error_response(str(e), 'VAL_001'), 400
    except Exception as e:
        from app import db
        db.session.rollback()
        logger.error(f"Batch delete failed: {e}", exc_info=True)
        return error_response(f"Batch delete failed: {str(e)}", 'SYS_001'), 500


# ==================== Link Validation Endpoints ====================

@link_bp.route('/validate', methods=['POST'])
def validate_links():
    """
    Validate links in batch

    Request:
        - link_ids: Array of link IDs to validate
    """
    try:
        data = request.get_json()
        validate_required(data, ['link_ids'])

        link_ids = data['link_ids']
        if not isinstance(link_ids, list):
            return error_response("link_ids must be an array", 'VAL_001'), 400

        validation_service = get_link_validation_service()
        result = validation_service.validate_batch(link_ids, update_db=True)

        return success_response(
            data=result,
            message=f"Validated {result['total']} links"
        )

    except ValueError as e:
        return error_response(str(e), 'VAL_001'), 400
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=True)
        return error_response(f"Validation failed: {str(e)}", 'SYS_001'), 500


@link_bp.route('/validate/pending', methods=['POST'])
def validate_pending_links():
    """
    Validate all pending links

    Request:
        - limit: Optional limit on number of links to validate
    """
    try:
        data = request.get_json() or {}
        limit = data.get('limit')

        validation_service = get_link_validation_service()
        result = validation_service.validate_all_pending(limit=limit)

        return success_response(
            data=result,
            message=result.get('message', 'Validation completed')
        )

    except Exception as e:
        logger.error(f"Pending validation failed: {e}", exc_info=True)
        return error_response(f"Validation failed: {str(e)}", 'SYS_001'), 500


@link_bp.route('/statistics', methods=['GET'])
def get_link_statistics():
    """
    Get link import and validation statistics
    """
    try:
        import_service = get_link_import_service()
        validation_service = get_link_validation_service()

        import_stats = import_service.get_import_statistics()
        validation_stats = validation_service.get_validation_statistics()

        return success_response(
            data={
                'import': import_stats,
                'validation': validation_stats
            }
        )

    except Exception as e:
        logger.error(f"Failed to get statistics: {e}", exc_info=True)
        return error_response(f"Failed to retrieve statistics: {str(e)}", 'SYS_001'), 500


# ==================== Task Management Endpoints ====================

task_bp = Blueprint('tasks', __name__, url_prefix='/tasks')


@task_bp.route('/import', methods=['GET'])
def get_import_tasks():
    """
    Get all import tasks

    Query Parameters:
        - status: Filter by status (pending/running/completed/failed)
        - limit: Limit number of results
    """
    try:
        status = request.args.get('status')
        limit = request.args.get('limit', type=int)

        if status:
            validate_choice(status, ['pending', 'running', 'completed', 'failed'], 'status')

        task_service = get_task_service()
        tasks = task_service.get_all_tasks(status=status, limit=limit)

        return success_response(
            data={
                'total': len(tasks),
                'tasks': [
                    {
                        'id': task.id,
                        'name': task.name,
                        'status': task.status,
                        'total_links': task.total_links,
                        'processed_links': task.processed_links,
                        'config': task.config,
                        'created_at': task.created_at.isoformat() if task.created_at else None,
                        'started_at': task.started_at.isoformat() if task.started_at else None,
                        'completed_at': task.completed_at.isoformat() if task.completed_at else None
                    }
                    for task in tasks
                ]
            }
        )

    except ValueError as e:
        return error_response(str(e), 'VAL_001'), 400
    except Exception as e:
        logger.error(f"Failed to get tasks: {e}", exc_info=True)
        return error_response(f"Failed to retrieve tasks: {str(e)}", 'SYS_001'), 500


@task_bp.route('/import', methods=['POST'])
def create_import_task():
    """
    Create a new import task

    Request:
        - name: Task name
        - config: Task configuration (optional)
    """
    try:
        data = request.get_json()
        validate_required(data, ['name'])

        name = data['name']
        config = data.get('config', {})

        task_service = get_task_service()
        task = task_service.create_import_task(name=name, config=config)

        return success_response(
            data={
                'id': task.id,
                'name': task.name,
                'status': task.status,
                'created_at': task.created_at.isoformat()
            },
            message="Import task created successfully",
            status=201
        )

    except ValueError as e:
        return error_response(str(e), 'VAL_001'), 400
    except Exception as e:
        logger.error(f"Failed to create task: {e}", exc_info=True)
        return error_response(f"Failed to create task: {str(e)}", 'SYS_001'), 500


@task_bp.route('/import/<int:task_id>', methods=['GET'])
def get_import_task(task_id):
    """
    Get import task details with statistics
    """
    try:
        task_service = get_task_service()
        task_summary = task_service.get_task_summary(task_id)

        if not task_summary:
            return error_response(f"Task {task_id} not found", 'RES_001'), 404

        return success_response(data=task_summary)

    except Exception as e:
        logger.error(f"Failed to get task {task_id}: {e}", exc_info=True)
        return error_response(f"Failed to retrieve task: {str(e)}", 'SYS_001'), 500


@task_bp.route('/import/<int:task_id>', methods=['DELETE'])
def delete_import_task(task_id):
    """
    Delete an import task

    Query Parameters:
        - delete_links: Whether to delete associated links (default: false)
    """
    try:
        delete_links = request.args.get('delete_links', 'false').lower() == 'true'

        task_service = get_task_service()
        success = task_service.delete_task(task_id, delete_links=delete_links)

        if not success:
            return error_response(f"Task {task_id} not found", 'RES_001'), 404

        return success_response(
            message="Task deleted successfully"
        )

    except Exception as e:
        logger.error(f"Failed to delete task {task_id}: {e}", exc_info=True)
        return error_response(f"Failed to delete task: {str(e)}", 'SYS_001'), 500


@task_bp.route('/import/<int:task_id>/start', methods=['POST'])
def start_import_task(task_id):
    """
    Start a pending import task
    """
    try:
        task_service = get_task_service()
        task = task_service.start_task(task_id)

        if not task:
            return error_response(f"Task {task_id} not found", 'RES_001'), 404

        return success_response(
            data={'id': task.id, 'status': task.status},
            message="Task started successfully"
        )

    except ValueError as e:
        return error_response(str(e), 'VAL_001'), 400
    except Exception as e:
        logger.error(f"Failed to start task {task_id}: {e}", exc_info=True)
        return error_response(f"Failed to start task: {str(e)}", 'SYS_001'), 500


@task_bp.route('/statistics', methods=['GET'])
def get_task_statistics():
    """
    Get task statistics
    """
    try:
        task_service = get_task_service()
        stats = task_service.get_task_statistics()

        return success_response(data=stats)

    except Exception as e:
        logger.error(f"Failed to get task statistics: {e}", exc_info=True)
        return error_response(f"Failed to retrieve statistics: {str(e)}", 'SYS_001'), 500
