# Copyright (©) 2025, Alexander Suvorov. All rights reserved.
from typing import Dict, Any
from datetime import datetime


class UIStateManager:
    def __init__(self):
        self.state: Dict[str, Any] = {
            'current_user': None,
            'user_name': None,
            'repositories_count': 0,
            'local_repositories_count': 0,
            'needs_update_count': 0,
            'ssh_status': 'unknown',
            'ssh_can_clone': False,
            'ssh_can_pull': False,
            'is_syncing': False,
            'sync_progress': 0,
            'sync_current_repo': None,
            'last_error': None,
            'storage_size_mb': 0,
            'users_list': [],
            'total_private': 0,
            'total_public': 0,
            'total_archived': 0,
            'total_forks': 0,
            'last_update': None
        }

    def update(self, **kwargs):
        self.state.update(kwargs)
        self.state['last_update'] = datetime.now().isoformat()
        return self

    def bulk_update(self, data: Dict[str, Any]):
        self.state.update(data)
        self.state['last_update'] = datetime.now().isoformat()
        return self

    def get(self, key: str, default: Any = None) -> Any:
        return self.state.get(key, default)

    def set(self, key: str, value: Any):
        self.state[key] = value
        self.state['last_update'] = datetime.now().isoformat()
        return self

    def reset(self):
        self.__init__()
        return self

    def get_state_summary(self) -> Dict[str, Any]:
        return {
            'user': self.state.get('current_user'),
            'repositories': {
                'total': self.state.get('repositories_count', 0),
                'local': self.state.get('local_repositories_count', 0),
                'needs_update': self.state.get('needs_update_count', 0)
            },
            'ssh_status': self.state.get('ssh_status'),
            'storage_mb': self.state.get('storage_size_mb', 0),
            'last_update': self.state.get('last_update')
        }
