import os
from dataclasses import dataclass
from dotenv import load_dotenv


load_dotenv()


@dataclass
class PleskConfig:
    url: str
    username: str
    password: str
    mail_domain: str
    mail_password: str
    mail_count: int
    
    @classmethod
    def LoadFromEnv(cls) -> "PleskConfig":
        return cls(
            url=os.getenv("PLESK_URL", ""),
            username=os.getenv("PLESK_USERNAME", ""),
            password=os.getenv("PLESK_PASSWORD", ""),
            mail_domain=os.getenv("MAIL_DOMAIN", ""),
            mail_password=os.getenv("MAIL_PASSWORD", ""),
            mail_count=int(os.getenv("MAIL_COUNT", "2"))
        )
    
    def Validate(self) -> bool:
        required_fields = [self.url, self.username, self.password, self.mail_domain]
        return all(field for field in required_fields)


DEFAULT_CONFIG = PleskConfig.LoadFromEnv()
