import random
import string
from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass
class MailAccount:
    username: str
    password: str
    email: str
    created_at: str
    
    def ToDict(self) -> dict:
        return {
            "username": self.username,
            "password": self.password,
            "email": self.email,
            "created_at": self.created_at
        }
    
    def ToFormattedString(self) -> str:
        return f"Email: {self.email} | Password: {self.password} | Created: {self.created_at}"


class MailGenerator:
    
    def __init__(self, domain: str, fixed_password: str = None, username_length: int = 8):
        self._domain = domain
        self._fixed_password = fixed_password
        self._username_length = username_length
    
    def GenerateUsername(self) -> str:
        chars = string.ascii_letters + string.digits
        
        username = "".join(random.choices(chars, k=self._username_length))
        
        return username
    
    def GenerateSecurePassword(self) -> str:
        lowercase = string.ascii_lowercase
        uppercase = string.ascii_uppercase
        digits = string.digits
        special = "!@#$%^&*"
        
        password_chars = [
            random.choice(lowercase),
            random.choice(uppercase),
            random.choice(digits),
            random.choice(special)
        ]
        
        all_chars = lowercase + uppercase + digits + special
        remaining_length = 12 - len(password_chars)
        password_chars.extend(random.choices(all_chars, k=remaining_length))
        
        random.shuffle(password_chars)
        return "".join(password_chars)
    
    def GenerateMailAccount(self) -> MailAccount:
        username = self.GenerateUsername()
        
        if self._fixed_password:
            password = self._fixed_password
        else:
            password = self.GenerateSecurePassword()
        
        email = f"{username}@{self._domain}"
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return MailAccount(
            username=username,
            password=password,
            email=email,
            created_at=created_at
        )
    
    def GenerateMultipleAccounts(self, count: int) -> List[MailAccount]:
        accounts = []
        generated_usernames = set()
        
        while len(accounts) < count:
            account = self.GenerateMailAccount()
            
            if account.username not in generated_usernames:
                generated_usernames.add(account.username)
                accounts.append(account)
        
        return accounts
