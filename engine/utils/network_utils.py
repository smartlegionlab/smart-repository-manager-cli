# Copyright (©) 2025, Alexander Suvorov. All rights reserved.
import requests
import socket
from typing import Optional
import ipaddress


class NetworkUtils:
    @staticmethod
    def get_external_ip() -> Optional[str]:
        ip_services = [
            "https://api.ipify.org",
            "https://icanhazip.com",
            "https://ident.me",
            "https://checkip.amazonaws.com",
            "https://ifconfig.me/ip"
        ]

        for service in ip_services:
            try:
                response = requests.get(service, timeout=3)
                if response.status_code == 200:
                    ip = response.text.strip()
                    if NetworkUtils.is_valid_ip(ip):
                        return ip
            except Exception as e:
                print(e)
                continue

        try:
            hostname = socket.gethostname()
            ip_address = socket.gethostbyname(hostname)
            if NetworkUtils.is_valid_ip(ip_address):
                return f"{ip_address} (local)"
        except Exception as e:
            print(e)
            pass

        return None

    @staticmethod
    def is_valid_ip(ip: str) -> bool:
        try:
            clean_ip = ip.split(' ')[0]
            ipaddress.ip_address(clean_ip)
            return True
        except ValueError:
            return False
