import re
from typing import Tuple, Dict

from asyncpg import UndefinedFunctionError, UndefinedObjectError, Connection

from openmaptiles.perfutils import RED, RESET


async def show_settings(conn: Connection) -> Tuple[Dict[str, str], bool]:
    is_postgis_v3 = False
    results = {}

    def parse_postgis_ver(value) -> None:
        nonlocal is_postgis_v3
        m = re.match(r'POSTGIS="(\d+)\.', value)
        is_postgis_v3 = int(m.group(1)) >= 3 if m else False

    for setting, validator in {
        'version()': None,
        'postgis_full_version()': parse_postgis_ver,
        'jit': lambda
            v: 'disable JIT in PG 11-12 for complex queries' if v != 'off' else '',
        'shared_buffers': None,
        'work_mem': None,
        'maintenance_work_mem': None,
        'max_connections': None,
        'max_worker_processes': None,
        'max_parallel_workers': None,
        'max_parallel_workers_per_gather': None,
    }.items():
        q = f"{'SELECT' if '(' in setting else 'SHOW'} {setting};"
        prefix = ''
        suffix = ''
        try:
            res = await conn.fetchval(q)
            if validator:
                msg = validator(res)
                if msg:
                    prefix, suffix = RED, f" {msg}{RESET}"
        except (UndefinedFunctionError, UndefinedObjectError) as ex:
            res = ex.message
            prefix, suffix = RED, RESET

        print(f"* {prefix}{setting:32} = {res}{suffix}")
        results[setting] = res

    print('vv', is_postgis_v3)
    return results, is_postgis_v3
