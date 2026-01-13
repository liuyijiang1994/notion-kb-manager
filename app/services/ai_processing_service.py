"""AI processing service for content summarization and enhancement"""
import logging
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.models.content import ParsedContent, AIProcessedContent
from app.models.configuration import ModelConfiguration
from app.services.model_service import get_model_service
from app.services.config_service import ConfigurationService
from app import db

logger = logging.getLogger(__name__)


class AIProcessingService:
    """Service for AI-powered content processing"""

    def __init__(self):
        self.model_service = get_model_service()
        self.config_service = ConfigurationService()

    def process_content(self, parsed_content_id: int,
                       model_id: Optional[int] = None,
                       processing_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process parsed content with AI

        Args:
            parsed_content_id: ParsedContent ID to process
            model_id: Optional specific model ID (uses default if not provided)
            processing_config: Processing configuration options

        Returns:
            Dict with processing result
        """
        try:
            # Get parsed content
            parsed_content = db.session.query(ParsedContent).get(parsed_content_id)
            if not parsed_content:
                return {
                    'success': False,
                    'error': f'Parsed content {parsed_content_id} not found'
                }

            # Get model configuration
            if model_id:
                model = self.config_service.get_model_config(model_id, decrypt_token=True)
            else:
                model = self.config_service.get_default_model(decrypt_token=True)

            if not model:
                return {
                    'success': False,
                    'error': 'No AI model configured'
                }

            # Prepare processing config
            config = processing_config or {}
            generate_summary = config.get('generate_summary', True)
            generate_keywords = config.get('generate_keywords', True)
            generate_insights = config.get('generate_insights', False)

            result = {
                'success': True,
                'summary': None,
                'keywords': None,
                'insights': None,
                'tokens_used': 0,
                'cost': 0.0
            }

            # Generate summary
            if generate_summary:
                summary_result = self._generate_summary(
                    parsed_content.formatted_content,
                    model
                )
                if summary_result['success']:
                    result['summary'] = summary_result['summary']
                    result['tokens_used'] += summary_result.get('tokens_used', 0)

            # Generate keywords
            if generate_keywords:
                keywords_result = self._extract_keywords(
                    parsed_content.formatted_content,
                    model
                )
                if keywords_result['success']:
                    result['keywords'] = keywords_result['keywords']
                    result['tokens_used'] += keywords_result.get('tokens_used', 0)

            # Generate insights
            if generate_insights:
                insights_result = self._generate_insights(
                    parsed_content.formatted_content,
                    model
                )
                if insights_result['success']:
                    result['insights'] = insights_result['insights']
                    result['tokens_used'] += insights_result.get('tokens_used', 0)

            # Save to database
            ai_content = self._save_ai_processed_content(
                parsed_content_id=parsed_content_id,
                model_id=model.id,
                summary=result['summary'],
                keywords=result['keywords'],
                insights=result['insights'],
                tokens_used=result['tokens_used'],
                processing_config=config
            )

            result['ai_content_id'] = ai_content.id
            logger.info(f"Successfully processed content {parsed_content_id} with AI")

            return result

        except Exception as e:
            logger.error(f"Failed to process content {parsed_content_id}: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_summary(self, content: str, model: ModelConfiguration) -> Dict[str, Any]:
        """
        Generate summary of content using AI

        Args:
            content: Content to summarize
            model: Model configuration

        Returns:
            Dict with summary result
        """
        try:
            # Truncate content if too long (keep first 4000 words)
            words = content.split()
            if len(words) > 4000:
                content = ' '.join(words[:4000]) + '...'

            prompt = f"""Please provide a concise summary of the following content in 2-3 paragraphs:

{content}

Summary:"""

            messages = [
                {"role": "user", "content": prompt}
            ]

            response = self.model_service.chat_completion(
                api_url=model.api_url,
                api_token=model.api_token,
                model_name=model.name,
                messages=messages,
                max_tokens=500,
                temperature=0.7,
                timeout=model.timeout
            )

            if response and 'choices' in response:
                summary = response['choices'][0]['message']['content'].strip()
                tokens_used = response.get('usage', {}).get('total_tokens', 0)

                return {
                    'success': True,
                    'summary': summary,
                    'tokens_used': tokens_used
                }

            return {
                'success': False,
                'error': 'No valid response from AI model'
            }

        except Exception as e:
            logger.error(f"Failed to generate summary: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _extract_keywords(self, content: str, model: ModelConfiguration) -> Dict[str, Any]:
        """
        Extract keywords from content using AI

        Args:
            content: Content to analyze
            model: Model configuration

        Returns:
            Dict with keywords result
        """
        try:
            # Truncate content if too long
            words = content.split()
            if len(words) > 2000:
                content = ' '.join(words[:2000]) + '...'

            prompt = f"""Extract 5-10 key topics or keywords from the following content. Return them as a comma-separated list:

{content}

Keywords:"""

            messages = [
                {"role": "user", "content": prompt}
            ]

            response = self.model_service.chat_completion(
                api_url=model.api_url,
                api_token=model.api_token,
                model_name=model.name,
                messages=messages,
                max_tokens=100,
                temperature=0.5,
                timeout=model.timeout
            )

            if response and 'choices' in response:
                keywords_text = response['choices'][0]['message']['content'].strip()
                # Parse comma-separated keywords
                keywords = [k.strip() for k in keywords_text.split(',')]
                keywords = [k for k in keywords if k]  # Remove empty strings
                tokens_used = response.get('usage', {}).get('total_tokens', 0)

                return {
                    'success': True,
                    'keywords': keywords,
                    'tokens_used': tokens_used
                }

            return {
                'success': False,
                'error': 'No valid response from AI model'
            }

        except Exception as e:
            logger.error(f"Failed to extract keywords: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_insights(self, content: str, model: ModelConfiguration) -> Dict[str, Any]:
        """
        Generate insights from content using AI

        Args:
            content: Content to analyze
            model: Model configuration

        Returns:
            Dict with insights result
        """
        try:
            # Truncate content if too long
            words = content.split()
            if len(words) > 3000:
                content = ' '.join(words[:3000]) + '...'

            prompt = f"""Analyze the following content and provide 3-5 key insights or takeaways:

{content}

Insights:"""

            messages = [
                {"role": "user", "content": prompt}
            ]

            response = self.model_service.chat_completion(
                api_url=model.api_url,
                api_token=model.api_token,
                model_name=model.name,
                messages=messages,
                max_tokens=400,
                temperature=0.7,
                timeout=model.timeout
            )

            if response and 'choices' in response:
                insights = response['choices'][0]['message']['content'].strip()
                tokens_used = response.get('usage', {}).get('total_tokens', 0)

                return {
                    'success': True,
                    'insights': insights,
                    'tokens_used': tokens_used
                }

            return {
                'success': False,
                'error': 'No valid response from AI model'
            }

        except Exception as e:
            logger.error(f"Failed to generate insights: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _save_ai_processed_content(self, parsed_content_id: int, model_id: int,
                                   summary: Optional[str], keywords: Optional[List[str]],
                                   insights: Optional[str], tokens_used: int,
                                   processing_config: Dict[str, Any]) -> AIProcessedContent:
        """
        Save AI processed content to database

        Args:
            parsed_content_id: ParsedContent ID
            model_id: Model ID used for processing
            summary: Generated summary
            keywords: Extracted keywords
            insights: Generated insights
            tokens_used: Total tokens used
            processing_config: Processing configuration

        Returns:
            Created AIProcessedContent object
        """
        # Deactivate previous versions
        db.session.query(AIProcessedContent).filter_by(
            parsed_content_id=parsed_content_id,
            is_active=True
        ).update({'is_active': False})

        # Get current version number
        max_version = db.session.query(
            db.func.max(AIProcessedContent.version)
        ).filter_by(
            parsed_content_id=parsed_content_id
        ).scalar() or 0

        # Create new version
        ai_content = AIProcessedContent(
            parsed_content_id=parsed_content_id,
            model_id=model_id,
            summary=summary,
            keywords=keywords,
            insights=insights,
            processing_config=processing_config,
            version=max_version + 1,
            is_active=True,
            tokens_used=tokens_used,
            cost=0.0,  # Cost calculation can be added later
            processed_at=datetime.utcnow()
        )

        db.session.add(ai_content)
        db.session.commit()

        return ai_content

    def get_ai_content(self, ai_content_id: int) -> Optional[AIProcessedContent]:
        """
        Get AI processed content by ID

        Args:
            ai_content_id: AIProcessedContent ID

        Returns:
            AIProcessedContent object or None
        """
        return db.session.query(AIProcessedContent).get(ai_content_id)

    def get_ai_content_by_parsed_content(self, parsed_content_id: int,
                                        version: Optional[int] = None) -> Optional[AIProcessedContent]:
        """
        Get AI processed content by parsed content ID

        Args:
            parsed_content_id: ParsedContent ID
            version: Specific version (returns active version if not specified)

        Returns:
            AIProcessedContent object or None
        """
        query = db.session.query(AIProcessedContent).filter_by(
            parsed_content_id=parsed_content_id
        )

        if version:
            query = query.filter_by(version=version)
        else:
            query = query.filter_by(is_active=True)

        return query.first()

    def get_all_versions(self, parsed_content_id: int) -> List[AIProcessedContent]:
        """
        Get all versions of AI processed content

        Args:
            parsed_content_id: ParsedContent ID

        Returns:
            List of AIProcessedContent objects
        """
        return db.session.query(AIProcessedContent).filter_by(
            parsed_content_id=parsed_content_id
        ).order_by(AIProcessedContent.version.desc()).all()

    def batch_process(self, parsed_content_ids: List[int],
                     model_id: Optional[int] = None,
                     processing_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process multiple contents in batch

        Args:
            parsed_content_ids: List of ParsedContent IDs
            model_id: Optional model ID
            processing_config: Processing configuration

        Returns:
            Dict with batch results
        """
        results = {
            'success': True,
            'total': len(parsed_content_ids),
            'completed': 0,
            'failed': 0,
            'results': []
        }

        for content_id in parsed_content_ids:
            result = self.process_content(content_id, model_id, processing_config)
            if result['success']:
                results['completed'] += 1
            else:
                results['failed'] += 1
            results['results'].append({
                'parsed_content_id': content_id,
                **result
            })

        return results

    def get_processing_statistics(self) -> Dict[str, Any]:
        """
        Get AI processing statistics

        Returns:
            Dict with statistics
        """
        total = db.session.query(AIProcessedContent).count()
        total_tokens = db.session.query(
            db.func.sum(AIProcessedContent.tokens_used)
        ).scalar() or 0
        total_cost = db.session.query(
            db.func.sum(AIProcessedContent.cost)
        ).scalar() or 0.0

        # Get counts by model
        by_model = db.session.query(
            AIProcessedContent.model_id,
            db.func.count(AIProcessedContent.id)
        ).group_by(AIProcessedContent.model_id).all()

        return {
            'total_processed': total,
            'total_tokens_used': int(total_tokens),
            'total_cost': float(total_cost),
            'by_model': {model_id: count for model_id, count in by_model}
        }


def get_ai_processing_service() -> AIProcessingService:
    """Get singleton instance of AIProcessingService"""
    return AIProcessingService()
