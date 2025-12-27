# Copyright (©) 2025, Alexander Suvorov. All rights reserved.
from engine.utils.decorator import Colors, clear_screen, print_section, print_menu_item, Icons


class MenuRenderer:
    @staticmethod
    def render_main_menu(ui_state: dict):
        clear_screen()
        print_section("MAIN MENU")

        print(f"\n{Colors.BOLD}📊 System Status:{Colors.END}")
        if ui_state.get('current_user'):
            print(f"  • {Icons.USER} User: {Colors.CYAN}{ui_state['current_user'].username}{Colors.END}")

        print(f"\n{Colors.BOLD}📊 Repositories Status:{Colors.END}")
        print(f"  • {Icons.REPO} Total repositories: {Colors.CYAN}{ui_state.get('repositories_count', 0)}{Colors.END}")
        print(
            f"  • {Icons.FOLDER} Local repositories: {Colors.CYAN}{ui_state.get('local_repositories_count', 0)}{Colors.END}")

        if ui_state.get('total_public', 0) > 0:
            print(f"  • {Icons.LOCK} Public repositories: {ui_state.get('total_public')}")

        if ui_state.get('total_private', 0) > 0:
            print(f"  • {Icons.LOCK} Private repositories: {ui_state.get('total_private')}")

        if ui_state.get('total_archived', 0) > 0:
            print(f"  • {Icons.STORAGE} Archived repositories: {ui_state.get('total_archived')}")

        print(f"  • {Icons.SYNC} Needs update: {Colors.YELLOW}{ui_state.get('needs_update_count', 0)}{Colors.END}")

        print(f"\n{Colors.BOLD}🚀 Main Commands:{Colors.END}")
        print_menu_item("1", "User Information", Icons.USER)
        print_menu_item("2", "Token Information", Icons.KEY)
        print_menu_item("3", "Repository Management", Icons.REPO)
        print_menu_item("4", "Synchronization", Icons.SYNC)
        print_menu_item("5", "SSH Configuration", Icons.SSH)
        print_menu_item("6", "Storage Management", Icons.STORAGE)
        print_menu_item("7", "System Information", Icons.INFO)

        print(f"\n{Colors.BOLD}⚙️  System:{Colors.END}")
        print_menu_item("8", "Run Checkup", Icons.CHECK)
        print_menu_item("9", "Clean Temporary Files", Icons.DELETE)

        print(f"\n{Colors.BOLD}{Colors.RED}0.{Colors.END} {Icons.EXIT} Exit")
        print('=' * 60)

    @staticmethod
    def render_repository_menu(ui_state: dict):
        clear_screen()
        print_section("REPOSITORY MANAGEMENT")

        print(f"\n{Colors.BOLD}📊 Repository Stats:{Colors.END}")
        print(f"  • Total repositories: {ui_state.get('repositories_count', 0)}")
        print(f"  • Local repositories: {ui_state.get('local_repositories_count', 0)}")
        print(f"  • Needs update: {ui_state.get('needs_update_count', 0)}")
        print(f"  • Private repositories: {ui_state.get('total_private', 0)}")
        print(f"  • Archived repositories: {ui_state.get('total_archived', 0)}")
        print(f"  • Forks: {ui_state.get('total_forks', 0)}")

        print(f"\n{Colors.BOLD}📋 Commands:{Colors.END}")
        print_menu_item("1", "List All Repositories", Icons.LIST)
        print_menu_item("2", "Search for Repository", Icons.SEARCH)
        print_menu_item("3", "Language Statistics", Icons.LANGUAGE)
        print_menu_item("4", "Check Single Repository", Icons.SEARCH)
        print_menu_item("5", "Repository Health Check", Icons.CHECK)

        print(f"\n{Colors.BOLD}{Colors.BLUE}0.{Colors.END} {Icons.BACK} Back")
        print('=' * 60)

    @staticmethod
    def render_sync_menu(ui_state: dict):
        clear_screen()
        print_section("SYNCHRONIZATION")

        print(f"\n{Colors.BOLD}📊 Status:{Colors.END}")
        print(f"  • Local repositories: {ui_state.get('local_repositories_count', 0)}")
        print(f"  • Needs update: {ui_state.get('needs_update_count', 0)}")

        print(f"\n{Colors.BOLD}🔄 Commands:{Colors.END}")
        print_menu_item("1", "Synchronize All", Icons.SYNC)
        print_menu_item("2", "Update Needed Only", Icons.SYNC)
        print_menu_item("3", "Clone Missing Only", Icons.DOWNLOAD)
        print_menu_item("4", "Sync with Repair", Icons.SETTINGS)

        print(f"\n{Colors.BOLD}{Colors.BLUE}0.{Colors.END} {Icons.BACK} Back")
        print('=' * 60)

    @staticmethod
    def render_ssh_menu(validation_result):
        clear_screen()
        print_section("SSH CONFIGURATION")

        status = validation_result.status.value
        if status == 'valid':
            status_display = f"{Colors.GREEN}✓ Ready{Colors.END}"
        elif status == 'partial':
            status_display = f"{Colors.YELLOW}⚠️ Requires configuration{Colors.END}"
        else:
            status_display = f"{Colors.RED}✗ Not configured{Colors.END}"

        print(f"\n{Colors.BOLD}🔐 Status:{Colors.END}")
        print(f"  • Configuration: {status_display}")
        print(f"  • Can clone: {'✓' if validation_result.can_clone_with_ssh else '✗'}")
        print(f"  • Can pull: {'✓' if validation_result.can_pull_with_ssh else '✗'}")
        print(f"  • GitHub auth: {'✓' if validation_result.github_authentication_working else '✗'}")

        print(f"\n{Colors.BOLD}🔧 Commands:{Colors.END}")
        print_menu_item("1", "Check SSH", Icons.CHECK)
        print_menu_item("2", "Generate SSH Key", Icons.KEY)
        print_menu_item("3", "Show SSH Keys", Icons.KEY)
        print_menu_item("4", "Fix Permissions", Icons.SETTINGS)
        print_menu_item("5", "Add GitHub to known_hosts", Icons.GITHUB)
        print_menu_item("6", "Create SSH Config", Icons.SETTINGS)
        print_menu_item("7", "Test Connection", Icons.NETWORK)
        print_menu_item("8", "Detailed Information", Icons.INFO)

        print(f"\n{Colors.BOLD}{Colors.BLUE}0.{Colors.END} {Icons.BACK} Back")
        print('=' * 60)

    @staticmethod
    def render_storage_menu(storage_info: dict):
        clear_screen()
        print_section("STORAGE MANAGEMENT")

        print(f"\n{Colors.BOLD}💾 Local Storage:{Colors.END}")
        if 'error' in storage_info:
            print(f"  • {Colors.RED}Error: {storage_info['error']}{Colors.END}")
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
        print_menu_item("2", "Clear All Storage", Icons.DELETE)
        print_menu_item("3", "Storage Information", Icons.INFO)

        print(f"\n{Colors.BOLD}{Colors.BLUE}0.{Colors.END} {Icons.BACK} Back")
        print('=' * 60)
