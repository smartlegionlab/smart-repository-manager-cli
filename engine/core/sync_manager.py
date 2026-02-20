# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import concurrent
import subprocess
import threading
import time
import json
from pathlib import Path
from datetime import datetime

from smart_repository_manager_core.services.download_service import DownloadService

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


class SyncManager:
    def __init__(self, cli):
        self.cli = cli
        self.download_service = DownloadService()
        self._stop_download = False

    def show_sync_menu(self):
        self.cli.menu_stack.append(self.cli.current_menu)
        self.cli.current_menu = "sync"

        while self.cli.current_menu == "sync":
            clear_screen()
            print_section("SYNCHRONIZATION")

            print(f"\n{Colors.BOLD}📊 Status:{Colors.END}")
            print(f"  • Total repositories: {len(self.cli.repositories)}")
            print(f"  • Local repositories: {self.cli.get_local_exist_repos_count()}")
            print(f"  • Needs update: {self.cli.get_need_update_repos_count()}")

            print(f"\n{Colors.BOLD}🔄 Git Operations:{Colors.END}")
            print_menu_item("1", "Synchronize All (Git Clone/Pull)", Icons.SYNC)
            print_menu_item("2", "Update Needed Only (Git Pull)", Icons.SYNC)
            print_menu_item("3", "Clone Missing Only (Git Clone)", Icons.DOWNLOAD)
            print_menu_item("4", "Sync with Repair", Icons.SETTINGS)
            print_menu_item("5", "Re-clone All (Git Clone)", Icons.SETTINGS)

            print(f"\n{Colors.BOLD}📦 Download Operations (ZIP):{Colors.END}")
            print_menu_item("6", "Download All Repositories", Icons.DOWNLOAD)
            print_menu_item("7", "Download Single Repository", Icons.DOWNLOAD)

            print(f"\n{Colors.BOLD}{Colors.BLUE}0.{Colors.END} {Icons.BACK} Back")
            print('=' * 60)

            choice = self.cli.get_menu_choice("Select option", 0, 7)

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
            elif choice == 6:
                self.download_all_repositories()
            elif choice == 7:
                self.download_single_repository()

            if choice != 0:
                wait_for_enter()

    def _get_logs_dir(self) -> Path:
        if not self.cli.current_user:
            return Path.home() / "smart_repository_manager" / "logs" / "sync"

        return Path.home() / "smart_repository_manager" / self.cli.current_user.username / "logs" / "sync"

    def _save_sync_log(self, operation_name: str, stats: dict):
        logs_dir = self._get_logs_dir()
        logs_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_op_name = operation_name.lower().replace(" ", "_")
        log_file = logs_dir / f"{safe_op_name}_{timestamp}.json"

        clean_stats = {k: v for k, v in stats.items() if k != 'durations'}

        if 'results' in clean_stats and clean_stats['results']:
            for result in clean_stats['results']:
                if 'duration' in result:
                    del result['duration']

        log_data = {
            "operation": operation_name,
            "timestamp": datetime.now().isoformat(),
            "username": self.cli.current_user.username if self.cli.current_user else "unknown",
            "statistics": clean_stats,
            "repositories_total": len(self.cli.repositories) if self.cli.repositories else 0,
            "repositories_local": self.cli.get_local_exist_repos_count() if self.cli.current_user else 0,
            "repositories_needs_update": self.cli.get_need_update_repos_count() if self.cli.current_user else 0
        }

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, indent=2, ensure_ascii=False)

        print_info(f"\n📝 Log saved: {log_file}")

    def _show_progress(self, completed: int, total: int, current_item: str, operation: str = "Processing"):
        progress_pct = (completed / total) * 100
        bar_length = 40
        filled_length = int(bar_length * completed // total)
        bar = '█' * filled_length + '░' * (bar_length - filled_length)

        status_color = Colors.GREEN if completed == total else Colors.CYAN

        print(
            f"\r{status_color}{operation}: |{bar}| {completed}/{total} ({progress_pct:.1f}%) - Current: {current_item}{Colors.END}",
            end='', flush=True)

        if completed == total:
            print()

    def download_all_repositories(self):
        clear_screen()
        print_section("DOWNLOAD ALL REPOSITORIES")

        if not self.cli.current_user or not self.cli.repositories:
            print_error("User or repositories not loaded")
            return

        cpu_count = getattr(self.download_service, 'cpu_count', 4)
        repo_workers = max(1, cpu_count - 1)

        print(f"\n{Colors.BOLD}📊 Download Information:{Colors.END}")
        print(f"  • User: {Colors.CYAN}{self.cli.current_user.username}{Colors.END}")
        print(f"  • Repositories to download: {len(self.cli.repositories)}")
        print(f"  • Download mode: {Colors.GREEN}ALL BRANCHES for each repo{Colors.END}")
        print(f"  • CPU cores detected: {cpu_count}")
        print(f"  • Repo downloads: {repo_workers} threads")
        print(f"  • Internal branch downloads: auto (per repo)")
        print(f"  • Download directory: {self.download_service.get_user_downloads_dir(self.cli.current_user.username)}")
        print(
            f"\n{Colors.YELLOW}⚠️  Warning: This will download ALL repositories with ALL branches as ZIP archives.{Colors.END}")
        print(f"{Colors.YELLOW}   This may take a long time and use significant disk space.{Colors.END}")

        if not self.cli.ask_yes_no("Continue with download?"):
            return

        print(
            f"\n{Colors.YELLOW}Starting download of {len(self.cli.repositories)} repositories...{Colors.END}")
        print_info(f"Using {repo_workers} workers for repository downloads\n")

        self._stop_download = False

        stats = {
            "downloaded": 0,
            "failed": 0,
            "skipped": 0,
            "total_size_mb": 0,
            "total_branches": 0,
            "results": [],
            "total": len(self.cli.repositories),
            "successful": 0
        }

        lock = threading.Lock()
        completed = 0

        def download_single_repo(repo):
            if self._stop_download:
                return {
                    'repo': repo.name,
                    'success': False,
                    'error': 'Download stopped by user',
                    'skipped': True
                }

            if not repo.html_url:
                return {
                    'repo': repo.name,
                    'success': False,
                    'error': 'No URL available',
                    'skipped': True
                }

            start_time = time.time()

            try:
                result = self.download_service.download_repository_with_all_branches(
                    repo_name=repo.name,
                    repo_url=repo.html_url,
                    token=self.cli.current_token,
                    username=self.cli.current_user.username,
                    verbose=False
                )

                repo_result = {
                    'repo': repo.name,
                    'success': result.get('success', False),
                    'result': result,
                    'is_private': getattr(repo, 'private', False)
                }

                return repo_result

            except Exception as e:
                return {
                    'repo': repo.name,
                    'success': False,
                    'error': str(e),
                    'is_private': getattr(repo, 'private', False)
                }

        with concurrent.futures.ThreadPoolExecutor(max_workers=repo_workers) as executor:
            future_to_repo = {
                executor.submit(download_single_repo, repo): repo
                for repo in self.cli.repositories
            }

            try:
                for future in concurrent.futures.as_completed(future_to_repo):
                    if self._stop_download:
                        for f in future_to_repo:
                            f.cancel()
                        break

                    repo = future_to_repo[future]

                    try:
                        repo_result = future.result(timeout=300)

                        with lock:
                            completed += 1
                            stats['results'].append(repo_result)

                            self._show_progress(completed, len(self.cli.repositories), repo.name, "Downloading")

                            if repo_result.get('success'):
                                successful_branches = repo_result.get('result', {}).get('successful', 0)
                                total_branches = repo_result.get('result', {}).get('total_branches', 0)
                                size_mb = repo_result.get('result', {}).get('total_size_bytes', 0) / (1024 * 1024)

                                stats['downloaded'] += 1
                                stats['successful'] += 1
                                stats['total_branches'] += successful_branches
                                stats['total_size_mb'] += size_mb

                                print_success(
                                    f"\n✓ {repo.name}: {successful_branches}/{total_branches} branches "
                                    f"({size_mb:.2f} MB)"
                                )
                            else:
                                stats['failed'] += 1
                                error_msg = repo_result.get('error', 'Unknown error')
                                print_error(f"\n✗ {repo.name}: {error_msg}")

                    except concurrent.futures.TimeoutError:
                        with lock:
                            completed += 1
                            stats['failed'] += 1
                            print_error(f"\n✗ {repo.name}: Download timeout after 5 minutes")

                    except Exception as e:
                        with lock:
                            completed += 1
                            stats['failed'] += 1
                            print_error(f"\n✗ {repo.name}: {str(e)}")

            except KeyboardInterrupt:
                print_warning("\n\nDownload interrupted by user")
                self._stop_download = True
                for future in future_to_repo:
                    future.cancel()

        self._show_download_summary(stats)
        self._save_sync_log("Download All Repositories", stats)

        if stats["downloaded"] > 0 and self.cli.ask_yes_no("Open downloads folder?"):
            downloads_dir = self.download_service.get_user_downloads_dir(self.cli.current_user.username)
            self.cli.open_folder(downloads_dir)

    def _show_download_summary(self, stats):
        print(f"\n\n{Colors.BOLD}{'=' * 60}{Colors.END}")
        print(f"{Colors.BOLD}DOWNLOAD SUMMARY{Colors.END}")
        print(f"{Colors.BOLD}{'=' * 60}{Colors.END}")

        print(f"\n{Colors.BOLD}📊 Results:{Colors.END}")
        print(f"  {Icons.SUCCESS} Repositories downloaded: {stats['downloaded']}")
        print(f"  {Icons.ERROR} Failed: {stats['failed']}")
        print(f"  {Icons.INFO} Skipped: {stats['skipped']}")
        print(f"  {Icons.STORAGE} Total branches: {stats['total_branches']}")
        print(f"  {Icons.STORAGE} Total size: {stats['total_size_mb']:.2f} MB")

        failed_results = [r for r in stats['results'] if not r.get('success')]
        if failed_results:
            print(f"\n{Colors.BOLD}{Colors.RED}Failed downloads:{Colors.END}")
            for result in failed_results[:5]:
                print(f"  • {result['repo']}: {result.get('error', 'Unknown error')}")
            if len(failed_results) > 5:
                print(f"  • ... and {len(failed_results) - 5} more")

    def download_single_repository(self):
        clear_screen()
        print_section("DOWNLOAD SINGLE REPOSITORY")

        if not self.cli.current_user or not self.cli.repositories:
            print_error("User or repositories not loaded")
            return

        print(f"\n{Colors.BOLD}Available repositories:{Colors.END}")
        for i, repo in enumerate(self.cli.repositories, 1):
            print(f"  {i}. {repo.name}")

        choice = self.cli.get_menu_choice(f"\nSelect repository (0 to cancel)", 0, len(self.cli.repositories))

        if choice == 0:
            return

        repo = self.cli.repositories[choice - 1]

        clear_screen()
        print_section(f"DOWNLOAD: {repo.name}")

        cpu_count = getattr(self.download_service, 'cpu_count', 'N/A')
        max_workers = getattr(self.download_service, 'max_workers', 'N/A')

        print(f"\n{Colors.BOLD}Repository Information:{Colors.END}")
        print(f"  • Name: {repo.name}")
        print(f"  • Default branch: {repo.default_branch or 'main'}")
        print(f"  • Private: {'Yes' if repo.private else 'No'}")
        print(f"  • URL: {repo.html_url}")
        print(f"\n{Colors.BOLD}Download Information:{Colors.END}")
        print(f"  • Mode: {Colors.GREEN}ALL BRANCHES{Colors.END}")
        print(f"  • CPU cores: {cpu_count}")
        print(f"  • Internal parallel workers: {max_workers}")

        if not self.cli.ask_yes_no(f"\nDownload {repo.name} with all branches?"):
            return

        print(f"\n{Colors.YELLOW}Downloading all branches...{Colors.END}")

        try:
            result = self.download_service.download_repository_with_all_branches(
                repo_name=repo.name,
                repo_url=repo.html_url,
                token=self.cli.current_token,
                username=self.cli.current_user.username,
                verbose=True
            )

            if result.get("success"):
                successful = result.get("successful", 0)
                total = result.get("total_branches", 0)
                size_mb = result.get("total_size_bytes", 0) / (1024 * 1024)
                workers = result.get("workers_used", 'N/A')

                print_success(f"\n✓ Successfully downloaded {successful}/{total} branches!")
                print(f"\n{Colors.BOLD}Download Details:{Colors.END}")
                print(f"  • Directory: {result.get('download_dir')}")
                print(f"  • Total size: {size_mb:.2f} MB")
                print(f"  • Internal workers used: {workers}")

                if result.get('results'):
                    print(f"\n{Colors.BOLD}Downloaded branches:{Colors.END}")
                    branches = []
                    for branch_result in result.get('results', []):
                        if branch_result['result'].get('success'):
                            branch_name = branch_result['branch']
                            branch_size = branch_result['result'].get('size_bytes', 0) / (1024 * 1024)
                            branches.append((branch_name, branch_size))

                    branches.sort(key=lambda x: x[1], reverse=True)

                    for branch_name, branch_size in branches:
                        print(f"  • {branch_name}: {branch_size:.2f} MB")

                stats = {
                    "total": 1,
                    "successful": 1,
                    "failed": 0,
                    "skipped": 0,
                    "downloaded": 1,
                    "total_branches": successful,
                    "total_size_mb": size_mb,
                    "repository_name": repo.name,
                    "repository_url": repo.html_url,
                    "is_private": repo.private,
                    "branch_details": branches if 'branches' in locals() else []
                }
                self._save_sync_log(f"Download Single Repository - {repo.name}", stats)

                if self.cli.ask_yes_no("Open downloads folder?"):
                    downloads_dir = Path(result.get('download_dir', ''))
                    self.cli.open_folder(downloads_dir)
            else:
                print_error(f"\n✗ Download failed: {result.get('error', 'Unknown error')}")

                stats = {
                    "total": 1,
                    "successful": 0,
                    "failed": 1,
                    "skipped": 0,
                    "repository_name": repo.name,
                    "repository_url": repo.html_url,
                    "error": result.get('error', 'Unknown error')
                }
                self._save_sync_log(f"Download Single Repository - {repo.name} (FAILED)", stats)

        except Exception as e:
            print_error(f"\n✗ Error: {e}")

            stats = {
                "total": 1,
                "successful": 0,
                "failed": 1,
                "skipped": 0,
                "repository_name": repo.name,
                "repository_url": repo.html_url,
                "error": str(e)
            }
            self._save_sync_log(f"Download Single Repository - {repo.name} (ERROR)", stats)

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
            "total": len(repo_list),
            "successful": 0,
            "results": []
        }

        for i, repo in enumerate(repo_list, 1):
            print(f"\n[{i}/{len(repo_list)}] Re-clone: {repo.name}")
            self._show_progress(i, len(repo_list), repo.name, "Re-cloning")

            repo_path = repos_path / repo.name
            self.cli.file_operations.safe_remove(repo_path)

            success, message, _ = self.cli.sync_service.sync_single_repository(
                self.cli.current_user,
                repo,
                "clone"
            )

            result = {
                "repo": repo.name,
                "success": success,
                "message": message
            }
            stats["results"].append(result)

            if success:
                print_success(f"✓ {message}")
                stats["cloned"] += 1
                stats["successful"] += 1
            else:
                print_error(f"✗ Failed: {message}")
                stats["failed"] += 1

        self.cli.show_sync_summary(stats, "Re-cloning")
        self._save_sync_log("Re-clone All Repositories", stats)

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
            "total": len(repo_list),
            "successful": 0,
            "results": []
        }

        for i, repo in enumerate(repo_list, 1):
            print(f"\n[{i}/{len(repo_list)}] Sync: {repo.name}")
            self._show_progress(i, len(repo_list), repo.name, "Syncing")

            if repo.local_exists:
                success, message, _ = self.cli.sync_service.sync_single_repository(
                    self.cli.current_user,
                    repo,
                    "pull"
                )
            else:
                success, message, _ = self.cli.sync_service.sync_single_repository(
                    self.cli.current_user,
                    repo,
                    "clone"
                )

            result = {
                "repo": repo.name,
                "success": success,
                "message": message,
                "action": "pull" if repo.local_exists else "clone"
            }
            stats["results"].append(result)

            if success:
                if message == 'Already up to date':
                    print_info(f"  {message}")
                    stats["skipped"] += 1
                else:
                    print_success(f"✓ {message}")
                    stats["synced"] += 1
                    stats["successful"] += 1
            else:
                print_error(f"✗ Failed: {message}")
                stats["failed"] += 1

        self.cli.show_sync_summary(stats, "Sync")
        self._save_sync_log("Sync All Repositories", stats)

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
            "total": len(repo_list),
            "successful": 0,
            "results": []
        }

        for i, repo in enumerate(repo_list, 1):
            print(f"\n[{i}/{len(repo_list)}] Updating: {repo.name}")
            self._show_progress(i, len(repo_list), repo.name, "Updating")

            success, message, _ = self.cli.sync_service.sync_single_repository(
                self.cli.current_user,
                repo,
                "pull"
            )

            result = {
                "repo": repo.name,
                "success": success,
                "message": message
            }
            stats["results"].append(result)

            if success:
                print_success(f"✓ {message}")
                stats["updated"] += 1
                stats["successful"] += 1
            else:
                print_error(f"✗ Failed: {message}")
                stats["failed"] += 1

        self.cli.show_sync_summary(stats, "Updating")
        self._save_sync_log("Update Needed Repositories", stats)

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
            "total": len(missing_repos),
            "successful": 0,
            "results": []
        }

        for i, repo in enumerate(missing_repos, 1):
            print(f"\n[{i}/{len(missing_repos)}] Cloning: {repo.name}")
            self._show_progress(i, len(missing_repos), repo.name, "Cloning")

            success, message, _ = self.cli.sync_service.sync_single_repository(
                self.cli.current_user,
                repo,
                "clone"
            )

            result = {
                "repo": repo.name,
                "success": success,
                "message": message
            }
            stats["results"].append(result)

            if success:
                repo.update_local_status(repos_path)
                self.cli.ui_state.state['local_repositories_count'] += 1
                print_success(f"✓ Cloned successfully")
                stats["cloned"] += 1
                stats["successful"] += 1
            else:
                print_error(f"✗ Failed: {message}")
                stats["failed"] += 1

        self.cli.show_sync_summary(stats, "Cloning")
        self._save_sync_log("Clone Missing Repositories", stats)

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
            "repaired": 0,
            "total": len(self.cli.repositories),
            "successful": 0,
            "results": []
        }

        for i, repo in enumerate(self.cli.repositories, 1):
            if not repo.ssh_url:
                stats["skipped"] += 1
                continue

            print(f"\n[{i}/{len(self.cli.repositories)}] Processing: {repo.name}")
            self._show_progress(i, len(self.cli.repositories), repo.name, "Repairing")

            success, message, _ = self.cli.sync_service.sync_single_repository(
                self.cli.current_user,
                repo,
                "sync"
            )

            result = {
                "repo": repo.name,
                "success": success,
                "message": message,
                "was_broken": repo in broken_repos
            }
            stats["results"].append(result)

            if success:
                if "repaired" in message.lower() or "re-cloned" in message.lower():
                    stats["repaired"] += 1
                    stats["successful"] += 1
                    if message == 'Already up to date':
                        print_info(f"  {message}")
                        stats['skipped'] += 1
                    else:
                        print_success(f"✓ Repaired: {message}")
                else:
                    if message == 'Already up to date':
                        print_info(f"  Synced")
                        stats['skipped'] += 1
                    else:
                        print_success(f"✓ Synced: {message}")
                        stats["synced"] += 1
                        stats["successful"] += 1
            else:
                print_error(f"✗ Failed: {message}")
                stats["failed"] += 1

        self.cli.show_sync_summary(stats, "Repair Sync")
        self._save_sync_log("Sync with Repair", stats)
