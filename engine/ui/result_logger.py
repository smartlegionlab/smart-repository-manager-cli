# Copyright (©) 2026, Alexander Suvorov. All rights reserved.
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

from engine.utils.decorator import Colors, Icons, print_success


class ResultLogger:
    def __init__(self):
        self.results: List[Dict[str, Any]] = []

    def log_result(self, success: bool, message: str, data: Dict[str, Any] = None) -> bool:
        result = {
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "message": message,
            "data": data or {}
        }
        self.results.append(result)

        print_success(f"{message}")

        if data and success:
            for key, value in data.items():
                if isinstance(value, (list, dict)) and len(str(value)) > 50:
                    print(f"    {Colors.YELLOW}{key}:{Colors.END} {len(value)} items")
                else:
                    print(f"    {Colors.YELLOW}{key}:{Colors.END} {value}")

        return success

    def save_results(self, username: str, results_dir: Path):
        results_file = results_dir / f"checkup_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        results_data = {
            "checkup_timestamp": datetime.now().isoformat(),
            "total_steps": len(self.results),
            "successful_steps": sum(1 for r in self.results if r["success"]),
            "failed_steps": sum(1 for r in self.results if not r["success"]),
            "steps": self.results,
            "username": username
        }

        results_dir.mkdir(parents=True, exist_ok=True)

        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, ensure_ascii=False)

        print_success(f"Results saved to: {results_file}")
        return results_file

    def clear(self):
        self.results.clear()

    def get_summary(self) -> Dict[str, Any]:
        successful = sum(1 for r in self.results if r["success"])
        total = len(self.results)

        return {
            "total_steps": total,
            "successful_steps": successful,
            "failed_steps": total - successful,
            "success_rate": (successful / total * 100) if total > 0 else 0
        }
