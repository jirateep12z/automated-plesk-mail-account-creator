import time
from typing import Optional

from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from config import PleskConfig


class WindsurfAutomation:
    DEFAULT_TIMEOUT = 15
    LOGIN_URL = "https://windsurf.com/account/login"
    MANAGE_PLAN_URL = "https://windsurf.com/subscription/manage-plan"
    CANCEL_URL = "https://windsurf.com/subscription/cancel"
    SETTINGS_URL = "https://windsurf.com/settings"
    
    def __init__(self, config: PleskConfig = None, headless: bool = False, email: str = None, password: str = None):
        self._config = config
        self._headless = headless
        self._driver: Optional[webdriver.Edge] = None
        self._is_logged_in = False
        self._email = email or (config.username if config else None)
        self._password = password or (config.password if config else None)
    
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
            self._driver.get(self.LOGIN_URL)
            print(f"[INFO] Navigating to: {self.LOGIN_URL}")
            
            wait = WebDriverWait(self._driver, self.DEFAULT_TIMEOUT)
            
            email_field = wait.until(
                EC.presence_of_element_located((By.ID, "email"))
            )
            email_field.clear()
            email_field.send_keys(self._email)
            print(f"[INFO] Filled email: {self._email}")
            
            password_field = self._driver.find_element(By.ID, "password")
            password_field.clear()
            password_field.send_keys(self._password)
            print("[INFO] Filled password")
            
            login_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Log in')]"))
            )
            login_button.click()
            print("[INFO] Clicked login button")
            
            time.sleep(5)
            
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
    
    def NavigateToManagePlan(self) -> bool:
        if not self._is_logged_in:
            print("[ERROR] Not logged in")
            return False
        
        try:
            self._driver.get(self.MANAGE_PLAN_URL)
            print(f"[INFO] Navigating to: {self.MANAGE_PLAN_URL}")
            time.sleep(3)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to navigate to manage plan: {str(e)}")
            return False
    
    def NavigateToSettings(self) -> bool:
        if not self._is_logged_in:
            print("[ERROR] Not logged in")
            return False
        
        try:
            self._driver.get(self.SETTINGS_URL)
            print(f"[INFO] Navigating to: {self.SETTINGS_URL}")
            time.sleep(3)
            return True
        except Exception as e:
            print(f"[ERROR] Failed to navigate to settings: {str(e)}")
            return False
    
    def CancelPlan(self, reason: str = "unused") -> bool:
        if not self._is_logged_in:
            print("[ERROR] Not logged in")
            return False
        
        try:
            wait = WebDriverWait(self._driver, self.DEFAULT_TIMEOUT)
            
            if not self.NavigateToManagePlan():
                return False
            
            try:
                renew_button = self._driver.find_element(
                    By.XPATH, "//button[contains(text(), 'Renew plan')]"
                )
                if renew_button:
                    print("[INFO] Found 'Renew plan' - Plan already cancelled, skipping...")
                    return True
            except NoSuchElementException:
                pass
            
            cancel_button_selectors = [
                (By.XPATH, "//a[@href='/subscription/cancel']//button[contains(text(), 'Cancel plan')]"),
                (By.XPATH, "//button[contains(text(), 'Cancel plan')]"),
                (By.CSS_SELECTOR, "a[href='/subscription/cancel'] button"),
            ]
            
            cancel_button = None
            for by, selector in cancel_button_selectors:
                try:
                    cancel_button = wait.until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    if cancel_button:
                        break
                except (TimeoutException, NoSuchElementException):
                    continue
            
            if cancel_button:
                self._driver.execute_script("arguments[0].click();", cancel_button)
                print("[INFO] Clicked Cancel plan button")
                time.sleep(3)
            else:
                self._driver.get(self.CANCEL_URL)
                print(f"[INFO] Navigating directly to: {self.CANCEL_URL}")
                time.sleep(3)
            
            reason_selectors = {
                "customer_service": "customer_service",
                "low_quality": "low_quality",
                "missing_features": "missing_features",
                "switched_service": "switched_service",
                "too_complex": "too_complex",
                "too_expensive": "too_expensive",
                "unused": "unused",
                "other": "other"
            }
            
            reason_value = reason_selectors.get(reason.lower(), "unused")
            
            reason_radio = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"input[type='radio'][value='{reason_value}']"))
            )
            self._driver.execute_script("arguments[0].click();", reason_radio)
            print(f"[INFO] Selected reason: {reason_value}")
            time.sleep(1)
            
            submit_button = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and contains(text(), 'Cancel plan')]"))
            )
            self._driver.execute_script("arguments[0].click();", submit_button)
            print("[INFO] Clicked submit Cancel plan button")
            time.sleep(3)
            
            print("[SUCCESS] Plan cancellation submitted")
            return True
            
        except TimeoutException:
            print("[ERROR] Cancel plan timeout - elements not found")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to cancel plan: {str(e)}")
            return False
    
    def DeleteAccount(self) -> bool:
        if not self._is_logged_in:
            print("[ERROR] Not logged in")
            return False
        
        try:
            wait = WebDriverWait(self._driver, self.DEFAULT_TIMEOUT)
            
            if not self.NavigateToSettings():
                return False
            
            delete_button_selectors = [
                (By.XPATH, "//button[contains(text(), 'Delete account')]"),
                (By.CSS_SELECTOR, "button.text-sk-error"),
            ]
            
            delete_button = None
            for by, selector in delete_button_selectors:
                try:
                    buttons = self._driver.find_elements(by, selector)
                    for btn in buttons:
                        if "Delete account" in btn.text:
                            delete_button = btn
                            break
                    if delete_button:
                        break
                except NoSuchElementException:
                    continue
            
            if not delete_button:
                print("[ERROR] Delete account button not found")
                return False
            
            self._driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", delete_button)
            time.sleep(1)
            self._driver.execute_script("arguments[0].click();", delete_button)
            print("[INFO] Clicked Delete account button")
            time.sleep(2)
            
            confirm_input = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[placeholder*='DELETE MY ACCOUNT']"))
            )
            confirm_input.clear()
            confirm_input.send_keys("DELETE MY ACCOUNT")
            print("[INFO] Typed confirmation text: DELETE MY ACCOUNT")
            time.sleep(1)
            
            confirm_delete_button_selectors = [
                (By.XPATH, "//div[contains(@class, 'rounded-lg')]//button[contains(@class, 'bg-sk-error') and contains(text(), 'Delete account')]"),
                (By.CSS_SELECTOR, "button.bg-sk-error\\/80"),
                (By.XPATH, "//button[contains(@class, 'bg-sk-error') and contains(text(), 'Delete account')]"),
            ]
            
            confirm_delete_button = None
            for by, selector in confirm_delete_button_selectors:
                try:
                    buttons = self._driver.find_elements(by, selector)
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            confirm_delete_button = btn
                            break
                    if confirm_delete_button:
                        break
                except NoSuchElementException:
                    continue
            
            if not confirm_delete_button:
                all_delete_buttons = self._driver.find_elements(By.XPATH, "//button[contains(text(), 'Delete account')]")
                for btn in all_delete_buttons:
                    try:
                        if btn.is_displayed() and btn.is_enabled():
                            parent = btn.find_element(By.XPATH, "./ancestor::div[contains(@class, 'rounded-lg')]")
                            if parent:
                                confirm_delete_button = btn
                                break
                    except NoSuchElementException:
                        continue
            
            if confirm_delete_button:
                time.sleep(1)
                self._driver.execute_script("arguments[0].click();", confirm_delete_button)
                print("[INFO] Clicked confirm Delete account button")
                time.sleep(5)
                print("[SUCCESS] Account deletion initiated")
                return True
            else:
                print("[ERROR] Confirm delete button not found or not enabled")
                return False
            
        except TimeoutException:
            print("[ERROR] Delete account timeout - elements not found")
            return False
        except Exception as e:
            print(f"[ERROR] Failed to delete account: {str(e)}")
            return False
    
    def CancelAndDeleteAccount(self, cancel_reason: str = "unused") -> bool:
        print("\n" + "=" * 60)
        print("[WINDSURF] Starting Cancel Plan and Delete Account process")
        print("=" * 60)
        
        print("\n[STEP 1/3] Cancelling plan...")
        cancel_result = self.CancelPlan(reason=cancel_reason)
        
        if cancel_result:
            print("[STEP 1/3] Plan cancellation: SUCCESS")
        else:
            print("[STEP 1/3] Plan cancellation: FAILED (continuing with delete)")
        
        time.sleep(2)
        
        print("\n[STEP 2/3] Deleting account...")
        delete_result = self.DeleteAccount()
        
        if delete_result:
            print("[STEP 2/3] Account deletion: SUCCESS")
        else:
            print("[STEP 2/3] Account deletion: FAILED")
        
        print("\n" + "=" * 60)
        print("[WINDSURF] Process completed")
        print(f"  - Cancel Plan: {'SUCCESS' if cancel_result else 'FAILED'}")
        print(f"  - Delete Account: {'SUCCESS' if delete_result else 'FAILED'}")
        print("=" * 60)
        
        return cancel_result and delete_result
    
    def TakeScreenshot(self, filename: str = "windsurf_screenshot.png") -> str:
        if self._driver:
            self._driver.save_screenshot(filename)
            print(f"[INFO] Screenshot saved: {filename}")
            return filename
        return ""
