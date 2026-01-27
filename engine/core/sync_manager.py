# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import subprocess

from engine.utils.text_decorator import (
    Colors,
    clear_screen,
    print_section,
    print_info, Icons,
    print_success,
    print_error,
    print_warning,
    wait_for_enter,
    print_menu_item
)
from smart_repository_manager_core.utils.helpers import Helpers

class SyncManager:
    def __init__(self, cli):
        self.cli = cli

    def show_sync_menu(self):
        self.cli.menu_stack.append(self.cli.current_menu)
        self.cli.current_menu = "sync"

        while self.cli.current_menu == "sync":
            clear_screen()
            print_section("SYNCHRONIZATION")

            print(f"\n{Colors.BOLD}📊 Status:{Colors.END}")
            print(f"  • Total repositories: {self.cli.ui_state.get('repositories_count', 0)}")
            print(f"  • Local repositories: {self.cli.get_local_exist_repos_count()}")
            print(f"  • Needs update: {self.cli.get_need_update_repos_count()}")

            print(f"\n{Colors.BOLD}🔄 Commands:{Colors.END}")
            print_menu_item("1", "Synchronize All", Icons.SYNC)
            print_menu_item("2", "Update Needed Only", Icons.SYNC)
            print_menu_item("3", "Clone Missing Only", Icons.DOWNLOAD)
            print_menu_item("4", "Sync with Repair", Icons.SETTINGS)
            print_menu_item("5", "Re-clone All", Icons.SETTINGS)

            print(f"\n{Colors.BOLD}{Colors.BLUE}0.{Colors.END} {Icons.BACK} Back")
            print('=' * 60)

            choice = self.cli.get_menu_choice("Select option", 0, 5)

            if choice == 0:
                self.cli.current_menu = self.cli.menu_stack.pop()
            elif choice == 1:
                self.sync_all_repositories()
            elif choice == 2:
                self.update_needed_repositories()
            elif choice == 3:
                self.sync_missing_repositories()
            elif choice == 4:
                self.sync_with_repair()
            elif choice == 5:
                self.reclone_all_repos()

            if choice != 0:
                wait_for_enter()

    def reclone_all_repos(self):
        clear_screen()
        print_section("RE-CLONE ALL REPOSITORIES")

        structure = self.cli.structure_service.get_user_structure(self.cli.current_user.username)
        if "repositories" not in structure:
            print_error("Storage structure not found")
            return

        repo_list = self.cli.repositories

        repos_path = structure['repositories']

        print(f"\n{Colors.BOLD}Found {len(repo_list)} repositories:{Colors.END}")
        for i, repo in enumerate(repo_list, 1):
            print(f"  {i}. {repo.name}")

        if not self.cli.ask_yes_no(f"\nRe-clone {len(repo_list)} repositories?"):
            return

        print_info(f"\nStarting re-clone of {len(repo_list)} repositories...")

        stats = {
            "cloned": 0,
            "failed": 0,
            "skipped": 0,
            "durations": []
        }

        for i, repo in enumerate(repo_list, 1):
            print(f"\n[{i}/{len(repo_list)}/{stats['failed']}] Re-clone: {repo.name}")
            repo_path = repos_path / repo.name
            self.cli.file_operations.safe_remove(repo_path)
            success, message, duration = self.cli.sync_service.sync_single_repository(
                self.cli.current_user,
                repo,
                "clone"
            )

            stats["durations"].append(duration)

            if success:
                print_success(f"{message} ({Helpers.format_duration(duration)})")
                stats["cloned"] += 1
            else:
                print_error(f"Failed: {message}")
                stats["failed"] += 1

        self.cli.show_sync_summary(stats, "Cloning")


    def sync_all_repositories(self):
        clear_screen()
        print_section("SYNC ALL REPOSITORIES")

        structure = self.cli.structure_service.get_user_structure(self.cli.current_user.username)
        if "repositories" not in structure:
            print_error("Storage structure not found")
            return

        repo_list = self.cli.repositories

        print(f"\n{Colors.BOLD}Found {len(repo_list)} repositories:{Colors.END}")
        for i, repo in enumerate(repo_list, 1):
            print(f"  {i}. {repo.name}")

        if not self.cli.ask_yes_no(f"\nSync {len(repo_list)} repositories?"):
            return

        print_info(f"\nStarting sync of {len(repo_list)} repositories...")

        stats = {
            "synced": 0,
            "failed": 0,
            "skipped": 0,
            "durations": []
        }

        for i, repo in enumerate(repo_list, 1):
            print(f"\n[{i}/{len(repo_list)}/{stats['failed']}] Sync: {repo.name}")

            if repo.local_exists:
                success, message, duration = self.cli.sync_service.sync_single_repository(
                    self.cli.current_user,
                    repo,
                    "pull"
                )
            else:
                success, message, duration = self.cli.sync_service.sync_single_repository(
                    self.cli.current_user,
                    repo,
                    "clone"
                )

            stats["durations"].append(duration)

            if success:
                if message == 'Already up to date':
                    print_info(f"{message} ({Helpers.format_duration(duration)})")
                    stats["skipped"] += 1
                else:
                    print_success(f"{message} ({Helpers.format_duration(duration)})")
                    stats["synced"] += 1
            else:
                print_error(f"Failed: {message}")
                stats["failed"] += 1

        self.cli.show_sync_summary(stats, "Cloning")


    def update_needed_repositories(self):
        clear_screen()
        print_section("UPDATE NEEDED REPOSITORIES")

        if not self.cli.current_user or not self.cli.repositories:
            print_error("User or repositories not loaded")
            return

        repo_list = self.cli.get_need_update_repos()

        if not repo_list:
            print('All repositories are up to date...')
            return

        structure = self.cli.structure_service.get_user_structure(self.cli.current_user.username)
        if "repositories" not in structure:
            print_error("Storage structure not found")
            return

        print(f"\n{Colors.BOLD}Found {len(repo_list)} repositories:{Colors.END}")
        for i, repo in enumerate(repo_list, 1):
            print(f"  {i}. {repo.name}")

        if not self.cli.ask_yes_no(f"\nUpdate {len(repo_list)} repositories?"):
            return

        stats = {
            "updated": 0,
            "failed": 0,
            "durations": []
        }

        for i, repo in enumerate(repo_list, 1):
            print(f"\n[{i}/{len(repo_list)}/{stats['failed']}] Sync: {repo.name}")

            success, message, duration = self.cli.sync_service.sync_single_repository(
                self.cli.current_user,
                repo,
                "pull"
            )

            stats["durations"].append(duration)

            if success:
                print_success(f"{message} ({Helpers.format_duration(duration)})")
                stats["updated"] += 1
            else:
                print_error(f"Failed: {message}")
                stats["failed"] += 1

        self.cli.show_sync_summary(stats, "Updating")


    def sync_missing_repositories(self):
        clear_screen()
        print_section("CLONE MISSING REPOSITORIES")

        if not self.cli.current_user or not self.cli.repositories:
            print_error("User or repositories not loaded")
            return

        structure = self.cli.structure_service.get_user_structure(self.cli.current_user.username)
        if "repositories" not in structure:
            print_error("Storage structure not found")
            return

        repos_path = structure["repositories"]
        missing_repos = []

        for repo in self.cli.repositories:
            if not repo.ssh_url:
                continue

            repo_path = repos_path / repo.name
            if not repo_path.exists() or not (repo_path / '.git').exists():
                missing_repos.append(repo)

        if not missing_repos:
            print_success("All repositories are already cloned")
            return

        print(f"\n{Colors.BOLD}Found {len(missing_repos)} missing repositories:{Colors.END}")
        for i, repo in enumerate(missing_repos, 1):
            print(f"  {i}. {repo.name}")

        if not self.cli.ask_yes_no(f"\nClone {len(missing_repos)} missing repositories?"):
            return

        print_info(f"\nStarting cloning of {len(missing_repos)} repositories...")

        stats = {
            "cloned": 0,
            "failed": 0,
            "durations": []
        }

        for i, repo in enumerate(missing_repos, 1):
            print(f"\n[{i}/{len(missing_repos)}/{stats['failed']}] Cloning: {repo.name}")

            success, message, duration = self.cli.sync_service.sync_single_repository(
                self.cli.current_user,
                repo,
                "clone"
            )

            stats["durations"].append(duration)

            if success:
                repo.update_local_status(repos_path)
                self.cli.ui_state.state['local_repositories_count'] += 1
                print_success(f"Cloned successfully ({Helpers.format_duration(duration)})")
                stats["cloned"] += 1
            else:
                print_error(f"Failed: {message}")
                stats["failed"] += 1

        self.cli.show_sync_summary(stats, "Cloning")

    def sync_with_repair(self):
        clear_screen()
        print_section("SYNC WITH REPAIR")

        if not self.cli.current_user or not self.cli.repositories:
            print_error("User or repositories not loaded")
            return

        print_info("This will check and repair broken repositories")
        print_warning("Broken repositories will be re-cloned")

        if not self.cli.ask_yes_no("Continue with repair sync?"):
            return

        structure = self.cli.structure_service.get_user_structure(self.cli.current_user.username)
        if "repositories" not in structure:
            print_error("Storage structure not found")
            return

        repos_path = structure["repositories"]

        broken_repos = []
        for repo in self.cli.repositories:
            if not repo.ssh_url:
                continue

            repo_path = repos_path / repo.name
            if repo_path.exists():
                if not (repo_path / '.git').exists():
                    broken_repos.append(repo)
                else:
                    try:
                        result = subprocess.run(
                            ['git', '-C', str(repo_path), 'rev-parse', '--git-dir'],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode != 0:
                            broken_repos.append(repo)
                    except Exception as e:
                        print(e)
                        broken_repos.append(repo)

        if broken_repos:
            print(f"\n{Colors.BOLD}Found {len(broken_repos)} broken repositories:{Colors.END}")
            for i, repo in enumerate(broken_repos, 1):
                print(f"  {i}. {repo.name}")

        print_info(f"\nStarting repair sync for {len(self.cli.repositories)} repositories...")

        stats = {
            "synced": 0,
            "failed": 0,
            "skipped": 0,
            "durations": []
        }

        for i, repo in enumerate(self.cli.repositories, 1):
            if not repo.ssh_url:
                stats["skipped"] += 1
                continue

            print(f"\n[{i}/{len(self.cli.repositories)}] Processing: {repo.name}")

            success, message, duration = self.cli.sync_service.sync_single_repository(
                self.cli.current_user,
                repo,
                "sync"
            )

            stats["durations"].append(duration)

            if success:
                if "repaired" in message.lower() or "re-cloned" in message.lower():
                    if message == 'Already up to date':
                        print_info(f"{message}: ({Helpers.format_duration(duration)})")
                        stats['skipped'] += 1
                    print_success(f"Repaired: {message} ({Helpers.format_duration(duration)})")
                else:
                    if message == 'Already up to date':
                        print_info(f"Synced: ({Helpers.format_duration(duration)})")
                        stats['skipped'] += 1
                    else:
                        print_success(f"Synced: {message} ({Helpers.format_duration(duration)})")
                    stats["synced"] += 1
            else:
                print_error(f"Failed: {message}")
                stats["failed"] += 1

        self.cli.show_sync_summary(stats, "Repair Sync")
