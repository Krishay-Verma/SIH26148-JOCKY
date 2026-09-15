"""
Collector registry: the single allowlist of collectors the interpreter
is permitted to run.

This is the safety boundary of the whole system. The interpreter never
calls a collector function directly by constructing its name dynamically
(e.g. no getattr(module, user_input)). It only ever looks functions up
in this dict. If a name isn't a key here, it cannot run — period.
"""

from functools import partial

from jocky.collectors.system_info import collect_system_info
from jocky.collectors.processes import collect_processes
from jocky.collectors.network_connections import collect_network_connections
from jocky.collectors.logged_in_users import collect_logged_in_users
from jocky.collectors.file_hash import collect_file_hashes

# Maps the JOCKY script name (what an investigator writes in `collect X;`)
# to the actual Python function that performs the collection.

# file_hash needs a target directory. Until the API milestone lets an
# investigator choose one per-investigation, we bind it to a fixed test
# folder so the registry's contract ("every collector is a zero-argument
# callable") stays consistent for the interpreter.
_TEST_HASH_DIRECTORY = "./sample_evidence"

COLLECTOR_REGISTRY = {
    "system_info": collect_system_info,
    "processes": collect_processes,
    "network_connections": collect_network_connections,
    "logged_in_users": collect_logged_in_users,
    "file_hash": partial(collect_file_hashes, _TEST_HASH_DIRECTORY),
}

def is_known_collector(name: str) -> bool:
    return name in COLLECTOR_REGISTRY


def get_collector(name: str):
    """Raise KeyError with a clear message if name isn't allowlisted."""
    if name not in COLLECTOR_REGISTRY:
        raise KeyError(f"Unknown collector: {name!r}")
    return COLLECTOR_REGISTRY[name]
