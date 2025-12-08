import time
from typing import List, Optional

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from config import PleskConfig
from mail_generator import MailAccount

class PleskAutomation:
    DEFAULT_TIMEOUT = 10
    MAIL_PAGE_PATH = "/smb/email-address/list"
    MAIL_CREATE_PATH = "/smb/email-address/create"
    
    def __init__(self, config: PleskConfig, headless: bool = False):
        self._config = config
        self._headless = headless
        self._driver: Optional[webdriver.Edge] = None
        self._is_logged_in = False
    
    def _InitDriver(self) -> webdriver.Edge:
        edge_options = Options()
        
        if self._headless:
            edge_options.add_argument("--headless=new")
        
        edge_options.add_argument("--no-sandbox")
        edge_options.add_argument("--disable-dev-shm-usage")
        edge_options.add_argument("--disable-gpu")
        edge_options.add_argument("--window-size=1920,1080")
        edge_options.add_argument("--ignore-certificate-errors")
        edge_options.add_argument("--ignore-ssl-errors")
        
        try:
            service = Service(EdgeChromiumDriverManager().install())
            return webdriver.Edge(service=service, options=edge_options)
        except Exception:
            print("[INFO] Using system Edge driver...")
            return webdriver.Edge(options=edge_options)
    
    def Start(self) -> None:
        if self._driver is None:
            self._driver = self._InitDriver()
            print("[INFO] Browser started successfully")
    
    def Stop(self) -> None:
        if self._driver:
            self._driver.quit()
            self._driver = None
            self._is_logged_in = False
            print("[INFO] Browser closed")
    
    def Login(self) -> bool:
        if self._driver is None:
            self.Start()
        
        try:
            login_url = f"{self._config.url}/login_up.php"
            self._driver.get(login_url)
            print(f"[INFO] Navigating to: {login_url}")
            
            wait = WebDriverWait(self._driver, self.DEFAULT_TIMEOUT)
            
            username_field = wait.until(
                EC.presence_of_element_located((By.ID, "login_name"))
            )
            username_field.clear()
            username_field.send_keys(self._config.username)
            
            password_field = self._driver.find_element(By.ID, "passwd")
            password_field.clear()
            password_field.send_keys(self._config.password)
            
            login_button = self._driver.find_element(
                By.CSS_SELECTOR, "button[data-action='log-in']"
            )
            login_button.click()
            
            time.sleep(3)
            
            if "/login" not in self._driver.current_url.lower():
                self._is_logged_in = True
                print("[SUCCESS] Login successful")
                return True
            else:
                print("[ERROR] Login failed - still on login page")
                return False
                
        except TimeoutException:
            print("[ERROR] Login timeout - elements not found")
            return False
        except Exception as e:
            print(f"[ERROR] Login failed: {str(e)}")
            return False
    
    def NavigateToMailSection(self) -> bool:
        if not self._is_logged_in:
            print("[ERROR] Not logged in")
            return False
        
        try:
            mail_url = f"{self._config.url}{self.MAIL_PAGE_PATH}"
            self._driver.get(mail_url)
            print(f"[INFO] Navigating to mail section: {mail_url}")
            
            time.sleep(2)
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to navigate to mail section: {str(e)}")
            return False
    
    def CreateMailAccount(self, account: MailAccount) -> bool:
        if not self._is_logged_in:
            print("[ERROR] Not logged in")
            return False
        
        try:
            wait = WebDriverWait(self._driver, self.DEFAULT_TIMEOUT)
            
            create_url = f"{self._config.url}{self.MAIL_CREATE_PATH}"
            self._driver.get(create_url)
            print(f"[INFO] Navigating to create page: {create_url}")
            time.sleep(2)
            
            email_input = wait.until(
                EC.presence_of_element_located((By.ID, "general-generalSection-name"))
            )
            email_input.clear()
            email_input.send_keys(account.username)
            print(f"[INFO] Filled email: {account.username}")
            
            password_input = self._driver.find_element(By.ID, "general-generalSection-password")
            password_input.clear()
            password_input.send_keys(account.password)
            print("[INFO] Filled password")
            
            confirm_input = self._driver.find_element(By.ID, "general-generalSection-passwordConfirmation")
            confirm_input.clear()
            confirm_input.send_keys(account.password)
            print("[INFO] Filled password confirmation")
            
            time.sleep(1)
            
            submit_button = None
            submit_selectors = [
                (By.CSS_SELECTOR, "button.btn-primary[type='submit']"),
                (By.CSS_SELECTOR, "input.btn-primary[type='submit']"),
                (By.CSS_SELECTOR, "#btn-send"),
                (By.XPATH, "//button[contains(@class, 'btn') and (contains(text(), 'OK') or contains(text(), 'Save'))]"),
                (By.CSS_SELECTOR, "button[name='send']"),
                (By.CSS_SELECTOR, ".btn-action input[type='submit']"),
            ]
            
            for by, selector in submit_selectors:
                try:
                    submit_button = self._driver.find_element(by, selector)
                    if submit_button:
                        break
                except NoSuchElementException:
                    continue
            
            if submit_button:
                submit_button.click()
                time.sleep(3)
                print(f"[SUCCESS] Created mail account: {account.email}")
                return True
            else:
                from selenium.webdriver.common.keys import Keys
                confirm_input.send_keys(Keys.RETURN)
                time.sleep(3)
                print(f"[SUCCESS] Created mail account: {account.email}")
                return True
                
        except Exception as e:
            print(f"[ERROR] Failed to create mail account: {str(e)}")
            return False
    
    def CreateMultipleAccounts(self, accounts: List[MailAccount]) -> List[MailAccount]:
        if not self.NavigateToMailSection():
            return []
        
        successful_accounts = []
        
        for account in accounts:
            if self.CreateMailAccount(account):
                successful_accounts.append(account)
            
            self.NavigateToMailSection()
            time.sleep(1)
        
        return successful_accounts
    
    def DeleteMailAccountsByEmail(self, emails: List[str], preview_only: bool = False) -> int:
        if not self._is_logged_in:
            print("[ERROR] Not logged in")
            return 0
        
        if not self.NavigateToMailSection():
            return 0
        
        try:
            wait = WebDriverWait(self._driver, self.DEFAULT_TIMEOUT)
            time.sleep(2)
            
            deleted_count = 0
            
            self._driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            rows = self._driver.find_elements(By.CSS_SELECTOR, "table.pul-list__table tbody tr")
            
            for row in rows:
                try:
                    email_link = row.find_element(By.CSS_SELECTOR, "td.pul-list__cell-title a")
                    row_email = email_link.text.strip()
                    
                    if row_email in emails:
                        checkbox = row.find_element(By.CSS_SELECTOR, "input.pul-checkbox__input[type='checkbox']")
                        
                        self._driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", checkbox)
                        time.sleep(0.3)
                        
                        if not checkbox.is_selected():
                            self._driver.execute_script("arguments[0].click();", checkbox)
                            print(f"[INFO] Selected: {row_email}")
                            deleted_count += 1
                            time.sleep(0.3)
                except NoSuchElementException:
                    continue
            
            if deleted_count > 0:
                if preview_only:
                    print(f"[PREVIEW] Selected {deleted_count} email(s) - waiting for review...")
                    return deleted_count
                
                self._driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(1)
                
                remove_button = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "button.sb-remove-selected"))
                )
                self._driver.execute_script("arguments[0].click();", remove_button)
                print(f"[INFO] Clicked Remove button")
                
                time.sleep(2)
                
                confirm_selectors = [
                    (By.CSS_SELECTOR, "div.pul-popover button.pul-button--danger"),
                    (By.XPATH, "//button[contains(@class, 'pul-button--danger')]"),
                    (By.XPATH, "//button[contains(., 'Yes, remove')]"),
                    (By.XPATH, "//button[contains(., 'Yes')]"),
                ]
                
                confirmed = False
                for by, selector in confirm_selectors:
                    try:
                        confirm_btns = self._driver.find_elements(by, selector)
                        for confirm_btn in confirm_btns:
                            if confirm_btn.is_displayed():
                                self._driver.execute_script("arguments[0].click();", confirm_btn)
                                print("[INFO] Confirmed deletion - clicked 'Yes, remove'")
                                confirmed = True
                                time.sleep(3)
                                break
                        if confirmed:
                            break
                    except NoSuchElementException:
                        continue
                
                if not confirmed:
                    print("[WARNING] Could not find confirmation button")
                
                print(f"[SUCCESS] Deleted {deleted_count} mail account(s)")
            else:
                print("[WARNING] No matching emails found to delete")
            
            return deleted_count
            
        except Exception as e:
            print(f"[ERROR] Failed to delete mail accounts: {str(e)}")
            return 0
    
    def DeleteAllCreatedMails(self, file_path: str, preview_only: bool = False) -> int:
        import re
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            email_pattern = r'Email:\s*(\S+@\S+)'
            emails = re.findall(email_pattern, content)
            
            if not emails:
                print("[WARNING] No emails found in file")
                return 0
            
            print(f"[INFO] Found {len(emails)} email(s) to process")
            return self.DeleteMailAccountsByEmail(emails, preview_only=preview_only)
            
        except FileNotFoundError:
            print(f"[ERROR] File not found: {file_path}")
            return 0
        except Exception as e:
            print(f"[ERROR] Failed to read file: {str(e)}")
            return 0
    
    def TakeScreenshot(self, filename: str = "screenshot.png") -> str:
        if self._driver:
            self._driver.save_screenshot(filename)
            return filename
        return ""
