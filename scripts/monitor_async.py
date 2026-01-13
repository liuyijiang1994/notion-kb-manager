#!/usr/bin/env python3
"""
Real-time monitoring dashboard for async task system

Usage:
    python scripts/monitor_async.py           # Live dashboard
    python scripts/monitor_async.py --once    # Single snapshot
    python scripts/monitor_async.py --json    # JSON output
"""
import sys
import time
import json
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import redis
from rq import Queue, Worker
from rq.registry import (
    StartedJobRegistry,
    FinishedJobRegistry,
    FailedJobRegistry,
    ScheduledJobRegistry
)
from config.workers import WorkerConfig

# Color codes
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'
    CLEAR = '\033[2J'
    HOME = '\033[H'

def clear_screen():
    """Clear terminal screen"""
    print(Colors.CLEAR + Colors.HOME, end='')

def print_header():
    """Print dashboard header"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}Notion KB Manager - Async Task System Dashboard{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*80}{Colors.END}")
    print(f"{Colors.CYAN}Updated: {timestamp}{Colors.END}\n")

def get_redis_stats(redis_conn):
    """Get Redis statistics"""
    try:
        info = redis_conn.info()
        return {
            'status': 'connected',
            'version': info.get('redis_version', 'unknown'),
            'uptime_days': info.get('uptime_in_days', 0),
            'connected_clients': info.get('connected_clients', 0),
            'used_memory_human': info.get('used_memory_human', '0'),
            'used_memory_peak_human': info.get('used_memory_peak_human', '0'),
            'total_commands_processed': info.get('total_commands_processed', 0),
            'instantaneous_ops_per_sec': info.get('instantaneous_ops_per_sec', 0),
        }
    except redis.ConnectionError:
        return {'status': 'disconnected'}

def get_queue_stats(redis_conn, queue_name):
    """Get statistics for a specific queue"""
    try:
        queue = Queue(queue_name, connection=redis_conn)

        started = StartedJobRegistry(queue_name, connection=redis_conn)
        finished = FinishedJobRegistry(queue_name, connection=redis_conn)
        failed = FailedJobRegistry(queue_name, connection=redis_conn)
        scheduled = ScheduledJobRegistry(queue_name, connection=redis_conn)

        return {
            'name': queue_name,
            'pending': len(queue),
            'running': len(started),
            'finished': len(finished),
            'failed': len(failed),
            'scheduled': len(scheduled),
            'total': len(queue) + len(started) + len(scheduled)
        }
    except Exception as e:
        return {
            'name': queue_name,
            'error': str(e)
        }

def get_worker_stats(redis_conn):
    """Get statistics for all workers"""
    try:
        workers = Worker.all(connection=redis_conn)

        stats = {
            'total': len(workers),
            'busy': 0,
            'idle': 0,
            'suspended': 0,
            'workers': []
        }

        for worker in workers:
            state = worker.get_state()
            current_job = worker.get_current_job()

            if state == 'busy':
                stats['busy'] += 1
            elif state == 'idle':
                stats['idle'] += 1
            elif state == 'suspended':
                stats['suspended'] += 1

            worker_info = {
                'name': worker.name,
                'state': state,
                'queues': [q.name for q in worker.queues],
                'success_count': worker.successful_job_count,
                'failed_count': worker.failed_job_count,
                'current_job': current_job.func_name if current_job else None,
                'birth_date': worker.birth_date.isoformat() if worker.birth_date else None
            }

            stats['workers'].append(worker_info)

        return stats
    except Exception as e:
        return {'error': str(e)}

def print_redis_stats(stats):
    """Print Redis statistics"""
    print(f"{Colors.BOLD}Redis Server{Colors.END}")

    if stats['status'] == 'disconnected':
        print(f"  {Colors.RED}✗ Disconnected{Colors.END}\n")
        return

    print(f"  {Colors.GREEN}✓ Connected{Colors.END} (v{stats['version']})")
    print(f"  Uptime: {stats['uptime_days']} days")
    print(f"  Clients: {stats['connected_clients']}")
    print(f"  Memory: {stats['used_memory_human']} (peak: {stats['used_memory_peak_human']})")
    print(f"  Ops/sec: {stats['instantaneous_ops_per_sec']}")
    print()

def print_queue_stats(all_stats):
    """Print queue statistics"""
    print(f"{Colors.BOLD}Queue Status{Colors.END}")

    # Header
    print(f"  {'Queue':<15} {'Pending':>8} {'Running':>8} {'Failed':>8} {'Finished':>10} {'Total':>8}")
    print(f"  {'-'*70}")

    for stats in all_stats:
        if 'error' in stats:
            print(f"  {stats['name']:<15} {Colors.RED}Error{Colors.END}")
            continue

        name = stats['name']
        pending = stats['pending']
        running = stats['running']
        failed = stats['failed']
        finished = stats['finished']
        total = stats['total']

        # Color based on load
        if pending > 100:
            color = Colors.RED
        elif pending > 50:
            color = Colors.YELLOW
        else:
            color = Colors.GREEN

        print(f"  {name:<15} {color}{pending:>8}{Colors.END} {running:>8} ", end='')

        # Color failed count
        if failed > 10:
            failed_color = Colors.RED
        elif failed > 0:
            failed_color = Colors.YELLOW
        else:
            failed_color = Colors.GREEN

        print(f"{failed_color}{failed:>8}{Colors.END} {finished:>10} {total:>8}")

    print()

def print_worker_stats(stats):
    """Print worker statistics"""
    print(f"{Colors.BOLD}Workers{Colors.END}")

    if 'error' in stats:
        print(f"  {Colors.RED}✗ Error: {stats['error']}{Colors.END}\n")
        return

    if stats['total'] == 0:
        print(f"  {Colors.YELLOW}⚠ No workers running{Colors.END}")
        print(f"  Start workers: python scripts/start_workers.py\n")
        return

    # Summary
    print(f"  Total: {stats['total']} workers")
    print(f"  {Colors.GREEN}Idle: {stats['idle']}{Colors.END} | ", end='')
    print(f"{Colors.BLUE}Busy: {stats['busy']}{Colors.END} | ", end='')
    print(f"{Colors.YELLOW}Suspended: {stats['suspended']}{Colors.END}\n")

    # Worker details
    if stats['workers']:
        print(f"  {'Name':<30} {'State':<10} {'Queue':<15} {'Jobs (S/F)':<12} {'Current Job'}")
        print(f"  {'-'*100}")

        for worker in stats['workers'][:10]:  # Show first 10 workers
            name = worker['name']
            state = worker['state']
            queues = ', '.join(worker['queues'])
            jobs = f"{worker['success_count']}/{worker['failed_count']}"
            current = worker['current_job'] or '-'

            # Color state
            if state == 'busy':
                state_colored = f"{Colors.BLUE}{state}{Colors.END}"
            elif state == 'idle':
                state_colored = f"{Colors.GREEN}{state}{Colors.END}"
            else:
                state_colored = f"{Colors.YELLOW}{state}{Colors.END}"

            # Truncate current job name
            if len(current) > 30:
                current = current[:27] + '...'

            print(f"  {name:<30} {state_colored:<20} {queues:<15} {jobs:<12} {current}")

        if len(stats['workers']) > 10:
            print(f"\n  ... and {len(stats['workers']) - 10} more workers")

    print()

def print_summary(redis_stats, queue_stats, worker_stats):
    """Print summary status"""
    print(f"{Colors.BOLD}Summary{Colors.END}")

    # Overall health
    healthy = True
    issues = []

    if redis_stats['status'] == 'disconnected':
        healthy = False
        issues.append("Redis disconnected")

    total_pending = sum(q.get('pending', 0) for q in queue_stats)
    if total_pending > 500:
        healthy = False
        issues.append(f"High queue backlog ({total_pending} jobs)")

    total_failed = sum(q.get('failed', 0) for q in queue_stats)
    if total_failed > 50:
        issues.append(f"High failure rate ({total_failed} failed jobs)")

    if worker_stats.get('total', 0) == 0:
        healthy = False
        issues.append("No workers running")

    # Print status
    if healthy:
        print(f"  Status: {Colors.GREEN}✓ Healthy{Colors.END}")
    else:
        print(f"  Status: {Colors.RED}✗ Unhealthy{Colors.END}")

    if issues:
        print(f"  Issues:")
        for issue in issues:
            print(f"    - {Colors.YELLOW}{issue}{Colors.END}")
    else:
        print(f"  {Colors.GREEN}All systems operational{Colors.END}")

    # Stats
    print(f"\n  Total pending jobs: {total_pending}")
    print(f"  Total failed jobs: {total_failed}")
    print(f"  Active workers: {worker_stats.get('total', 0)}")
    print()

def monitor_once(redis_conn, output_json=False):
    """Single snapshot of system status"""
    redis_stats = get_redis_stats(redis_conn)

    queue_stats = []
    for queue_name in ['parsing', 'ai', 'notion', 'default']:
        stats = get_queue_stats(redis_conn, queue_name)
        queue_stats.append(stats)

    worker_stats = get_worker_stats(redis_conn)

    if output_json:
        # JSON output
        data = {
            'timestamp': datetime.now().isoformat(),
            'redis': redis_stats,
            'queues': queue_stats,
            'workers': worker_stats
        }
        print(json.dumps(data, indent=2))
    else:
        # Pretty output
        print_header()
        print_redis_stats(redis_stats)
        print_queue_stats(queue_stats)
        print_worker_stats(worker_stats)
        print_summary(redis_stats, queue_stats, worker_stats)

def monitor_live(redis_conn, interval=2):
    """Live monitoring dashboard"""
    try:
        while True:
            clear_screen()
            monitor_once(redis_conn, output_json=False)
            print(f"{Colors.CYAN}Refreshing in {interval} seconds... (Press Ctrl+C to exit){Colors.END}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}✓ Monitoring stopped{Colors.END}")

def main():
    parser = argparse.ArgumentParser(description='Monitor async task system')
    parser.add_argument('--once', action='store_true', help='Show single snapshot')
    parser.add_argument('--json', action='store_true', help='Output as JSON')
    parser.add_argument('--interval', type=int, default=2, help='Refresh interval (seconds)')

    args = parser.parse_args()

    # Connect to Redis
    try:
        redis_conn = redis.from_url(WorkerConfig.REDIS_URL)
        redis_conn.ping()
    except redis.ConnectionError:
        print(f"{Colors.RED}✗ Cannot connect to Redis at {WorkerConfig.REDIS_URL}{Colors.END}")
        print(f"{Colors.YELLOW}Start Redis with: redis-server{Colors.END}")
        sys.exit(1)

    # Run monitoring
    if args.once or args.json:
        monitor_once(redis_conn, output_json=args.json)
    else:
        monitor_live(redis_conn, interval=args.interval)

if __name__ == '__main__':
    main()
