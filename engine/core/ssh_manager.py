# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
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
from smart_repository_manager_core.core.models.ssh_models import SSHKeyType
from smart_repository_manager_core.services.ssh_service import SSHService


class SSHManager:
    def __init__(self, cli):
        self.cli = cli

    def show_ssh_menu(self):
        self.cli.menu_stack.append(self.cli.current_menu)
        self.cli.current_menu = "ssh"

        while self.cli.current_menu == "ssh":
            clear_screen()
            print_section("SSH CONFIGURATION")
            print_info(" Please wait...")

            ssh = SSHService()
            validation = ssh.validate_ssh_configuration()

            print(f"\n{Colors.BOLD}🔐 Status:{Colors.END}")
            status = validation.status.value
            if status == 'valid':
                status_display = f"{Colors.GREEN}✓ Ready{Colors.END}"
            elif status == 'partial':
                status_display = f"{Colors.YELLOW}⚠️ Requires configuration{Colors.END}"
            else:
                status_display = f"{Colors.RED}✗ Not configured{Colors.END}"

            print(f"  • Configuration: {status_display}")
            print(f"  • Can clone: {'✓' if validation.can_clone_with_ssh else '✗'}")
            print(f"  • Can pull: {'✓' if validation.can_pull_with_ssh else '✗'}")
            print(f"  • GitHub auth: {'✓' if validation.github_authentication_working else '✗'}")

            print(f"\n{Colors.BOLD}🔧 Commands:{Colors.END}")
            print_menu_item("1", "Check SSH", Icons.CHECK)
            print_menu_item("2", "Generate SSH Key", Icons.KEY)
            print_menu_item("3", "Show SSH Keys", Icons.KEY)
            print_menu_item("4", "Fix Permissions", Icons.SETTINGS)
            print_menu_item("5", "Add GitHub to known_hosts", Icons.GITHUB)
            print_menu_item("6", "Create SSH Config", Icons.SETTINGS)
            print_menu_item("7", "Test Connection", Icons.NETWORK)
            print_menu_item("8", "Detailed Information", Icons.INFO)

            print(f"\n{Colors.BOLD}{Colors.BLUE}0.{Colors.END} {Icons.BACK}  Back")
            print('=' * 60)

            choice = self.cli.get_menu_choice("Select option", 0, 8)

            if choice == 0:
                self.cli.current_menu = self.cli.menu_stack.pop()
            elif choice == 1:
                self.show_ssh_info()
            elif choice == 2:
                self.ssh_generate_key()
            elif choice == 3:
                self.ssh_show_public_keys()
            elif choice == 4:
                self.ssh_fix_permissions()
            elif choice == 5:
                self.ssh_add_github_known_hosts()
            elif choice == 6:
                self.ssh_create_config()
            elif choice == 7:
                self.ssh_test_connection()
            elif choice == 8:
                self.ssh_detailed_info()

            if choice != 0:
                wait_for_enter()

    @staticmethod
    def show_ssh_info():
        clear_screen()
        print_section("SSH INFORMATION")

        print_info(" Please wait...")

        try:
            ssh = SSHService()
            validation = ssh.validate_ssh_configuration()

            ssh_config = validation.ssh_config

            print(f"\n{Colors.BOLD}📁 SSH Configuration:{Colors.END}")
            print(f"  • SSH Directory: {ssh_config.ssh_dir}")
            print(f"  • Status: {validation.status.value}")
            print(f"  • GitHub Auth Working: {'✅ Yes' if validation.github_authentication_working else '❌ No'}")
            print(f"  • Can Clone with SSH: {'✅ Yes' if validation.can_clone_with_ssh else '❌ No'}")
            print(f"  • Can Pull with SSH: {'✅ Yes' if validation.can_pull_with_ssh else '❌ No'}")

            print(f"\n{Colors.BOLD}🔑 SSH Keys Found: {len(ssh_config.keys)}{Colors.END}")
            for i, key in enumerate(ssh_config.keys, 1):
                print(f"\n  {i}. {key.type.value.upper()} Key:")
                print(f"     Private: {key.private_path}")
                if key.public_path:
                    print(f"     Public:  {key.public_path}")
                if key.fingerprint:
                    print(f"     Fingerprint: {key.fingerprint}")
                if key.comment:
                    print(f"     Comment: {key.comment}")
                print(f"     GitHub Auth: {'✅ Yes' if key.is_github_authenticated else '❌ No'}")
                print(f"     Encrypted: {'✅ Yes' if key.is_encrypted else '❌ No'}")

            print(f"\n{Colors.BOLD}📄 Configuration Files:{Colors.END}")
            print(
                f"  Config File: {ssh_config.config_file} ({'✅ Exists' if ssh_config.config_file.exists() else '❌ Missing'})")
            if ssh_config.config_file.exists():
                print(f"    Has GitHub config: {'✅ Yes' if ssh_config.has_github_in_config else '❌ No'}")

            print(
                f"  Known Hosts: {ssh_config.known_hosts_file} ({'✅ Exists' if ssh_config.known_hosts_file.exists() else '❌ Missing'})")
            if ssh_config.known_hosts_file.exists():
                print(f"    Has GitHub: {'✅ Yes' if ssh_config.has_github_in_known_hosts else '❌ No'}")

            print(f"\n{Colors.BOLD}📋 Validation Results:{Colors.END}")
            if validation.errors:
                print(f"  {Colors.RED}Errors:{Colors.END}")
                for error in validation.errors:
                    print(f"    ❌ {error}")

            if validation.warnings:
                print(f"  {Colors.YELLOW}Warnings:{Colors.END}")
                for warning in validation.warnings:
                    print(f"    ⚠️  {warning}")

            if validation.recommendations:
                print(f"  {Colors.GREEN}Recommendations:{Colors.END}")
                for rec in validation.recommendations:
                    print(f"    💡 {rec}")

        except Exception as e:
            print_error(f"Error getting SSH info: {e}")

    def ssh_generate_key(self):
        clear_screen()
        print_section("GENERATE SSH KEY")

        print("Select key type:")
        print_menu_item("1", "ED25519 (Recommended)", Icons.KEY)
        print_menu_item("2", "RSA 4096 (Legacy)", Icons.KEY)
        print_menu_item("3", "ECDSA", Icons.KEY)
        print_menu_item("4", "DSA (Not recommended)", Icons.WARNING)

        key_type_choice = self.cli.get_menu_choice("Select key type", 1, 4)

        key_type_map = {
            1: SSHKeyType.ED25519,
            2: SSHKeyType.RSA,
            3: SSHKeyType.ECDSA,
            4: SSHKeyType.DSA
        }

        key_type = key_type_map[key_type_choice]

        print(f"\n{Colors.YELLOW}Enter email for key comment (optional):{Colors.END}")
        email = input(f"{Colors.CYAN}Email: {Colors.END}").strip()

        print(f"\n{Colors.YELLOW}Enter custom key name (optional, default: id_{key_type.value}):{Colors.END}")
        key_name = input(f"{Colors.CYAN}Key name: {Colors.END}").strip()

        if not key_name:
            key_name = None

        print(f"\n{Colors.YELLOW}Generating {key_type.value} key...{Colors.END}")

        ssh = SSHService()
        success, message, key_path = ssh.generate_ssh_key(
            key_type=key_type,
            email=email if email else None,
            key_name=key_name
        )

        if success:
            print_success(message)
            if key_path:
                print_success(f"Public key saved to: {key_path}")

                try:
                    public_key_content = key_path.read_text().strip()
                    print(f"\n{Colors.BOLD}Public Key Content:{Colors.END}")
                    print(f"{Colors.CYAN}{public_key_content}{Colors.END}")

                    print(f"\n{Colors.YELLOW}Add this key to GitHub:{Colors.END}")
                    print("1. Go to https://github.com/settings/keys")
                    print("2. Click 'New SSH key'")
                    print("3. Paste the above key content")
                    print("4. Add a title and click 'Add SSH key'")

                except Exception as e:
                    print_error(f"Error reading public key: {e}")
        else:
            print_error(message)

    def ssh_show_public_keys(self):
        clear_screen()
        print_section("SHOW PUBLIC SSH KEYS")

        print_info(" Please wait...")

        ssh = SSHService()
        keys = ssh.get_public_keys()

        if not keys:
            print_info("No public SSH keys found")
            return

        print_success(f"Found {len(keys)} public keys:\n")

        for i, key in enumerate(keys, 1):
            print(f"{i}. {key['type'].upper()} Key:")
            print(f"   Path: {key['path']}")
            if key['fingerprint']:
                print(f"   Fingerprint: {key['fingerprint']}")
            print(f"   GitHub Working: {'✅ Yes' if key['github_working'] else '❌ No'}")
            print()

            if self.cli.ask_yes_no("Show key content?"):
                print(f"{Colors.CYAN}{key['content']}{Colors.END}")
                print()

    @staticmethod
    def ssh_fix_permissions():
        clear_screen()
        print_section("FIX SSH PERMISSIONS")

        ssh = SSHService()
        success, message = ssh.fix_permissions()

        if success:
            print_success(message)
        else:
            print_error(message)

    @staticmethod
    def ssh_add_github_known_hosts():
        clear_screen()
        print_section("ADD GITHUB TO KNOWN HOSTS")

        ssh = SSHService()
        success, message = ssh.add_github_to_known_hosts()

        if success:
            print_success(message)
        else:
            print_error(message)

    @staticmethod
    def ssh_create_config():
        clear_screen()
        print_section("CREATE SSH CONFIG")

        ssh = SSHService()
        success, message = ssh.create_ssh_config()

        if success:
            print_success(message)

            try:
                config_path = ssh.config_file
                config_content = config_path.read_text()
                print(f"\n{Colors.BOLD}SSH Config Content:{Colors.END}")
                print(f"{Colors.CYAN}{config_content}{Colors.END}")
            except Exception as e:
                print_error(f"Error reading config: {e}")
        else:
            print_error(message)

    @staticmethod
    def ssh_test_connection():
        clear_screen()
        print_section("TEST SSH CONNECTION")

        print_info("Testing connection to GitHub...")

        ssh = SSHService()
        success, message, response_time = ssh.test_connection("github.com", "git")

        if success:
            print_success(message)
            print_info(f"Response time: {response_time:.2f}s")
        else:
            print_error(message)

    @staticmethod
    def ssh_detailed_info():
        clear_screen()
        print_section("DETAILED SSH INFORMATION")

        print_info(" Please wait...")

        try:
            ssh = SSHService()
            validation = ssh.validate_ssh_configuration()

            ssh_config = validation.ssh_config

            print(f"\n{Colors.BOLD}📁 Configuration Files:{Colors.END}")
            print(f"  • SSH Directory: {ssh_config.ssh_dir}")
            print(f"  • Config File: {ssh_config.config_file}")
            print(f"  • Known Hosts: {ssh_config.known_hosts_file}")

            print(f"\n{Colors.BOLD}🔑 SSH Keys ({len(ssh_config.keys)}):{Colors.END}")
            for key in ssh_config.keys:
                print(f"  • Type: {key.type.value.upper()}")
                print(f"    Private: {key.private_path}")
                if key.public_path:
                    print(f"    Public: {key.public_path}")
                if key.fingerprint:
                    print(f"    Fingerprint: {key.fingerprint}")
                print(f"    GitHub Auth: {'✓' if key.is_github_authenticated else '✗'}")
                print(f"    Encrypted: {'✓' if key.is_encrypted else '✗'}")
                print()

            print(f"\n{Colors.BOLD}🧪 Test Results:{Colors.END}")
            test_results = validation.test_results
            for test, result in test_results.items():
                result_icon = "✓" if result else "✗"
                result_color = Colors.GREEN if result else Colors.RED
                print(f"  {result_color}{result_icon}{Colors.END} {test}")

            print(f"\n{Colors.BOLD}📊 Validation:{Colors.END}")
            print(f"  • Status: {validation.status.value}")
            print(f"  • Can Clone: {'✓' if validation.can_clone_with_ssh else '✗'}")
            print(f"  • Can Pull: {'✓' if validation.can_pull_with_ssh else '✗'}")
            print(f"  • GitHub Auth: {'✓' if validation.github_authentication_working else '✗'}")

            if validation.errors:
                print(f"\n{Colors.BOLD}{Colors.RED}❌ Errors:{Colors.END}")
                for error in validation.errors:
                    print(f"  {error}")

            if validation.warnings:
                print(f"\n{Colors.BOLD}{Colors.YELLOW}⚠️ Warnings:{Colors.END}")
                for warning in validation.warnings:
                    print(f"  {warning}")

            if validation.recommendations:
                print(f"\n{Colors.BOLD}{Colors.GREEN}💡 Recommendations:{Colors.END}")
                for rec in validation.recommendations:
                    print(f"  {rec}")

        except Exception as e:
            print_error(f"Error getting SSH info: {e}")
