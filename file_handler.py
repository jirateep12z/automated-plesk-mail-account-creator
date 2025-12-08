import os
import re
from datetime import datetime
from typing import List, Tuple

from mail_generator import MailAccount


class FileHandler:
    DEFAULT_FILE_NAME = "created_mails.txt"
    
    def __init__(self, output_dir: str = None):
        self._output_dir = output_dir or os.path.dirname(os.path.abspath(__file__))
        self._file_path = os.path.join(self._output_dir, self.DEFAULT_FILE_NAME)
    
    @property
    def file_path(self) -> str:
        return self._file_path
    
    def SaveAccounts(self, accounts: List[MailAccount], append: bool = True) -> str:
        mode = "a" if append else "w"
        
        with open(self._file_path, mode, encoding="utf-8") as file:
            if append and os.path.exists(self._file_path) and os.path.getsize(self._file_path) > 0:
                file.write("\n")
                file.write("=" * 60 + "\n")
            
            file.write(f"Batch Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            file.write("-" * 60 + "\n")
            
            for idx, account in enumerate(accounts, 1):
                file.write(f"{idx}. {account.ToFormattedString()}\n")
            
            file.write("-" * 60 + "\n")
        
        return self._file_path
    
    def ReadAllAccounts(self) -> str:
        if not os.path.exists(self._file_path):
            return "No accounts found. File does not exist."
        
        with open(self._file_path, "r", encoding="utf-8") as file:
            return file.read()
    
    def ClearFile(self) -> None:
        if os.path.exists(self._file_path):
            os.remove(self._file_path)
    
    def ParseAccountsFromFile(self) -> List[Tuple[str, str]]:
        accounts: List[Tuple[str, str]] = []
        
        if not os.path.exists(self._file_path):
            return accounts
        
        pattern = r"Email:\s*([^\s|]+)\s*\|\s*Password:\s*([^\s|]+)"
        
        with open(self._file_path, "r", encoding="utf-8") as file:
            for line in file:
                match = re.search(pattern, line)
                if match:
                    email = match.group(1).strip()
                    password = match.group(2).strip()
                    accounts.append((email, password))
        
        return accounts
