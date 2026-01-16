#!/usr/bin/env python3
"""
Test script for Notion KB Manager import functionality
Demonstrates the full workflow: Import → Parse → AI Processing → Task Monitoring
"""
import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:5001/api"
USERNAME = "admin"
PASSWORD = "admin123"

# Test URL - use timestamp to ensure uniqueness
import random
TEST_URL = f"https://httpbin.org/uuid?test={int(time.time())}&r={random.randint(1000, 9999)}"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def login():
    """Login and get access token"""
    print_section("Step 1: Authentication")

    response = requests.post(
        f"{API_BASE_URL}/auth/login",
        json={"username": USERNAME, "password": PASSWORD}
    )

    if response.status_code == 200:
        data = response.json()
        token = data['data']['access_token']
        user = data['data']['user']
        print(f"✅ Logged in as: {user['username']}")
        print(f"   Roles: {', '.join(user['roles'])}")
        return token
    else:
        print(f"❌ Login failed: {response.text}")
        return None

def import_url(token, url):
    """Import a URL using manual import endpoint"""
    print_section("Step 2: Import URL")
    print(f"📥 Importing: {url}")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    # Use manual import endpoint which extracts URLs from text
    response = requests.post(
        f"{API_BASE_URL}/links/import/manual",
        headers=headers,
        json={
            "text": url,
            "task_name": f"Import {url}"
        }
    )

    if response.status_code in [200, 201]:
        data = response.json()
        print(f"✅ URL imported!")
        print(f"   Total: {data['data']['total']}")
        print(f"   Imported: {data['data']['imported']}")
        print(f"   Task ID: {data['data']['task_id']}")
        return data['data']
    else:
        print(f"❌ Import failed: {response.text}")
        return None

def start_parsing(token, link_ids):
    """Start async parsing for imported links"""
    print_section("Step 3: Start Parsing")
    print(f"🔄 Starting parsing for {len(link_ids)} link(s)")

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        f"{API_BASE_URL}/parsing/async/batch",
        headers=headers,
        json={"link_ids": link_ids}
    )

    if response.status_code in [200, 202]:
        data = response.json()
        print(f"✅ Parsing queued!")
        print(f"   Task ID: {data['data']['task_id']}")
        print(f"   Job ID: {data['data']['job_id']}")
        return data['data']
    else:
        print(f"❌ Parsing failed: {response.text}")
        return None

def get_imported_links(token, task_id):
    """Get links imported by a task"""
    print_section("Step 3: Get Imported Links")

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{API_BASE_URL}/links?task_id={task_id}&limit=10",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        links = data.get('data', {}).get('links', [])

        print(f"📋 Found {len(links)} imported link(s)")

        link_ids = []
        for link in links:
            print(f"\n   ID: {link['id']}")
            print(f"   URL: {link['url']}")
            print(f"   Title: {link.get('title', 'N/A')}")
            link_ids.append(link['id'])

        return link_ids
    else:
        print(f"❌ Failed to get links: {response.text}")
        return []

def get_all_tasks(token):
    """Get all processing tasks"""
    print_section("Check Tasks")

    headers = {"Authorization": f"Bearer {token}"}

    # Get both pending and historical tasks
    pending_response = requests.get(
        f"{API_BASE_URL}/tasks/pending?page=1&per_page=50",
        headers=headers
    )

    history_response = requests.get(
        f"{API_BASE_URL}/tasks/history?page=1&per_page=50",
        headers=headers
    )

    tasks = []

    if pending_response.status_code == 200:
        pending_data = pending_response.json()
        tasks.extend(pending_data.get('data', {}).get('tasks', []))

    if history_response.status_code == 200:
        history_data = history_response.json()
        tasks.extend(history_data.get('data', {}).get('tasks', []))

    if tasks:

        print(f"📋 Total tasks: {len(tasks)} (pending + history)")

        for task in tasks[:10]:  # Show max 10 tasks
            status_emoji = {
                'pending': '⏳',
                'queued': '🔵',
                'running': '🔄',
                'completed': '✅',
                'failed': '❌',
                'cancelled': '⛔'
            }.get(task['status'], '❓')

            print(f"\n{status_emoji} Task #{task['id']} - {task['type']}")
            print(f"   Status: {task['status']}")
            print(f"   Progress: {task['progress']}%")
            print(f"   Items: {task['completed_items']}/{task['total_items']}")
            if task.get('error_log'):
                print(f"   Errors: {task['error_log']}")

    else:
        print(f"⚠️  No tasks found")

    return tasks

