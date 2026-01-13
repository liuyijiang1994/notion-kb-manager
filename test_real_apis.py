#!/usr/bin/env python3
"""
Test script for real API connections
Tests VolcEngine LLM and Notion API with real credentials

IMPORTANT: Set these environment variables before running:
- VOLCENGINE_API_TOKEN
- VOLCENGINE_MODEL_NAME (optional, defaults to doubao-seed-1-6-251015)
- NOTION_API_TOKEN
"""
import os
from app import create_app, db
from app.services.config_service import ConfigurationService
from app.services.model_service import get_model_service
from app.services.notion_service import get_notion_service

# Get credentials from environment variables
VOLCENGINE_CONFIG = {
    'name': os.getenv('VOLCENGINE_MODEL_NAME', 'doubao-seed-1-6-251015'),
    'api_url': os.getenv('VOLCENGINE_API_URL', 'https://ark.cn-beijing.volces.com/api/v3/'),
    'api_token': os.getenv('VOLCENGINE_API_TOKEN'),
    'max_tokens': int(os.getenv('VOLCENGINE_MAX_TOKENS', '4096')),
    'timeout': 30,
    'rate_limit': 60
}

NOTION_TOKEN = os.getenv('NOTION_API_TOKEN')


def check_credentials():
    """Check if required credentials are set"""
    missing = []

    if not VOLCENGINE_CONFIG['api_token']:
        missing.append('VOLCENGINE_API_TOKEN')

    if not NOTION_TOKEN:
        missing.append('NOTION_API_TOKEN')

    if missing:
        print("❌ Error: Missing required environment variables:")
        for var in missing:
            print(f"   - {var}")
        print("\nPlease set them in your .env file or export them:")
        print(f"   export VOLCENGINE_API_TOKEN='your-token'")
        print(f"   export NOTION_API_TOKEN='your-token'")
        return False

    return True


def test_volcengine_model():
    """Test VolcEngine (Doubao) model connection"""
    print("=" * 60)
    print("Testing VolcEngine (Doubao) Model Connection")
    print("=" * 60)

    app = create_app('development')
    with app.app_context():
        service = ConfigurationService()

        # Create or get model configuration
        try:
            models = service.get_all_model_configs()
            volcengine_model = None
            for m in models:
                if m.name == VOLCENGINE_CONFIG['name']:
                    volcengine_model = m
                    print(f"✓ Found existing model config: {m.name} (ID: {m.id})")
                    break

            if not volcengine_model:
                print("\n📝 Creating new model configuration...")
                volcengine_model = service.create_model_config(**VOLCENGINE_CONFIG)
                print(f"✓ Created model config: {volcengine_model.name} (ID: {volcengine_model.id})")

            # Test connection
            print(f"\n🔌 Testing connection to {VOLCENGINE_CONFIG['api_url']}...")
            model_service = get_model_service()

            # Get decrypted token
            model_with_token = service.get_model_config(volcengine_model.id, decrypt_token=True)

            result = model_service.test_connection(
                api_url=model_with_token.api_url,
                api_token=model_with_token.api_token,
                model_name=model_with_token.name,
                timeout=model_with_token.timeout
            )

            print(f"\n📊 Connection Test Result:")
            print(f"  Success: {result['success']}")

            if result['success']:
                print(f"  ✅ Latency: {result['latency_ms']}ms")
                print(f"  Model: {result['model_info']['model']}")
                print(f"  Response: {result['model_info']['response'][:100]}...")
                print(f"  Tokens used: {result['model_info'].get('usage', {})}")

                # Update status
                service.update_model_config(volcengine_model.id, status='active', is_active=True)
                print(f"\n✅ Model status updated to 'active'")
            else:
                print(f"  ❌ Error: {result.get('error', 'Unknown error')}")
                service.update_model_config(volcengine_model.id, status='failed', is_active=False)
                print(f"\n❌ Model status updated to 'failed'")

            return result['success']

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


def test_notion_api():
    """Test Notion API connection"""
    print("\n" + "=" * 60)
    print("Testing Notion API Connection")
    print("=" * 60)

    app = create_app('development')
    with app.app_context():
        service = ConfigurationService()

        try:
            # Create or update Notion configuration
            print("\n📝 Saving Notion configuration...")
            notion_config = service.create_or_update_notion_config(
                api_token=NOTION_TOKEN
            )
            print(f"✓ Notion config saved (ID: {notion_config.id})")

            # Test connection
            print(f"\n🔌 Testing connection to Notion API...")
            notion_service = get_notion_service()

            # Get decrypted token
            notion_with_token = service.get_notion_config(decrypt_token=True)

            result = notion_service.test_connection(api_token=notion_with_token.api_token)

            print(f"\n📊 Connection Test Result:")
            print(f"  Success: {result['success']}")

            if result['success']:
                workspace_info = result['workspace_info']
                print(f"  ✅ Bot ID: {workspace_info['bot_id']}")
                print(f"  Bot Name: {workspace_info['bot_name']}")
                print(f"  Workspace: {workspace_info['workspace_name']}")
                print(f"  Databases found: {result['databases_count']}")

                if result['databases']:
                    print(f"\n  📚 Accessible Databases:")
                    for db in result['databases'][:5]:  # Show first 5
                        print(f"    - {db['title']} ({db['id'][:8]}...)")

                # Update configuration with workspace info
                service.create_or_update_notion_config(
                    api_token=NOTION_TOKEN,
                    workspace_id=workspace_info['bot_id'],
                    workspace_name=workspace_info['workspace_name']
                )

                # Update status
                from app import db as database
                notion_config.status = 'active'
                database.session.commit()
                print(f"\n✅ Notion status updated to 'active'")
            else:
                print(f"  ❌ Error: {result.get('error', 'Unknown error')}")
                from app import db as database
                notion_config.status = 'failed'
                database.session.commit()
                print(f"\n❌ Notion status updated to 'failed'")

            return result['success']

        except Exception as e:
            print(f"\n❌ Error: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    print("\n🚀 Starting Real API Connection Tests\n")

    # Check if credentials are set
    if not check_credentials():
        exit(1)

    # Test VolcEngine
    volcengine_success = test_volcengine_model()

    # Test Notion
    notion_success = test_notion_api()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"VolcEngine (Doubao): {'✅ PASS' if volcengine_success else '❌ FAIL'}")
    print(f"Notion API:          {'✅ PASS' if notion_success else '❌ FAIL'}")
    print()

    if volcengine_success and notion_success:
        print("🎉 All API connections successful!")
        exit(0)
    else:
        print("⚠️  Some API connections failed. Check errors above.")
        exit(1)
