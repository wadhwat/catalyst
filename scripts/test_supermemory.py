from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from src.memory.supermemory_client import SupermemoryClient


def main() -> int:
    parser = argparse.ArgumentParser(description='Test Supermemory integration.')
    parser.add_argument('--vin', default='VIN_TEST_001')
    parser.add_argument('--note', default='Test memory from CATalyst Inspect.')
    args = parser.parse_args()

    client = SupermemoryClient()
    payload = {
        'vin': args.vin,
        'client_trace_id': f'test-{datetime.utcnow().isoformat()}',
        'summary_status': 'UNKNOWN',
        'items': [{'id': 'radiator_debris', 'status': 'UNKNOWN'}],
        'references': [],
    }

    created = client.create_memory(
        kind='session_summary',
        content=payload,
        tags=[f'vin:{args.vin}', 'kind:session_summary'],
        metadata={'vin': args.vin},
    )
    print('create_memory:', json.dumps(created, indent=2))

    results = client.search_memories(tags=[f'vin:{args.vin}'], limit=3)
    print('search_memories:', json.dumps(results, indent=2))
    return 0


if __name__ == '__main__':
    sys.exit(main())
