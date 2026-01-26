# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import sys
import time
import traceback

from engine.core.cli_base import SmartGitCLI
from engine.core.menu_handlers import MenuHandlers
from engine.core.repository_manager import RepositoryManager
from engine.core.ssh_manager import SSHManager
from engine.core.step_handlers import StepHandlers
from engine.core.storage_manager import StorageManager
from engine.core.sync_manager import SyncManager
from engine.utils.decorator import Colors, print_error, print_warning, print_info, wait_for_enter, print_section

try:
    from smart_repository_manager_core.utils.helpers import Helpers
except ImportError as e:
    print(f"Error importing core modules: {e}")
    sys.exit(1)


class EnhancedSmartGitCLI(SmartGitCLI):
    def __init__(self, config_path: str = "config.json"):
        super().__init__(config_path)

        self.step_handlers = StepHandlers(self)
        self.menu_handlers = MenuHandlers(self)
        self.repository_manager = RepositoryManager(self)
        self.sync_manager = SyncManager(self)
        self.ssh_manager = SSHManager(self)
        self.storage_manager = StorageManager(self)

        self._bind_methods()

    def _bind_methods(self):
        self.show_main_menu = self.menu_handlers.show_main_menu
        self.show_user_info = self.menu_handlers.show_user_info
        self.show_token_info = self.menu_handlers.show_token_info
        self.show_system_info = self.menu_handlers.show_system_info
        self.clean_temp_files = self.menu_handlers.clean_temp_files

        self.show_repository_menu = self.repository_manager.show_repository_menu
        self.list_all_repositories = self.repository_manager.list_all_repositories
        self.search_repository = self.repository_manager.search_repository
        self.show_language_stats = self.repository_manager.show_language_stats
        self.check_repository_health = self.repository_manager.check_repository_health
        self.check_single_repository = self.repository_manager.check_single_repository

        self.show_sync_menu = self.sync_manager.show_sync_menu
        self.sync_all_repositories = self.sync_manager.sync_all_repositories
        self.update_needed_repositories = self.sync_manager.update_needed_repositories
        self.sync_missing_repositories = self.sync_manager.sync_missing_repositories
        self.sync_with_repair = self.sync_manager.sync_with_repair

        self.show_ssh_menu = self.ssh_manager.show_ssh_menu
        self.show_ssh_info = self.ssh_manager.show_ssh_info
        self.ssh_generate_key = self.ssh_manager.ssh_generate_key
        self.ssh_show_public_keys = self.ssh_manager.ssh_show_public_keys
        self.ssh_fix_permissions = self.ssh_manager.ssh_fix_permissions
        self.ssh_add_github_known_hosts = self.ssh_manager.ssh_add_github_known_hosts
        self.ssh_create_config = self.ssh_manager.ssh_create_config
        self.ssh_test_connection = self.ssh_manager.ssh_test_connection
        self.ssh_detailed_info = self.ssh_manager.ssh_detailed_info

        self.show_storage_menu = self.storage_manager.show_storage_menu
        self.get_storage_info = self.storage_manager.get_storage_info
        self.delete_local_repository = self.storage_manager.delete_local_repository
        self.delete_all_repositories = self.storage_manager.delete_all_repositories
        self.show_storage_info = self.storage_manager.show_storage_info

        self.step1_structure = self.step_handlers.step1_structure
        self.step2_internet = self.step_handlers.step2_internet
        self.step3_ssh = self.step_handlers.step3_ssh
        self.step4_users = self.step_handlers.step4_users
        self.step5_user_data = self.step_handlers.step5_user_data
        self.step6_repositories = self.step_handlers.step6_repositories
        self.step7_local_check = self.step_handlers.step7_local_check
        self.step8_update_check = self.step_handlers.step8_update_check

    def run_full_checkup(self):
        try:
            print_info("Running full system check...")
            start_time = time.time()

            if not self._run_step_with_retry(self.step1_structure, "structure", "Checking directory structure"):
                print_error("Structure check failed")
                if not self.ask_continue("Continue checking?"):
                    return

            if not self._run_step_with_retry(self.step2_internet, "network", "Checking internet connection"):
                print_error("Internet test failed")
                if not self.ask_continue("Continue checking?"):
                    return

            if not self._run_step_with_retry(self.step3_ssh, "ssh", "Checking SSH configuration"):
                print_warning("SSH not configured, some features may not work")
                if not self.ask_continue("Continue checking?"):
                    return

            if not self._run_step_with_retry(self.step4_users, "users", "Loading user configuration"):
                print_error("No user selected")
                return

            if not self._run_step_with_retry(self.step5_user_data, "auth", "Authenticating user"):
                print_error("Failed to get user data")
                return

            if not self._run_step_with_retry(self.step6_repositories, "repos", "Loading repositories"):
                print_error("Failed to get repositories")
                return

            if not self._run_step_with_retry(self.step7_local_check, "local", "Checking local repositories"):
                print_warning("Local repositories not verified")

            self.step8_update_check()

            total_time = time.time() - start_time
            print_section("CHECKUP COMPLETED!")

            summary = self.result_logger.get_summary()
            successful = summary["successful_steps"]
            total = summary["total_steps"]

            print_info(f"{Colors.YELLOW}Total time: {Colors.END}{Helpers.format_duration(total_time)}")
            print_info(f"{Colors.YELLOW}Successful steps: {Colors.END}{successful}/{total}")

            if self.current_user:
                print_info(f"{Colors.YELLOW}User: {Colors.END}{self.current_user.username}")

            if self.repositories:
                print_info(f"{Colors.YELLOW}Repositories: {Colors.END}{len(self.repositories)}\n")

            self.save_results()
            wait_for_enter()
            self.show_main_menu()

        except KeyboardInterrupt:
            print_warning("Check interrupted by user")
        except Exception as e:
            print_error(f"Critical error: {e}")
            traceback.print_exc()

    @staticmethod
    def get_menu_choice(prompt: str, min_choice: int, max_choice: int):
        while True:
            try:
                choice_str = input(f"\n{Colors.CYAN}{prompt} [{min_choice}-{max_choice}]: {Colors.END}").strip()

                if not choice_str:
                    print_error("Please enter a number")
                    continue

                choice = int(choice_str)

                if min_choice <= choice <= max_choice:
                    return choice
                else:
                    print_error(f"Please enter a number between {min_choice} and {max_choice}")

            except ValueError:
                print_error("Please enter a number")
            except (KeyboardInterrupt, EOFError):
                return 0

    def ask_yes_no(self, question: str) -> bool:
        while True:
            response = input(f"\n{Colors.CYAN}{question} (y/n): {Colors.END}").strip().lower()

            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print_error("Please answer 'y' or 'n'")

    def ask_continue(self, question: str) -> bool:
        return self.ask_yes_no(question)


def main():
    try:
        cli = EnhancedSmartGitCLI()
        cli.run_full_checkup()
    except KeyboardInterrupt:
        print_warning("Interrupted by user")
    except Exception as e:
        print_error(f"❌ Critical error: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()
