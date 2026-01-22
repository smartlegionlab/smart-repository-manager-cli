# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import subprocess

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
            print(f"  • Private repositories: {self.cli.ui_state.get('total_private', 0)}")
            print(f"  • Archived repositories: {self.cli.ui_state.get('total_archived', 0)}")
            print(f"  • Forks: {self.cli.ui_state.get('total_forks', 0)}")

            print(f"\n{Colors.BOLD}📋 Commands:{Colors.END}")
            print_menu_item("1", "List All Repositories", Icons.LIST)
            print_menu_item("2", "Search for Repository", Icons.SEARCH)
            print_menu_item("3", "Language Statistics", Icons.LANGUAGE)
            print_menu_item("4", "Check Single Repository", Icons.SEARCH)
            print_menu_item("5", "Repository Health Check", Icons.CHECK)

            print(f"\n{Colors.BOLD}{Colors.BLUE}0.{Colors.END} {Icons.BACK} Back")
            print('=' * 60)

            choice = self.cli._get_menu_choice("Select option", 0, 5)

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
                update_icon = Icons.WARNING if not repo.need_update else Icons.SUCCESS

            private_icon = Icons.LOCK if repo.private else Icons.UNLOCK
            size_mb = repo.size / 1024 if repo.size else 0

            rows.append([
                i,
                repo.name[:30],
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

        for repo in found_repos[:20]:
            local_icon = Icons.SUCCESS if repo.local_exists else Icons.ERROR

            if repo.local_exists and self.cli.current_user:
                needs_update = self.cli._get_repository_needs_update(repo)
                update_icon = Icons.WARNING if needs_update else Icons.SUCCESS
            else:
                update_icon = Icons.ERROR if not repo.local_exists else Icons.SUCCESS

            description = repo.description[:40] + "..." if repo.description and len(repo.description) > 40 else (
                        repo.description or "-")

            rows.append([
                repo.name[:30],
                local_icon,
                update_icon,
                repo.language or "-",
                description
            ])

        print_table(headers, rows)

        if len(found_repos) > 20:
            print_info(f"... and {len(found_repos) - 20} more repositories")

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

        for lang, count in sorted_languages[:15]:
            percentage = (count / total_repos) * 100
            rows.append([lang, count, f"{percentage:.1f}%"])

        print_table(headers, rows)

        other_count = total_repos - sum(count for _, count in sorted_languages[:15])
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
            except:
                broken_count += 1

        print(f"\n{Colors.BOLD}Health Status (first 20):{Colors.END}")
        print(f"  • {Icons.SUCCESS} Healthy: {healthy_count}")
        print(f"  • {Icons.ERROR} Broken: {broken_count}")
        print(f"  • {Icons.WARNING} Missing: {missing_count}")

        if broken_count > 0 or missing_count > 0:
            print_warning("Some repositories have issues")
            print_info("Use 'Sync with Repair' option to fix them")

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
            choice = self.cli._get_menu_choice(f"\nSelect repository (0 for exit)", 0, len(self.cli.repositories))

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
