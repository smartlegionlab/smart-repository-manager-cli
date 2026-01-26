# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import shutil
import sys
import getpass
import time
from pathlib import Path
from datetime import datetime

from engine.utils.decorator import Colors, print_warning, print_info, print_menu_item, print_success, print_section
from smart_repository_manager_core.core.models.ssh_models import SSHStatus
from smart_repository_manager_core.services.config_service import ConfigService
from smart_repository_manager_core.services.github_service import GitHubService
from smart_repository_manager_core.services.ssh_service import SSHService

from engine import __version__ as ver
from engine import __copyright__ as copyright_


class StepHandlers:
    def __init__(self, cli):
        self.cli = cli

    # Step 1
    def check_structure_step(self) -> bool:
        time.sleep(1.0)
        self.cli.log_step(1, "Checking directory structure")

        try:
            config_service = ConfigService(self.cli.config_path)

            config = config_service.load_config()

            config.set_version(ver)

            config.update_last_launch()

            config_service.save_config()

            config = config_service.load_config()


            self.cli.log_result(
                True,
                "Configuration loaded",
                {
                    "app_name": config.app_name,
                    "version": ver,
                    "users_count": len(config.users),
                    "active_user": config.active_user or "Not selected"
                }
            )

            base_dir = Path.home() / "smart_repo_manager"
            base_dir_exists = base_dir.exists()

            if not base_dir_exists:
                print(f"  {Colors.YELLOW}⚠️ Base directory does not exist{Colors.END}")
                print(f"  {Colors.YELLOW}  Will be created when working with user{Colors.END}")

            test_user = "_test_check"
            test_structure = self.cli.structure_service.create_user_structure(test_user)

            if test_structure:
                success = self.cli.log_result(
                    True,
                    "Directory structure works",
                    {
                        "test_user": test_user,
                        "directories": list(test_structure.keys()),
                        "base_dir": str(base_dir)
                    }
                )

                test_user_dir = base_dir / test_user
                if test_user_dir.exists():
                    shutil.rmtree(test_user_dir)
            else:
                return self.cli.log_result(False, "Failed to create structure")

            return success

        except Exception as e:
            return self.cli.log_result(False, f"Structure check error: {str(e)}")

    # Step 2
    def check_internet_connection_step(self) -> bool:
        self.cli.log_step(2, "Checking internet connection")

        try:
            network = self.cli.network_service

            is_online = network.is_online()

            if not is_online:
                return self.cli.log_result(False, "Internet unavailable")

            network_check = network.check_network()

            successful_checks = sum(1 for r in network_check.detailed_results if r["success"])
            total_checks = len(network_check.detailed_results)

            data = {
                "online": network_check.is_online,
                "checks_passed": f"{successful_checks}/{total_checks}",
                "check_duration": f"{network_check.check_duration:.2f}s",
                "servers": []
            }

            for result in network_check.detailed_results:
                status = "✅" if result["success"] else "❌"
                data["servers"].append(
                    f"{status} {result['name']}: {result['response_time']:.2f}s"
                )

            self.cli.log_result(
                network_check.is_online,
                f"Internet available ({successful_checks}/{total_checks} servers)",
                data
            )

            git_ok, git_msg = network.check_git_connectivity()

            self.cli.log_result(
                git_ok,
                f"Git server access: {git_msg}",
                {"git_status": git_msg}
            )

            dns_ok, dns_msg, ip_addresses = network.check_dns_resolution("github.com")

            if dns_ok:
                self.cli.log_result(
                    True,
                    f"DNS working: {dns_msg}",
                    {"ip_addresses": ip_addresses[:3]}
                )

                external_ip = self.cli.get_external_ip()
                if external_ip:
                    self.cli.log_result(
                        True,
                        f"External IP address: {external_ip}",
                        {"external_ip": external_ip}
                    )
                else:
                    self.cli.log_result(
                        False,
                        "Could not retrieve external IP",
                        {"note": "Check connection to IP services"}
                    )
            else:
                self.cli.log_result(False, f"DNS error: {dns_msg}")

            return network_check.is_online

        except Exception as e:
            return self.cli.log_result(False, f"Network check error: {str(e)}")

    # Step 3
    def check_ssh_configuration_step(self) -> bool:
        self.cli.log_step(3, "Checking SSH configuration")

        try:
            ssh = self.cli.ssh_service
            ssh_validation = ssh.validate_ssh_configuration()

            data = {
                "status": ssh_validation.status.value,
                "ssh_keys_found": len(ssh_validation.ssh_config.keys),
                "github_auth_working": ssh_validation.github_authentication_working,
                "can_clone": ssh_validation.can_clone_with_ssh,
                "can_pull": ssh_validation.can_pull_with_ssh
            }

            if ssh_validation.ssh_config.keys:
                keys_info = []
                for key in ssh_validation.ssh_config.keys:
                    key_status = "✅" if key.is_github_authenticated else "⚠️"
                    keys_info.append(
                        f"{key_status} {key.type.value}: {key.fingerprint or 'No fingerprint'}"
                    )
                data["keys"] = keys_info

            if ssh_validation.errors:
                data["errors"] = ssh_validation.errors[:3]

            if ssh_validation.warnings:
                data["warnings"] = ssh_validation.warnings[:3]

            success = self.cli.log_result(
                ssh_validation.status in [SSHStatus.VALID, SSHStatus.PARTIAL],
                f"SSH status: {ssh_validation.status.value}",
                data
            )

            if ssh_validation.ssh_config.keys:
                test_success, test_msg, test_time = ssh.test_connection("github.com", "git")

                self.cli.log_result(
                    test_success,
                    f"SSH connection to GitHub: {test_msg}",
                    {"response_time": f"{test_time:.2f}s"}
                )

            if ssh_validation.errors and self.cli.ask_yes_no("Fix common SSH errors?"):
                self.fix_ssh_issues(ssh, ssh_validation)

            return success

        except Exception as e:
            return self.cli.log_result(False, f"SSH check error: {str(e)}")

    @staticmethod
    def fix_ssh_issues(ssh: SSHService, validation):
        print(f"\n  {Colors.YELLOW}Fixing SSH issues...{Colors.END}")

        if any("permission" in error.lower() for error in validation.errors):
            success, message = ssh.fix_permissions()
            print(f"  {'✅' if success else '❌'} {message}")

        if any("known_hosts" in error.lower() for error in validation.errors):
            success, message = ssh.add_github_to_known_hosts()
            print(f"  {'✅' if success else '❌'} {message}")

        if not validation.ssh_config.has_github_in_config:
            success, message = ssh.create_ssh_config()
            print(f"  {'✅' if success else '❌'} {message}")

        if not validation.ssh_config.keys:
            print(f"  {Colors.YELLOW}Generating new SSH key...{Colors.END}")
            success, message, key_path = ssh.generate_ssh_key()
            print(f"  {'✅' if success else '❌'} {message}")

    # Step 4
    def set_user_step(self):
        self.cli.log_step(4, "Managing GitHub Users")

        try:
            config_service = ConfigService(self.cli.config_path)
            config = config_service.load_config()

            while True:

                print(f"\n  {Colors.BOLD}Current configuration:{Colors.END}")
                print(f"    App: {config.app_name} v{config.version}")
                print(f"    Users: {len(config.users)}")
                print(f"    Active user: {Colors.GREEN}{config.active_user or 'Not selected'}{Colors.END}")

                if config.users:
                    print(f"\n  {Colors.BOLD}Saved Users:{Colors.END}")

                    for i, username in enumerate(config.users.keys(), 1):
                        marker = f"{Colors.GREEN} ➤ {Colors.END}" if username == config.active_user else "   "
                        print_menu_item(f"{i}", f"{marker}{username}")

                    print_menu_item(f"\n    {len(config.users) + 1}", "Add new user")
                    print_menu_item(f"  {len(config.users) + 2}", "Delete user")
                    print_menu_item(f"  {len(config.users) + 3}", "Continue without changes")
                    print_menu_item(f"  {len(config.users) + 4}", "Exit")

                    choice = self.cli.get_menu_choice("Select action", 1, len(config.users) + 4)

                    if choice <= len(config.users):
                        username = list(config.users.keys())[choice - 1]
                        config_service.set_active_user(username)
                        self.cli.current_token = config.users[username]

                        success = self.cli.log_result(
                            True,
                            f"User selected: {username}",
                            {"username": username, "action": "selected_existing"}
                        )

                    elif choice == len(config.users) + 1:
                        return self.add_new_user_step(config_service)

                    elif choice == len(config.users) + 2:
                        self.delete_user_step(config_service, config)
                        continue
                    elif choice == len(config.users) + 4:
                        print_success("Goodbye!")

                        print_section(f"{copyright_}")

                        sys.exit(1)

                    else:
                        if config.active_user:
                            self.cli.current_token = config.users[config.active_user]
                            success = self.cli.log_result(
                                True,
                                f"Using current user: {config.active_user}",
                                {"username": config.active_user}
                            )
                        else:
                            print(f"\n  {Colors.RED}❌ No active user selected{Colors.END}")
                            return self.add_new_user_step(config_service)

                else:
                    print(f"\n  {Colors.YELLOW}⚠️ No saved users{Colors.END}")
                    return self.add_new_user_step(config_service)

                return success

        except Exception as e:
            return self.cli.log_result(False, f"User management error: {str(e)}")

    def add_new_user_step(self, config_service: ConfigService):
        print(f"\n  {Colors.BOLD}Adding new GitHub user{Colors.END}")

        while True:
            print(f"\n  {Colors.YELLOW}GitHub Personal Access Token (PAT) required{Colors.END}")
            print("  To create token:")
            print("  1. Go to https://github.com/settings/tokens")
            print("  2. Click 'Generate new token'")
            print("  3. Select scopes: 'repo' (full repository access)")
            print("  4. Copy the generated token")
            print()

            token = getpass.getpass(f"  {Colors.CYAN}Enter GitHub token: {Colors.END}").strip()

            if not token:
                if self.cli.ask_yes_no("Cancel adding user?"):
                    return False
                continue

            github_service = GitHubService(token)
            valid, user = github_service.validate_token()

            if valid and user:
                config_service.add_user(user.username, token)
                config_service.set_active_user(user.username)

                self.cli.current_user = user
                self.cli.current_token = token

                return self.cli.log_result(
                    True,
                    f"User added: {user.username}",
                    {
                        "username": user.username,
                        "name": user.name,
                        "action": "added_new"
                    }
                )
            else:
                print(f"  {Colors.RED}❌ Invalid token or validation error{Colors.END}")

                if not self.cli.ask_yes_no("Try different token?"):
                    return False

    def delete_user_step(self, config_service: ConfigService, config) -> bool:
        print(f"\n  {Colors.BOLD}Deleting user{Colors.END}")

        if not config.users:
            print(f"  {Colors.YELLOW}No users to delete{Colors.END}")
            return False

        print("\n  Select user to delete:")
        for i, username in enumerate(config.users.keys(), 1):
            print(f"    {i}. {username}")

        print(f"    {len(config.users) + 1}. Cancel")

        choice = self.cli.get_menu_choice("Select user", 1, len(config.users) + 1)

        if choice <= len(config.users):
            username = list(config.users.keys())[choice - 1]

            if self.cli.ask_yes_no(f"Delete user '{username}'? Data will be lost."):
                success = config_service.remove_user(username)

                if success:
                    if username == config.active_user:
                        config_service.set_active_user("")
                        self.cli.current_token = None

                    return self.cli.log_result(
                        True,
                        f"User deleted: {username}",
                        {"username": username, "action": "deleted"}
                    )
                else:
                    return self.cli.log_result(False, f"Error deleting user {username}")

        return False

    # Step 5
    def get_github_user_data_step(self) -> bool:
        self.cli.log_step(5, "Getting GitHub user data")

        if not self.cli.current_token:
            return self.cli.log_result(False, "No token set")

        try:
            github_service = GitHubService(self.cli.current_token)

            valid, user = github_service.validate_token()

            if not valid or not user:
                return self.cli.log_result(False, "Token invalid")

            self.cli.current_user = user

            user_data = {
                "username": user.username,
                "name": user.name or "Not specified",
                "public_repos": user.public_repos,
                "followers": user.followers,
                "following": user.following,
                "created": user.created_date,
                "bio": user.bio[:100] + "..." if user.bio and len(user.bio) > 100 else user.bio or "No description"
            }

            success = self.cli.log_result(
                True,
                f"User: {user.username} ({user.name or 'No name'})",
                user_data
            )

            token_info = github_service.get_token_info()

            token_data = {
                "username": token_info.username,
                "scopes": token_info.scopes or "Not specified",
                "rate_limit": token_info.rate_limit,
                "rate_remaining": token_info.rate_remaining,
                "created": token_info.created_at[:10] if token_info.created_at else "Unknown"
            }

            self.cli.log_result(
                True,
                "Token information received",
                token_data
            )

            limits = github_service.check_rate_limits()

            limits_data = {
                "limit": limits.get("limit", "Unknown"),
                "remaining": limits.get("remaining", "Unknown"),
            }

            if limits.get("reset"):
                try:
                    reset_time = datetime.fromtimestamp(int(limits["reset"]))
                    limits_data["reset_time"] = reset_time.strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    print(e)
                    pass

            self.cli.log_result(
                True,
                f"API Limits: {limits.get('remaining', '?')}/{limits.get('limit', '?')}",
                limits_data
            )

            return success

        except Exception as e:
            return self.cli.log_result(False, f"Error getting user data: {str(e)}")

    # Step 6
    def get_repositories_step(self) -> bool:
        self.cli.log_step(6, "Getting GitHub repositories")

        if not self.cli.current_token or not self.cli.current_user:
            return self.cli.log_result(False, "User not set")

        try:
            github_service = GitHubService(self.cli.current_token)

            print(f"\n  {Colors.YELLOW}Loading repositories for {self.cli.current_user.username}...{Colors.END}")
            print("  This may take a moment...")

            success, repositories = github_service.fetch_user_repositories()

            if not success:
                return self.cli.log_result(False, "Failed to load repositories")

            self.cli.repositories = repositories

            total = len(repositories)
            private_count = sum(1 for r in repositories if r.private)
            public_count = total - private_count

            forks_count = sum(1 for r in repositories if r.fork)
            archived_count = sum(1 for r in repositories if r.archived)

            languages = {}
            for repo in repositories:
                if repo.language:
                    languages[repo.language] = languages.get(repo.language, 0) + 1

            top_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)[:5]

            data = {
                "total": total,
                "private": private_count,
                "public": public_count,
                "forks": forks_count,
                "archived": archived_count,
                "top_languages": dict(top_languages) if top_languages else "No data"
            }

            success = self.cli.log_result(
                True,
                f"Repositories loaded: {total} (private: {private_count})",
                data
            )

            print_warning(f"{Colors.BOLD} Preparing content...{Colors.END}")

            self.cli.update_ui_state()

            return success

        except Exception as e:
            return self.cli.log_result(False, f"Error loading repositories: {str(e)}")

    # Step 7
    def check_local_repositories_step(self) -> bool:
        self.cli.log_step(7, "Checking local repository copies")

        if not self.cli.current_user or not self.cli.repositories:
            return self.cli.log_result(False, "No user data or repositories available")

        try:
            user_structure = self.cli.structure_service.create_user_structure(self.cli.current_user.username)

            if not user_structure:
                return self.cli.log_result(False, "Failed to create directory structure")

            repos_path = user_structure["repositories"]

            data = {
                "user_directory": str(user_structure["user"]),
                "repositories_path": str(repos_path),
                "structure_created": True
            }

            success = self.cli.log_result(
                True,
                f"Structure created for user {self.cli.current_user.username}",
                data
            )

            local_repos = []

            for repo in self.cli.repositories:
                repo_path = repos_path / repo.name

                if repo_path.exists() and (repo_path / '.git').exists():
                    repo.local_exists = True
                    local_repos.append(repo.name)

            local_count = len(local_repos)

            local_data = {
                "total_repositories": len(self.cli.repositories),
                "local_repositories": local_count,
                "missing_local": len(self.cli.repositories) - local_count,
                "local_path": str(repos_path)
            }

            self.cli.log_result(
                True,
                f"Local repositories: {local_count}/{len(self.cli.repositories)}",
                local_data
            )

            return success

        except Exception as e:
            return self.cli.log_result(False, f"Error checking local copies: {str(e)}")

    # Step 8
    def check_need_update_repositories_step(self) -> bool:
        self.cli.log_step(8, "Checking for updates needed")
        print_info('Please be patient...')

        if not self.cli.current_user or not self.cli.repositories:
            return self.cli.log_result(False, "No data to check updates")

        try:
            user_structure = self.cli.structure_service.get_user_structure(self.cli.current_user.username)

            if not user_structure or "repositories" not in user_structure:
                return self.cli.log_result(False, "User structure not found")

            repos_path = user_structure["repositories"]

            needs_update = self.cli.calculate_needs_update_count()
            up_to_date = len(self.cli.repositories) - needs_update
            not_cloned = []

            for repo in self.cli.repositories:
                repo_path = repos_path / repo.name

                if not repo_path.exists() or not (repo_path / '.git').exists():
                    not_cloned.append(repo.name)
                    continue

            update_per = f"{(needs_update / len(self.cli.repositories) * 100):.1f}%" if self.cli.repositories else "0%"

            data = {
                "total_repositories": len(self.cli.repositories),
                "needs_update": needs_update,
                "up_to_date": up_to_date,
                "not_cloned": len(not_cloned),
                "update_percentage": update_per
            }

            success = self.cli.log_result(
                True,
                f"Needs update: {needs_update}/{len(self.cli.repositories)}",
                data
            )

            return success

        except Exception as e:
            return self.cli.log_result(False, f"Error checking updates: {str(e)}")
