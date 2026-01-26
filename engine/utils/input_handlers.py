# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
from engine.utils.text_decorator import Colors, print_error


class InputHandler:
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

    @staticmethod
    def ask_yes_no(question: str) -> bool:
        while True:
            response = input(f"\n{Colors.CYAN}{question} (y/n): {Colors.END}").strip().lower()

            if response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print_error("Please answer 'y' or 'n'")