def monitor_task(token, task_id, timeout=60):
    """Monitor a task until completion or timeout"""
    print_section(f"Monitor Task #{task_id}")

    headers = {"Authorization": f"Bearer {token}"}
    start_time = time.time()

    while time.time() - start_time < timeout:
        response = requests.get(
            f"{API_BASE_URL}/parsing/async/status/{task_id}",
            headers=headers
        )

        if response.status_code == 200:
            data = response.json()
            task = data['data']['task']

            status = task['status']
            progress = task['progress']

            status_emoji = {
                'pending': '⏳',
                'queued': '🔵',
                'running': '🔄',
                'completed': '✅',
                'failed': '❌'
            }.get(status, '❓')

            elapsed = int(time.time() - start_time)
            print(f"\r{status_emoji} Status: {status:12} | Progress: {progress:3}% | Elapsed: {elapsed}s", end='', flush=True)

            if status in ['completed', 'failed', 'cancelled']:
                print()  # New line
                print(f"\n🏁 Task {status}!")
                return task

            time.sleep(2)  # Check every 2 seconds
        else:
            print(f"\n❌ Failed to get task status: {response.text}")
            return None

    print(f"\n⏰ Timeout after {timeout}s")
    return None

def get_system_health(token):
    """Check system health"""
    print_section("System Health Check")

    headers = {"Authorization": f"Bearer {token}"}

    response = requests.get(
        f"{API_BASE_URL}/monitoring/health",
        headers=headers
    )

    if response.status_code == 200:
        data = response.json()
        health = data['data']['health']

        print(f"🔧 Redis: {health['redis']}")
        print(f"👷 Workers: {health['workers']['total']} total, "
              f"{health['workers']['active']} active, "
              f"{health['workers']['busy']} busy")

        queues = health['queues']
        for queue_name, queue_info in queues.items():
            status = '✅' if queue_info['healthy'] else '❌'
            print(f"   {status} {queue_name}: {queue_info['pending']} pending")

        return health
    else:
        print(f"❌ Failed to get health: {response.text}")
        return None

def main():
    """Main test workflow"""
    print("="*60)
    print("  Notion KB Manager - Import Test")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Step 1: Login
    token = login()
    if not token:
        print("\n❌ Test failed: Could not authenticate")
        return

    # Check system health
    get_system_health(token)

    # Step 2: Import URL
    import_result = import_url(token, TEST_URL)
    if not import_result:
        print("\n❌ Test failed: Could not import URL")
        return

    import_task_id = import_result.get('task_id')

    # Wait a moment for import to complete
    time.sleep(2)

    # Step 3: Get imported links
    link_ids = get_imported_links(token, import_task_id)
    if not link_ids:
        print("\n❌ Test failed: No links were imported")
        return

    # Step 4: Start parsing
    parsing_result = start_parsing(token, link_ids)
    if not parsing_result:
        print("\n❌ Test failed: Could not start parsing")
        return

    parsing_task_id = parsing_result.get('task_id')

    # Step 5: Monitor parsing task
    monitor_task(token, parsing_task_id, timeout=120)

    # Step 6: Check all tasks
    print_section("All Tasks")
    tasks = get_all_tasks(token)

    # Final status
    print_section("Test Complete")
    final_tasks = get_all_tasks(token)

    completed = sum(1 for t in final_tasks if t['status'] == 'completed')
    failed = sum(1 for t in final_tasks if t['status'] == 'failed')
    running = sum(1 for t in final_tasks if t['status'] == 'running')

    print(f"📊 Summary:")
    print(f"   ✅ Completed: {completed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   🔄 Running: {running}")
    print(f"   📋 Total: {len(final_tasks)}")

    print(f"\n✨ Test finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
