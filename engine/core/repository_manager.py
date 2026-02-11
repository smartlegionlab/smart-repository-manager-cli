# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import datetime
import subprocess
from pathlib import Path

from engine.core.archive_creator import ArchiveCreator
from engine.utils.text_decorator import (
    Colors,
    clear_screen,
    print_section,
    print_info,
    Icons,
    print_success,
    print_error,
    print_warning,
    wait_for_enter,
    print_menu_item,
    print_table
)
from smart_repository_manager_core.utils.helpers import Helpers


class RepositoryManager:
    def __init__(self, cli):
        self.cli = cli

    def show_repository_menu(self):
        self.cli.menu_stack.append(self.cli.current_menu)
        self.cli.current_menu = "repositories"

        while self.cli.current_menu == "repositories":
            clear_screen()
            print_section("REPOSITORY MANAGEMENT")

            print(f"\n{Colors.BOLD}📊 Repository Stats:{Colors.END}")
            print(f"  • Total repositories: {len(self.cli.repositories)}")
            print(f"  • Local repositories: {self.cli.get_local_exist_repos_count()}")
            print(f"  • Needs update: {self.cli.get_need_update_repos_count()}")
            print(f"  • Private repositories: {self.cli.get_private_repos_count()}")
            print(f"  • Public repositories: {self.cli.get_public_repos_count()}")
            print(f"  • Archived repositories: {self.cli.ui_state.get('total_archived', 0)}")
            print(f"  • Forks: {self.cli.ui_state.get('total_forks', 0)}")

            print(f"\n{Colors.BOLD}📋 Commands:{Colors.END}")
            print_menu_item("1", "List All Repositories", Icons.LIST)
            print_menu_item("2", "Search for Repository", Icons.SEARCH)
            print_menu_item("3", "Language Statistics", Icons.LANGUAGE)
            print_menu_item("4", "Check Single Repository", Icons.SEARCH)
            print_menu_item("5", "Repository Health Check", Icons.CHECK)
            print_menu_item("6", "Create Archive", Icons.STORAGE)

            print(f"\n{Colors.BOLD}{Colors.BLUE}0.{Colors.END} {Icons.BACK} Back")
            print('=' * 60)

            choice = self.cli.get_menu_choice("Select option", 0, 6)

            if choice == 0:
                self.cli.current_menu = self.cli.menu_stack.pop()
            elif choice == 1:
                self.list_all_repositories()
            elif choice == 2:
                self.search_repository()
            elif choice == 3:
                self.show_language_stats()
            elif choice == 4:
                self.check_single_repository()
            elif choice == 5:
                self.check_repository_health()
            elif choice == 6:
                self.create_user_repositories_archive()

            if choice != 0:
                wait_for_enter()

    def list_all_repositories(self):
        clear_screen()
        print_section("LIST ALL REPOSITORIES")

        if not self.cli.repositories:
            print_error("No repositories available")
            return

        print(f"\n{Colors.BOLD}Total: {len(self.cli.repositories)} repositories{Colors.END}")
        print_info("Showing all repositories")

        headers = ["#", "Name", "Local", "Updates", "Private", "Language", "Size"]
        rows = []

        for i, repo in enumerate(self.cli.repositories, 1):
            local_icon = Icons.SUCCESS if repo.local_exists else Icons.ERROR
            if repo.local_exists and self.cli.current_user:
                needs_update = repo.need_update
                update_icon = Icons.WARNING if needs_update else Icons.SUCCESS
            else:
                update_icon = Icons.WARNING if not repo.need_update or not repo.local_exists else Icons.SUCCESS

            private_icon = Icons.LOCK if repo.private else Icons.NETWORK
            size_mb = repo.size / 1024 if repo.size else 0

            rows.append([
                i,
                repo.name[:50],
                local_icon,
                update_icon,
                private_icon,
                repo.language or "-",
                f"{size_mb:.1f} MB"
            ])

        print_table(headers, rows)

    def search_repository(self):
        clear_screen()
        print_section("SEARCH REPOSITORY")

        if not self.cli.repositories:
            print_error("No repositories available")
            return

        search_term = input(f"\n{Colors.CYAN}Enter repository name to search: {Colors.END}").strip().lower()

        if not search_term:
            print_error("Search term cannot be empty")
            return

        found_repos = [r for r in self.cli.repositories if search_term in r.name.lower()]

        if not found_repos:
            print_error("No repositories found")
            return

        clear_screen()
        print_section("SEARCH RESULTS")
        print(f"\n{Colors.BOLD}Found: {len(found_repos)} repositories{Colors.END}")

        headers = ["Name", "Local", "Updates", "Language", "Description"]
        rows = []

        for repo in found_repos:
            local_icon = Icons.SUCCESS if repo.local_exists else Icons.ERROR

            if repo.local_exists and self.cli.current_user:
                needs_update = repo.need_update
                update_icon = Icons.WARNING if needs_update else Icons.SUCCESS
            else:
                update_icon = Icons.WARNING if not repo.need_update else Icons.SUCCESS

            description = repo.description[:40] + "..." if repo.description and len(repo.description) > 40 else (
                        repo.description or "-")

            rows.append([
                repo.name[:50],
                local_icon,
                update_icon,
                repo.language or "-",
                description
            ])

        print_table(headers, rows)

    def show_language_stats(self):
        clear_screen()
        print_section("LANGUAGE STATISTICS")

        if not self.cli.repositories:
            print_error("No repositories available")
            return

        languages = {}
        for repo in self.cli.repositories:
            if repo.language:
                languages[repo.language] = languages.get(repo.language, 0) + 1

        if not languages:
            print_info("No language data available")
            return

        total_repos = len(self.cli.repositories)
        sorted_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)

        print(f"\n{Colors.BOLD}Top Languages:{Colors.END}")

        headers = ["Language", "Count", "Percentage"]
        rows = []

        for lang, count in sorted_languages:
            percentage = (count / total_repos) * 100
            rows.append([lang, count, f"{percentage:.1f}%"])

        print_table(headers, rows)

        other_count = total_repos - sum(count for _, count in sorted_languages)
        if other_count > 0:
            print_info(f"Other languages: {other_count} repositories")

    def check_repository_health(self):
        clear_screen()
        print_section("REPOSITORY HEALTH CHECK")

        if not self.cli.current_user or not self.cli.repositories:
            print_error("User or repositories not loaded")
            return

        print_info("Checking repository health...")

        structure = self.cli.structure_service.get_user_structure(self.cli.current_user.username)
        if "repositories" not in structure:
            print_error("Storage structure not found")
            return

        repos_path = structure["repositories"]

        healthy_count = 0
        broken_count = 0
        missing_count = 0

        for repo in self.cli.repositories:
            repo_path = repos_path / repo.name

            if not repo_path.exists():
                missing_count += 1
                continue

            if not (repo_path / '.git').exists():
                broken_count += 1
                continue

            try:
                result = subprocess.run(
                    ['git', '-C', str(repo_path), 'rev-parse', '--git-dir'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    healthy_count += 1
                else:
                    broken_count += 1
            except Exception as e:
                print(e)
                broken_count += 1

        print(f"\n{Colors.BOLD}Health Status:{Colors.END}")
        print(f"  • {Icons.SUCCESS} Healthy: {healthy_count}")
        print(f"  • {Icons.ERROR} Broken: {broken_count}")
        print(f"  • {Icons.WARNING} Missing: {missing_count}")

        if broken_count > 0 or missing_count > 0:
            print_warning("Some repositories have issues")
            print_info("Use 'Sync with Repair' option to fix them")

    def create_user_repositories_archive(self):
        clear_screen()
        print_section("CREATE ARCHIVE")

        username = self.cli.current_user.username
        user_path = Path.home() / "smart_repository_manager" / username
        repos_path = user_path / "repositories"
        archive_path = user_path / "archives"
        current_datetime = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{username}_repositories_{current_datetime}"
        archive_format = 'zip'

        print(f'\n{Colors.BLUE}This will create a ZIP archive containing all user data.{Colors.END}\n')
        print(f'\n  • {Colors.YELLOW}Username:{Colors.END} {username}')
        print(f'  • {Colors.YELLOW}Repositories path:{Colors.END} {repos_path}')
        print(f"  • {Colors.YELLOW}Archives path:{Colors.END} {archive_path}")
        print(f"  • {Colors.YELLOW}Archives name:{Colors.END} "
              f"{Colors.GREEN}{archive_name}.{archive_format}{Colors.END}\n\n")

        if not username:
            print(f"\n{Colors.RED}Warning! No user selected...{Colors.END}")
            return

        response = input(f'Create archive of user {username} [y/n]? ')

        if response.lower() != 'y':
            return

        print(f'\n{Colors.YELLOW}Creating archive...\nPlease wait...{Colors.END}\n')

        archive_path.mkdir(parents=True, exist_ok=True)

        archive_file = ArchiveCreator.create_archive(
            folder_path=repos_path,
            archive_format=archive_format,
            output_dir=archive_path,
            archive_name=archive_name
        )

        print(f'{Colors.GREEN}Archive successfully created at:{Colors.END} {archive_file}')

    def check_single_repository(self):
        clear_screen()
        print_section("CHECK SINGLE REPOSITORY")

        if not self.cli.current_user or not self.cli.repositories:
            print_error("User or repositories not loaded")
            return

        print("Available repositories:")
        for i, repo in enumerate(self.cli.repositories, 1):
            print(f"{i:2d}. {repo.name}")

        try:
            choice = self.cli.get_menu_choice(f"\nSelect repository (0 for exit)", 0, len(self.cli.repositories))

            if not choice:
                return

            repo = self.cli.repositories[choice - 1]

            clear_screen()
            print_section(f"REPOSITORY: {repo.name}")

            print(f"\n{Colors.BOLD}📋 Basic Info:{Colors.END}")
            print(f"  • {Colors.YELLOW}Full Name: {Colors.END}{repo.full_name}")
            print(f"  • {Colors.YELLOW}Description: {Colors.END}{repo.description or 'No description'}")
            print(f"  • {Icons.LOCK if repo.private else Icons.UNLOCK} {Colors.YELLOW}"
                  f"Private: {Colors.END}{'Yes' if repo.private else 'No'}")
            print(f"  • {Icons.LANGUAGE}{Colors.YELLOW}Language: {Colors.END}{repo.language or 'Not specified'}")
            print(f"  • {Icons.STAR} {Colors.YELLOW}Stars: {Colors.END}{repo.stargazers_count}")
            print(f"  • {Icons.FORK} {Colors.YELLOW}Forks: {Colors.END}{repo.forks_count}")
            print(f"  • {Icons.CALENDAR} {Colors.YELLOW}Last Update: {Colors.END}{repo.last_update}")
            print(f"  • {Colors.YELLOW}URL: {Colors.CYAN}{repo.html_url}")

            if repo.ssh_url:
                print(f"\n{Colors.YELLOW}🔐 SSH URL:{Colors.END}")
                print(f"  • {repo.ssh_url}")

                needs_update = False
                reason = "Unknown"
                if self.cli.current_user:
                    needs_update, reason = self.cli.sync_service.check_repository_needs_update(
                        self.cli.current_user,
                        repo
                    )

                print(f"\n{Colors.YELLOW}📊 Local Status:{Colors.END}")
                print(f"  • {Colors.YELLOW}Exists: {Colors.END}{'✓' if repo.local_exists else '✗'}")
                print(f"  • {Colors.YELLOW}Status: {Colors.END}{reason}")

                if needs_update:
                    print(f"\n{Colors.YELLOW}{Icons.WARNING} This repository needs updating.{Colors.END}")

                    if self.cli.ask_yes_no("Update now?"):
                        success, message, duration = self.cli.sync_service.sync_single_repository(
                            self.cli.current_user,
                            repo,
                            "update"
                        )

                        if success:
                            print_success(f"Updated successfully in {Helpers.format_duration(duration)}")
                        else:
                            print_error(f"Update failed: {message}")
            else:
                print_error("No SSH URL available")

        except (KeyboardInterrupt, EOFError):
            print_warning("Cancelled")
        except Exception as e:
            print_error(f"Error: {e}")
