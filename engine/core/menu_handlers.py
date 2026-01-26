# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import shutil
from datetime import datetime

from engine.utils.decorator import (
    Colors,
    clear_screen,
    print_section,
    print_info,
    Icons,
    print_success,
    print_error,
    wait_for_enter,
    print_menu_item
)
from smart_repository_manager_core.services.config_service import ConfigService
from smart_repository_manager_core.services.github_service import GitHubService
from smart_repository_manager_core.services.ssh_service import SSHService
from smart_repository_manager_core.utils.helpers import Helpers

from engine import __version__ as ver
from engine import __copyright__ as copyright_


class MenuHandlers:
    def __init__(self, cli):
        self.cli = cli

    def show_main_menu(self):
        self.cli.current_menu = "main"

        while self.cli.running:
            clear_screen()
            print_section(f"Smart Repository Manager {ver}")

            if not self.cli.current_user or not self.cli.repositories:
                print_error("User or repositories not loaded.")
                print_info("Please run the full checkup first.")
                wait_for_enter()
                return

            print(f"\n{Colors.BOLD}📊 System Status:{Colors.END}")
            print(f"  • {Icons.USER} User: {Colors.CYAN}{self.cli.current_user.username}{Colors.END}")
            print(f"\n{Colors.BOLD}📊 Repositories Status:{Colors.END}")
            print(
                f"  • {Icons.REPO} Total repositories: {Colors.CYAN}{len(self.cli.repositories)}{Colors.END}")
            print(
                f"  • {Icons.FOLDER} Local repositories: {Colors.CYAN}"
                f"{self.cli.get_local_exist_repos_count()}{Colors.END}")

            if self.cli.ui_state.get('total_public', 0) > 0:
                print(f"  • {Icons.NETWORK} Public repositories: {self.cli.get_public_repos_count()}")

            if self.cli.ui_state.get('total_private', 0) > 0:
                print(f"  • {Icons.LOCK} Private repositories: {self.cli.get_private_repos_count()}")

            if self.cli.ui_state.get('total_archived', 0) > 0:
                print(f"  • {Icons.STORAGE} Archived repositories: {self.cli.ui_state.get('total_archived')}")

            print(f"  • {Icons.SYNC} Needs update: {Colors.YELLOW}"
                  f"{self.cli.get_need_update_repos_count()}{Colors.END}")

            print(f"\n{Colors.BOLD}🚀 Main Commands:{Colors.END}")
            print_menu_item("1", "User Information", Icons.USER)
            print_menu_item("2", "Token Information", Icons.KEY)
            print_menu_item("3", "Repository Management", Icons.REPO)
            print_menu_item("4", "Synchronization", Icons.SYNC)
            print_menu_item("5", "SSH Configuration", Icons.SSH)
            print_menu_item("6", "Storage Management", Icons.STORAGE)
            print_menu_item("7", "System Information", Icons.INFO)

            print(f"\n{Colors.BOLD}⚙️  System:{Colors.END}")
            print_menu_item("8", "Restart", Icons.CHECK)
            print_menu_item("9", " Clean Temporary Files", Icons.DELETE)

            print(f"\n{Colors.BOLD}{Colors.RED}0.{Colors.END} {Icons.EXIT} Exit")
            print('=' * 60)

            choice = self.cli.get_menu_choice("Select option", 0, 9)

            if choice == 0:
                print_success("Goodbye!")

                print_section(f"{copyright_}")

                break
            elif choice == 1:
                self.show_user_info()
            elif choice == 2:
                self.show_token_info()
            elif choice == 3:
                self.cli.show_repository_menu()
            elif choice == 4:
                self.cli.show_sync_menu()
            elif choice == 5:
                self.cli.show_ssh_menu()
            elif choice == 6:
                self.cli.show_storage_menu()
            elif choice == 7:
                self.show_system_info()
            elif choice == 8:
                self.cli.run_full_checkup()
                break
            elif choice == 9:
                self.clean_temp_files()

    def show_user_info(self):
        clear_screen()
        print_section("USER INFORMATION")

        if not self.cli.current_user:
            print_error("No user information available")
            return

        user = self.cli.current_user

        print(f"\n{Colors.BOLD}👤 Profile:{Colors.END}")
        print(f"  • {Icons.USER} Username: {Colors.CYAN}{user.username}{Colors.END}")
        if user.name:
            print(f"  • Name: {user.name}")
        if user.bio:
            print(f"  • Bio: {user.bio}")
        print(f"  • {Icons.GITHUB} Profile: {user.html_url}")

        print(f"\n{Colors.BOLD}📊 Statistics:{Colors.END}")
        print(f"  • {Icons.REPO} Public Repositories: {user.public_repos}")
        print(f"  • {Icons.USER} Followers: {user.followers}")
        print(f"  • {Icons.USER} Following: {user.following}")
        print(f"  • {Icons.CALENDAR} Created: {user.created_date}")

        if self.cli.repositories:
            total = len(self.cli.repositories)
            private_count = sum(1 for r in self.cli.repositories if r.private)

            print(f"\n{Colors.BOLD}📁 Repository Summary:{Colors.END}")
            print(f"  • Total: {total}")
            print(f"  • {Icons.LOCK} Private: {private_count}")
            print(f"  • {Icons.UNLOCK} Public: {total - private_count}")

        wait_for_enter()

    def show_token_info(self):
        clear_screen()
        print_section("TOKEN INFORMATION")

        if not self.cli.current_token:
            print_error("No token available")
            return

        try:
            github_service = GitHubService(self.cli.current_token)
            token_info = github_service.get_token_info()

            print(f"\n{Colors.BOLD}🔑 Token Details:{Colors.END}")
            print(f"  • {Icons.USER} Username: {Colors.CYAN}{token_info.username}{Colors.END}")
            print(f"  • Scopes: {token_info.scopes or 'Not specified'}")
            print(f"  • {Icons.CALENDAR} Created: {token_info.created_at[:10] if token_info.created_at else 'Unknown'}")

            limits = github_service.check_rate_limits()
            print(f"\n{Colors.BOLD}📈 API Limits:{Colors.END}")
            print(f"  • Limit: {limits.get('limit', '?')}")
            print(f"  • Remaining: {limits.get('remaining', '?')}")
            print(f"  • Used: {limits.get('limit', 0) - limits.get('remaining', 0)}")

            if limits.get('reset'):
                try:
                    reset_time = datetime.fromtimestamp(int(limits["reset"]))
                    print(f"  • {Icons.CLOCK} Resets: {reset_time.strftime('%Y-%m-%d %H:%M:%S')}")
                except Exception as e:
                    print(e)

            token_preview = self.cli.current_token if len(
                self.cli.current_token) > 12 else "***"
            print(f"\n{Colors.BOLD}🔐 Token Preview:{Colors.END}")
            print(f"  • {token_preview}")

        except Exception as e:
            print_error(f"Error getting token info: {e}")

        wait_for_enter()

    def show_system_info(self):
        clear_screen()
        print_section("SYSTEM INFORMATION")

        print(f"\n{Colors.BOLD}📊 Application Info:{Colors.END}")
        config_service = ConfigService(self.cli.config_path)
        config = config_service.load_config()

        print(f"  • App Name: {config.app_name}")
        print(f"  • Version: {config.version}")
        print(f"  • Last Launch: {config.last_launch}")
        print(f"  • Config Path: {self.cli.config_path.absolute()}")

        print(f"\n{Colors.BOLD}👤 User Info:{Colors.END}")
        if self.cli.current_user:
            print(f"  • Username: @{self.cli.current_user.username}")
            if self.cli.current_user.name:
                print(f"  • Name: {self.cli.current_user.name}")
            print(f"  • Public Repos: {self.cli.current_user.public_repos}")
            print(f"  • Followers: {self.cli.current_user.followers}")
            print(f"  • Following: {self.cli.current_user.following}")
            print(f"  • Created: {self.cli.current_user.created_date}")

        print(f"\n{Colors.BOLD}📁 Repository Stats:{Colors.END}")
        print(f"  • Total: {len(self.cli.repositories)}")
        print(f"  • Local: {self.cli.ui_state.get('local_repositories_count', 0)}")
        print(f"  • Needs Update: {self.cli.ui_state.get('needs_update_count', 0)}")
        print(f"  • Private: {self.cli.ui_state.get('total_private', 0)}")
        print(f"  • Archived: {self.cli.ui_state.get('total_archived', 0)}")
        print(f"  • Forks: {self.cli.ui_state.get('total_forks', 0)}")

        print(f"\n{Colors.BOLD}🔐 SSH Status:{Colors.END}")
        ssh = SSHService()
        validation = ssh.validate_ssh_configuration()
        print(f"  • Status: {validation.status.value}")
        print(f"  • Can Clone: {'✓' if validation.can_clone_with_ssh else '✗'}")
        print(f"  • Can Pull: {'✓' if validation.can_pull_with_ssh else '✗'}")
        print(f"  • GitHub Auth: {'✓' if validation.github_authentication_working else '✗'}")

        wait_for_enter()

    def clean_temp_files(self):
        clear_screen()
        print_section("CLEAN TEMPORARY FILES")

        if not self.cli.current_user:
            print_error("No user selected")
            return

        structure = self.cli.structure_service.get_user_structure(self.cli.current_user.username)

        if "temp" not in structure:
            print_info("No temp directory exists")
            return

        temp_dir = structure["temp"]

        if not temp_dir.exists():
            print_info("Temp directory is empty")
            return

        file_count = 0
        total_size = 0

        for item in temp_dir.iterdir():
            if item.is_file():
                file_count += 1
                total_size += item.stat().st_size

        if file_count == 0:
            print_success("No temporary files to clean")
            return

        size_str = Helpers.format_size(total_size)
        print(f"Found {file_count} temporary files ({size_str})")

        if not self.cli.ask_yes_no("Clean temporary files?"):
            return

        try:
            removed_count = 0

            for item in temp_dir.iterdir():
                try:
                    if item.is_file():
                        item.unlink()
                        removed_count += 1
                    elif item.is_dir():
                        shutil.rmtree(item)
                        removed_count += 1
                except Exception as e:
                    print(e)
                    pass

            print_success(f"Cleaned {removed_count} files/directories")

        except Exception as e:
            print_error(f"Error cleaning files: {e}")

        wait_for_enter()
