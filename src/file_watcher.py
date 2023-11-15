import os
import stat


def check_entry_for_updates(entry_to_watch: str, old_last_updated: int = 0) -> int:
    s = os.stat(entry_to_watch)
    entry_last_updated = s.st_mtime_ns
    if entry_last_updated > old_last_updated:
        return entry_last_updated

    if stat.S_ISDIR(s.st_mode):
        for f in os.listdir(entry_to_watch):
            path_child = os.path.join(entry_to_watch, f)
            entry_last_updated = check_entry_for_updates(path_child, old_last_updated)
            if entry_last_updated > old_last_updated:
                return entry_last_updated

    return old_last_updated
