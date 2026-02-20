# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import shutil
from datetime import datetime

from engine.utils.text_decorator import (
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
            print_menu_item("9", " Clean Log Files", Icons.DELETE)

            print_menu_item("10", "Help / Quick Guide", Icons.INFO)
            print_menu_item("11", "About", Icons.INFO)

            print(f"\n{Colors.BOLD}{Colors.RED}0.{Colors.END} {Icons.EXIT} Exit")
            print('=' * 60)

            choice = self.cli.get_menu_choice("Select option", 0, 11)

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
                self.clean_log_files()
            elif choice == 10:
                self.show_help()
            elif choice == 11:
                self.show_about()

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

    def clean_log_files(self):
        clear_screen()
        print_section("CLEAN LOG FILES")

        if not self.cli.current_user:
            print_error("No user selected")
            return

        structure = self.cli.structure_service.get_user_structure(self.cli.current_user.username)

        if "logs" not in structure:
            print_info('No "logs" directory exists')
            return

        log_dir = structure["logs"]

        if not log_dir.exists():
            print_info("Log directory is empty...")
            wait_for_enter()
            return

        files = []
        total_size = 0

        for item in log_dir.iterdir():
            try:
                if item.is_file():
                    stat = item.stat()
                    files.append({
                        'path': item,
                        'name': item.name,
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'is_dir': False
                    })
                    total_size += stat.st_size
                elif item.is_dir():
                    dir_size = 0
                    file_count = 0
                    try:
                        for dir_item in item.rglob('*'):
                            try:
                                if dir_item.is_file():
                                    dir_size += dir_item.stat().st_size
                                    file_count += 1
                            except (PermissionError, OSError):
                                continue
                    except (PermissionError, OSError):
                        dir_size = 0
                        file_count = 0

                    stat = item.stat()
                    files.append({
                        'path': item,
                        'name': item.name,
                        'size': dir_size,
                        'modified': stat.st_mtime,
                        'is_dir': True,
                        'file_count': file_count
                    })
                    total_size += dir_size
            except Exception as e:
                print(e)
                continue

        if not files:
            print_success("No log files to clean")
            wait_for_enter()
            return

        files.sort(key=lambda x: x['modified'], reverse=True)

        file_count = len(files)
        size_str = Helpers.format_size(total_size)
        print(f"Found {file_count} log files and directories ({size_str})")
        print()

        print("LAST 10 LOG FILES/DIRECTORIES:")
        print()

        for i, file_info in enumerate(files[:10], 1):
            from datetime import datetime
            modified_dt = datetime.fromtimestamp(file_info['modified'])
            time_str = modified_dt.strftime("%Y-%m-%d %H:%M:%S")

            size_str = Helpers.format_size(file_info['size'])

            if file_info['is_dir']:
                type_indicator = "[DIR]"
                extra_info = f" ({file_info['file_count']} files)"
            else:
                type_indicator = "[FILE]"
                extra_info = ""

            print(f"  {i:2}. {type_indicator} {file_info['name']}")
            print(f"       Size: {size_str:>8} | Modified: {time_str}{extra_info}")
            print()

        if len(files) > 10:
            remaining = len(files) - 10
            print_info(f"... and {remaining} more files/directories")
            print()

        if not self.cli.ask_yes_no(f"Clean ALL {file_count} log files and directories?"):
            return

        print()
        print("CLEANING IN PROGRESS...")
        print()

        try:
            removed_count = 0
            errors = []

            for i, file_info in enumerate(files, 1):
                item = file_info['path']
                name = file_info['name']

                try:
                    if file_info['is_dir']:
                        shutil.rmtree(item)
                        status = "✓"
                    else:
                        item.unlink()
                        status = "✓"

                    removed_count += 1

                    size_str = Helpers.format_size(file_info['size'])
                    if file_info['is_dir']:
                        type_info = "directory"
                        file_info_text = f"with {file_info['file_count']} files"
                    else:
                        type_info = "file"
                        file_info_text = f"size: {size_str}"

                    print(f"  [{i:3}/{len(files):3}] {status} Removing {type_info}: {name} ({file_info_text})")

                except Exception as e:
                    errors.append(f"{name}: {str(e)}")
                    print(f"  [{i:3}/{len(files):3}] ✗ Error removing: {name}")
                    print(f"       Error: {str(e)}")

            print()

            if removed_count > 0:
                cleaned_size = sum(f['size'] for f in files[:removed_count])
                size_str = Helpers.format_size(cleaned_size)
                print_success(f"Cleaned {removed_count} files/directories ({size_str} freed)")

            if errors:
                print(f"Failed to remove {len(errors)} items:")
                for error in errors[:5]:
                    print(f"  • {error}")
                if len(errors) > 5:
                    print(f"  ... and {len(errors) - 5} more errors")

        except Exception as e:
            print_error(f"Error cleaning files: {e}")

        wait_for_enter()

    def show_help(self):
            clear_screen()
            print_section("HELP / QUICK GUIDE")

            help_text = f"""
    {Colors.BOLD}Smart Repository Manager CLI - Quick Guide{Colors.END}

    {Colors.BOLD}Main Concepts:{Colors.END}
      • The tool organizes your repositories by GitHub user.
      • All data is stored in: {Colors.CYAN}~/smart_repository_manager/[username]/{Colors.END}
      • SSH is the recommended way to interact with GitHub.

    {Colors.BOLD}First Time Setup:{Colors.END}
      1. Run the tool. It will start a 'Full System Checkup'.
      2. When prompted, enter your {Colors.YELLOW}GitHub Personal Access Token (PAT){Colors.END}.
         (Create one at https://github.com/settings/tokens with 'repo' scope)
      3. The tool will guide you through SSH setup if needed.
      4. After the checkup, you'll see the main menu.

    {Colors.BOLD}Common Workflows:{Colors.END}
      • {Colors.BOLD}Synchronize All Repos:{Colors.END} Go to {Colors.CYAN}Synchronization -> Sync All{Colors.END}
      • {Colors.BOLD}Check SSH Status:{Colors.END} Go to {Colors.CYAN}SSH Configuration{Colors.END}
      • {Colors.BOLD}Find a Repository:{Colors.END} Go to {Colors.CYAN}Repository Management -> Search{Colors.END}
      • {Colors.BOLD}Free Up Disk Space:{Colors.END} Go to {Colors.CYAN}Storage Management{Colors.END}

    {Colors.BOLD}Troubleshooting:{Colors.END}
      • If sync fails, check {Colors.CYAN}SSH Configuration -> Test Connection{Colors.END}
      • If you see API errors, check {Colors.CYAN}Token Information{Colors.END} for rate limits.
      • For broken repositories, use {Colors.CYAN}Synchronization -> Sync with Repair{Colors.END}
      • Run a full {Colors.CYAN}Restart{Colors.END} (option 8) to re-run the system checkup.
    """
            print(help_text)
            wait_for_enter()

    def show_about(self):
        clear_screen()
        print_section("ABOUT")

        about_text = f"""
{Colors.BOLD}Smart Repository Manager CLI{Colors.END}
Version: {ver}
{Colors.BOLD}A comprehensive tool for managing GitHub repositories.{Colors.END}

{Colors.BOLD}Key Features:{Colors.END}
  • 🔄 Intelligent Sync: Automatically clones missing and updates existing repos.
  • 🔐 SSH Management: Complete toolkit for SSH key generation and configuration.
  • 📊 Repository Insights: Language stats, health checks, and storage monitoring.
  • 🗂️ Multi-User Support: Switch between different GitHub accounts seamlessly.

{Colors.BOLD}Developed by:{Colors.END} Alexander Suvorov
{Colors.BOLD}License:{Colors.END} BSD 3-Clause
{Colors.BOLD}Copyright:{Colors.END} {copyright_}

{Colors.BOLD}Project Links:{Colors.END}
  • GitHub: {Colors.CYAN}https://github.com/smartlegionlab/smart-repository-manager-cli{Colors.END}
  • Core Library: {Colors.CYAN}https://github.com/smartlegionlab/smart-repository-manager-core{Colors.END}
  • GUI Version: {Colors.CYAN}https://github.com/smartlegionlab/smart-repository-manager-gui{Colors.END}

{Colors.BOLD}Support:{Colors.END}
  • Report issues on the GitHub repository.
  • For questions, contact: {Colors.CYAN}smartlegiondev@gmail.com{Colors.END}
"""
        print(about_text)
        wait_for_enter()
