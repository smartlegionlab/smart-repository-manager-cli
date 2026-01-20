# Copyright (©) 2025, Alexander Suvorov. All rights reserved.
import ipaddress
import socket
import sys
import time
import signal
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

import requests

from engine.ui.result_logger import ResultLogger
from engine.ui.state_manager import UIStateManager
from engine.utils.decorator import (
    Colors,
    clear_screen,
    print_section,
    print_info,
    Icons,
    print_success,
    print_error,
    print_warning
)

sys.path.insert(0, str(Path(__file__).parent))

try:
    from smart_repository_manager_core.core.models.repository import Repository
    from smart_repository_manager_core.core.models.user import User
    from smart_repository_manager_core.services.git_service import GitService
    from smart_repository_manager_core.services.github_service import GitHubService
    from smart_repository_manager_core.services.network_service import NetworkService
    from smart_repository_manager_core.services.ssh_service import SSHService
    from smart_repository_manager_core.services.structure_service import StructureService
    from smart_repository_manager_core.services.sync_service import SyncService
    from smart_repository_manager_core.utils.helpers import Helpers
except ImportError as e:
    print(f"Error importing core modules: {e}")
    sys.exit(1)


class SmartGitCLI:
    def __init__(self, config_path: str = "config.json"):
        self.config_path = Path.home() / "smart_repo_manager" / config_path
        self.current_user: Optional[User] = None
        self.current_token: Optional[str] = None
        self.repositories: List[Repository] = []
        self.structure_service = StructureService()
        self.git_service = GitService()
        self.sync_service = SyncService()
        self.ssh_service = SSHService()
        self.network_service = NetworkService()

        self.ui_state = UIStateManager()
        self.result_logger = ResultLogger()

        self._retry_counts: Dict[str, int] = {}
        self._max_retries = 3

        self.menu_stack = []
        self.current_menu = "main"
        self.running = True

        signal.signal(signal.SIGINT, self._signal_handler)

        self.print_header()

    def _signal_handler(self, signum, frame):
        _ = signum, frame
        print(f"\n\n{Colors.RED}Interrupt signal received. Exiting...{Colors.END}")
        self.running = False
        sys.exit(0)

    def _get_repository_needs_update(self, repo: Repository) -> bool:
        if not self.current_user:
            return False

        try:
            needs_update, _ = self.sync_service.check_repository_needs_update(
                self.current_user,
                repo
            )
            return needs_update
        except Exception as e:
            print(e)
            return False

    def print_header(self):
        clear_screen()
        print_section("Smart Repository Manager - FULL SYSTEM CHECK")
        print_info("Initializing system...")

    def log_step(self, step: int, title: str):
        print(f"\n{Colors.BOLD}{Colors.CYAN}Step {step}: {title}{Colors.END}")
        print(f"{Colors.CYAN}{'-' * 50}{Colors.END}")

    def log_result(self, success: bool, message: str, data: Dict[str, Any] = None):
        return self.result_logger.log_result(success, message, data)

    def save_results(self):
        if not self.current_user:
            print_error("No user selected")
            return

        results_dir = (Path.home() / "smart_repo_manager" / f"{self.current_user.username}" / "logs")
        self.result_logger.save_results(self.current_user.username, results_dir)

    def load_repositories(self):
        if not self.current_token or not self.current_user:
            return False

        try:
            github_service = GitHubService(self.current_token)
            success, repositories = github_service.fetch_user_repositories()

            if success:
                self.repositories = repositories
                print_success(f"Loaded {len(repositories)} repositories")
                return True
            else:
                print_error("Failed to load repositories")
                return False

        except Exception as e:
            print_error(f"Error loading repositories: {e}")
            return False

    def _calculate_needs_update_count(self) -> int:
        if not self.current_user or not self.repositories:
            return 0

        needs_update_count = 0

        for repo in self.repositories:
            if not repo.ssh_url:
                continue

            needs_update, _ = self.sync_service.check_repository_needs_update(
                self.current_user,
                repo
            )

            if needs_update:
                needs_update_count += 1

        return needs_update_count

    def _show_sync_summary(self, stats: Dict[str, Any], operation: str):
        print(f"\n{Colors.BOLD}{'=' * 60}{Colors.END}")
        print(f"{Colors.BOLD}{operation.upper()} SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'=' * 60}{Colors.END}")

        print(f"\n{Colors.BOLD}📊 Results:{Colors.END}")
        for key, value in stats.items():
            if key != "durations" and isinstance(value, int):
                icon = Icons.SUCCESS if value > 0 and key in ["cloned", "synced", "repaired"] else Icons.INFO
                print(f"  {icon} {key.replace('_', ' ').title()}: {value}")

        if stats["durations"]:
            total_time = sum(stats["durations"])
            avg_time = total_time / len(stats["durations"]) if stats["durations"] else 0

            print(f"\n{Colors.BOLD}⏱️ Performance:{Colors.END}")
            print(f"  • Total time: {Helpers.format_duration(total_time)}")
            print(f"  • Average per repo: {Helpers.format_duration(avg_time)}")

    def _update_ui_state(self):
        self.ui_state.get_all_repositories(self.repositories)
        self.ui_state.get_local_repositories(self.repositories)
        self.ui_state.get_private_public_repositories(self.repositories)

        self.ui_state.set('needs_update_count', self._calculate_needs_update_count())

    def _get_external_ip(self) -> Optional[str]:

        ip_services = [
            "https://api.ipify.org",
            "https://icanhazip.com",
            "https://ident.me",
            "https://checkip.amazonaws.com",
            "https://ifconfig.me/ip"
        ]

        for service in ip_services:
            try:
                response = requests.get(service, timeout=3)
                if response.status_code == 200:
                    ip = response.text.strip()
                    if self._is_valid_ip(ip):
                        return ip
            except Exception as e:
                print(e)
                continue

        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            if self._is_valid_ip(ip_address):
                return f"{ip_address} (local)"
        except Exception as e:
            print(e)
            pass

        return None

    def _is_valid_ip(self, ip: str) -> bool:

        try:
            clean_ip = ip.split(' ')[0]
            ipaddress.ip_address(clean_ip)
            return True
        except ValueError:
            return False

    def _run_step_with_retry(self, step_func: Callable, step_name: str, step_description: str,
                             max_retries: int = None) -> bool:
        if max_retries is None:
            max_retries = self._max_retries

        retry_count = 0
        self._retry_counts[step_name] = 0

        while retry_count <= max_retries:
            try:
                print(f"\n  [{step_name.upper()}] {step_description} (attempt {retry_count + 1}/{max_retries + 1})")

                success = step_func()

                if success:
                    print_success(f"{step_description} completed successfully")
                    return True
                else:
                    retry_count += 1
                    self._retry_counts[step_name] += 1

                    if retry_count <= max_retries:
                        print_warning(f"{step_description} failed, retrying in 2 seconds...")
                        time.sleep(2)
                    else:
                        print_error(f"{step_description} failed after {max_retries} attempts")
                        return False

            except Exception as e:
                print_error(f"Exception in {step_name}: {str(e)}")
                retry_count += 1
                self._retry_counts[step_name] += 1

                if retry_count <= max_retries:
                    print_warning("Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    return False

        return False
