# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import shutil
from typing import Dict, Any

from engine.utils.decorator import (
    Colors,
    clear_screen,
    print_section,
    print_info,
    Icons,
    print_success,
    print_error,
    print_warning,
    wait_for_enter,
    print_menu_item
)

class StorageManager:
    def __init__(self, cli):
        self.cli = cli

    def show_storage_menu(self):
        self.cli.menu_stack.append(self.cli.current_menu)
        self.cli.current_menu = "storage"

        while self.cli.current_menu == "storage":
            clear_screen()
            print_section("STORAGE MANAGEMENT")

            storage_info = self.get_storage_info()

            print(f"\n{Colors.BOLD}💾 Local Storage:{Colors.END}")
            if 'error' in storage_info:
                print_error(f"Error: {storage_info['error']}")
            else:
                size_mb = storage_info.get('total_size_mb', 0)
                repo_count = storage_info.get('repo_count', 0)
                exists = storage_info.get('exists', False)

                print(f"  • Path: {storage_info.get('path', 'N/A')}")
                print(f"  • Exists: {'✓' if exists else '✗'}")
                print(f"  • Size: {size_mb:.2f} MB")
                print(f"  • Repositories: {repo_count}")

            print(f"\n{Colors.BOLD}🗑️ Commands:{Colors.END}")
            print_menu_item("1", "Delete Repository", Icons.DELETE)
            print_menu_item("2", "Delete All Repos", Icons.DELETE)
            print_menu_item("3", "Storage Information", Icons.INFO)

            print(f"\n{Colors.BOLD}{Colors.BLUE}0.{Colors.END} {Icons.BACK} Back")
            print('=' * 60)

            choice = self.cli.get_menu_choice("Select option", 0, 3)

            if choice == 0:
                self.cli.current_menu = self.cli.menu_stack.pop()
            elif choice == 1:
                self.delete_local_repository()
            elif choice == 2:
                self.delete_all_repositories()
            elif choice == 3:
                self.show_storage_info()

            if choice != 0:
                wait_for_enter()

    def get_storage_info(self) -> Dict[str, Any]:
        if not self.cli.current_user:
            return {"error": "No user selected"}

        structure = self.cli.structure_service.get_user_structure(self.cli.current_user.username)
        if "repositories" not in structure:
            return {"error": "Storage structure not found"}

        repos_path = structure["repositories"]

        info = {
            "path": str(repos_path),
            "exists": repos_path.exists(),
            "repo_count": 0,
            "total_size_mb": 0
        }

        if repos_path.exists():
            try:
                repo_count = 0
                total_size = 0

                for item in repos_path.iterdir():
                    if item.is_dir():
                        repo_count += 1
                        for file in item.rglob('*'):
                            if file.is_file():
                                total_size += file.stat().st_size

                info["repo_count"] = repo_count
                info["total_size_mb"] = total_size / (1024 * 1024)

            except Exception as e:
                info["error"] = str(e)

        return info

    def delete_local_repository(self):
        clear_screen()
        print_section("DELETE LOCAL REPOSITORY")

        if not self.cli.current_user:
            print_error("No user selected")
            return

        structure = self.cli.structure_service.get_user_structure(self.cli.current_user.username)
        if "repositories" not in structure:
            print_error("Storage structure not found")
            return

        repos_path = structure["repositories"]

        local_repos = []
        for repo in self.cli.repositories:
            repo_path = repos_path / repo.name
            if repo_path.exists():
                local_repos.append(repo)

        if not local_repos:
            print_info("No local repositories found")
            return

        print(f"\n{Colors.BOLD}Local repositories ({len(local_repos)}):{Colors.END}")
        for i, repo in enumerate(local_repos, 1):
            print(f"  {i}. {repo.name}")

        choice = self.cli.get_menu_choice("\nSelect repository to delete (0 to cancel)", 0, len(local_repos))

        if choice == 0:
            print_info("Deletion cancelled")
            return

        repo_name = local_repos[choice - 1].name

        if not self.cli.ask_yes_no(f"{Colors.RED}Delete repository '{repo_name}'? This cannot be undone!{Colors.END}"):
            print_info("Deletion cancelled")
            return

        repo_path = repos_path / repo_name

        try:
            if repo_path.exists():
                shutil.rmtree(repo_path)
                print_success(f"Repository '{repo_name}' deleted successfully")

                for repo in self.cli.repositories:
                    if repo.name == repo_name:
                        repo.local_exists = False
                        repo.need_update = True
                        break
            else:
                print_error(f"Repository '{repo_name}' not found")
        except Exception as e:
            print_error(f"Error deleting repository: {e}")

    def delete_all_repositories(self):
        clear_screen()
        print_section("DELETE ALL REPOSITORIES")

        if not self.cli.current_user:
            print_error("No user selected")
            return

        storage_info = self.get_storage_info()
        repo_count = storage_info.get('repo_count', 0)

        if repo_count == 0:
            print_info("No local repositories found")
            return

        size_mb = storage_info.get('total_size_mb', 0)

        print_warning(f"⚠️ WARNING: This will delete ALL local repositories!")
        print_warning(f"    • Count: {repo_count} repositories")
        print_warning(f"    • Size: {size_mb:.2f} MB")
        print_warning("    • This action cannot be undone!")

        confirm = input(f"\n{Colors.RED}Type 'DELETE-ALL' to confirm (Press Enter to exit): {Colors.END}").strip()
        if confirm != 'DELETE-ALL':
            print_info("Deletion cancelled")
            return

        structure = self.cli.structure_service.get_user_structure(self.cli.current_user.username)
        if "repositories" not in structure:
            print_error("Storage structure not found")
            return

        repos_path = structure["repositories"]

        deleted_count = 0
        if repos_path.exists():
            try:
                for item in repos_path.iterdir():
                    if item.is_dir():
                        shutil.rmtree(item, ignore_errors=True)
                        deleted_count += 1

                print_success(f"Deleted {deleted_count} repositories")

                for repo in self.cli.repositories:
                    repo.local_exists = False
                    repo.need_update = True

            except Exception as e:
                print_error(f"Error deleting repositories: {e}")
        else:
            print_info("No repositories to delete")

    def show_storage_info(self):
        clear_screen()
        print_section("STORAGE INFORMATION")

        storage_info = self.get_storage_info()

        if 'error' in storage_info:
            print_error(f"Error: {storage_info['error']}")
            return

        print(f"\n{Colors.BOLD}Storage Details:{Colors.END}")
        print(f"  • Path: {storage_info.get('path', 'N/A')}")
        print(f"  • Exists: {'✓' if storage_info.get('exists') else '✗'}")
        print(f"  • Size: {storage_info.get('total_size_mb', 0):.2f} MB")
        print(f"  • Repositories: {storage_info.get('repo_count', 0)}")

        if storage_info.get('exists') and storage_info.get('repo_count', 0) > 0:
            avg_size = storage_info.get('total_size_mb', 0) / max(1, storage_info.get('repo_count', 1))
            print(f"  • Average per repo: {avg_size:.2f} MB")

        print(f"\n{Colors.BOLD}Additional Information:{Colors.END}")
        print(f"  • 1 MB = 1024 KB")
        print(f"  • 1 GB = 1024 MB")
