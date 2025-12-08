import argparse
import sys
from typing import Optional

from config import PleskConfig, DEFAULT_CONFIG
from mail_generator import MailGenerator
from file_handler import FileHandler
from plesk_automation import PleskAutomation
from windsurf_automation import WindsurfAutomation

def ParseArguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Automated Plesk Mail Account Creator"
    )
    
    parser.add_argument(
        "-c", "--count",
        type=int,
        default=2,
        help="Number of mail accounts to create (default: 2)"
    )
    
    parser.add_argument(
        "-d", "--domain",
        type=str,
        help="Mail domain (overrides .env setting)"
    )
    
    parser.add_argument(
        "-u", "--url",
        type=str,
        help="Plesk URL (overrides .env setting)"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate accounts without creating them in Plesk"
    )
    
    parser.add_argument(
        "--show-saved",
        action="store_true",
        help="Show all previously saved accounts"
    )
    
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Delete all mail accounts saved in created_mails.txt"
    )
    
    parser.add_argument(
        "--delete-emails",
        type=str,
        nargs="+",
        help="Delete specific email addresses (space separated)"
    )
    
    parser.add_argument(
        "--delete-preview",
        action="store_true",
        help="Preview delete - select emails but don't confirm deletion"
    )
    
    parser.add_argument(
        "--windsurf-cancel",
        action="store_true",
        help="Cancel Windsurf subscription plan"
    )
    
    parser.add_argument(
        "--windsurf-delete",
        action="store_true",
        help="Delete Windsurf account"
    )
    
    parser.add_argument(
        "--windsurf-full",
        action="store_true",
        help="Cancel plan and delete Windsurf account (full cleanup)"
    )
    
    return parser.parse_args()


def RunDryMode(config: PleskConfig, count: int) -> None:
    print("\n[DRY RUN MODE] Generating accounts without Plesk integration\n")
    
    generator = MailGenerator(domain=config.mail_domain, fixed_password=config.mail_password)
    file_handler = FileHandler()
    
    accounts = generator.GenerateMultipleAccounts(count)
    
    print(f"Generated {len(accounts)} mail account(s):\n")
    print("-" * 60)
    
    for idx, account in enumerate(accounts, 1):
        print(f"{idx}. Email: {account.email}")
        print(f"   Password: {account.password}")
        print(f"   Created: {account.created_at}")
        print()
    
    saved_path = file_handler.SaveAccounts(accounts)
    print("-" * 60)
    print(f"\n[SAVED] Accounts saved to: {saved_path}")


def RunFullMode(config: PleskConfig, count: int, headless: bool) -> None:
    print("\n[FULL MODE] Creating accounts in Plesk\n")
    
    generator = MailGenerator(domain=config.mail_domain, fixed_password=config.mail_password)
    file_handler = FileHandler()
    automation = PleskAutomation(config=config, headless=headless)
    
    try:
        accounts = generator.GenerateMultipleAccounts(count)
        
        print(f"Generated {len(accounts)} account(s) to create:\n")
        for account in accounts:
            print(f"  - {account.email}")
        print()
        
        automation.Start()
        
        if not automation.Login():
            print("\n[ERROR] Failed to login to Plesk. Aborting.")
            automation.TakeScreenshot("login_error.png")
            return
        
        successful_accounts = automation.CreateMultipleAccounts(accounts)
        
        if successful_accounts:
            saved_path = file_handler.SaveAccounts(successful_accounts)
            
            print("\n" + "=" * 60)
            print(f"[SUCCESS] Created {len(successful_accounts)}/{len(accounts)} account(s)")
            print(f"[SAVED] Accounts saved to: {saved_path}")
            print("=" * 60)
            
            print("\nCreated accounts:")
            for account in successful_accounts:
                print(f"  - {account.email} | Password: {account.password}")
        else:
            print("\n[WARNING] No accounts were created successfully")
            automation.TakeScreenshot("creation_error.png")
            
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {str(e)}")
        automation.TakeScreenshot("error.png")
    finally:
        automation.Stop()


def ShowSavedAccounts() -> None:
    file_handler = FileHandler()
    print("\n" + "=" * 60)
    print("SAVED MAIL ACCOUNTS")
    print("=" * 60 + "\n")
    print(file_handler.ReadAllAccounts())


def RunWindsurfMode(config: PleskConfig, headless: bool, mode: str = "full") -> None:
    print("\n[WINDSURF MODE] Managing Windsurf accounts\n")
    
    file_handler = FileHandler()
    accounts = file_handler.ParseAccountsFromFile()
    
    if not accounts:
        print("[ERROR] No accounts found in created_mails.txt")
        print("[INFO] Please create mail accounts first using: python main.py -c <count>")
        return
    
    print(f"[INFO] Found {len(accounts)} account(s) in created_mails.txt:")
    for idx, (email, _) in enumerate(accounts, 1):
        print(f"  {idx}. {email}")
    print()
    
    success_count = 0
    fail_count = 0
    
    for idx, (email, password) in enumerate(accounts, 1):
        print(f"\n{'=' * 60}")
        print(f"[ACCOUNT {idx}/{len(accounts)}] Processing: {email}")
        print("=" * 60)
        
        automation = WindsurfAutomation(headless=headless, email=email, password=password)
        
        try:
            automation.Start()
            
            if not automation.Login():
                print(f"\n[ERROR] Failed to login to Windsurf for: {email}")
                automation.TakeScreenshot(f"windsurf_login_error_{idx}.png")
                fail_count += 1
                continue
            
            if mode == "cancel":
                print("\n[ACTION] Cancelling Windsurf plan...")
                result = automation.CancelPlan(reason="unused")
                if result:
                    print("[SUCCESS] Plan cancelled successfully")
                    success_count += 1
                else:
                    print("[ERROR] Failed to cancel plan")
                    automation.TakeScreenshot(f"windsurf_cancel_error_{idx}.png")
                    fail_count += 1
                    
            elif mode == "delete":
                print("\n[ACTION] Deleting Windsurf account...")
                result = automation.DeleteAccount()
                if result:
                    print("[SUCCESS] Account deleted successfully")
                    success_count += 1
                else:
                    print("[ERROR] Failed to delete account")
                    automation.TakeScreenshot(f"windsurf_delete_error_{idx}.png")
                    fail_count += 1
                    
            elif mode == "full":
                print("\n[ACTION] Full cleanup - Cancel plan and Delete account...")
                result = automation.CancelAndDeleteAccount(cancel_reason="unused")
                if result:
                    print("[SUCCESS] Full cleanup completed successfully")
                    success_count += 1
                else:
                    print("[WARNING] Some operations may have failed. Check logs above.")
                    automation.TakeScreenshot(f"windsurf_full_error_{idx}.png")
                    fail_count += 1
            
        except Exception as e:
            print(f"\n[ERROR] An error occurred: {str(e)}")
            automation.TakeScreenshot(f"windsurf_error_{idx}.png")
            fail_count += 1
        finally:
            automation.Stop()
    
    print(f"\n{'=' * 60}")
    print("[WINDSURF MODE] Summary")
    print(f"  - Total accounts: {len(accounts)}")
    print(f"  - Success: {success_count}")
    print(f"  - Failed: {fail_count}")
    print("=" * 60)


def RunDeleteMode(config: PleskConfig, headless: bool, emails: list = None, preview_only: bool = False) -> None:
    if preview_only:
        print("\n[DELETE PREVIEW MODE] Select emails only - will NOT delete\n")
    else:
        print("\n[DELETE MODE] Deleting mail accounts from Plesk\n")
    
    file_handler = FileHandler()
    automation = PleskAutomation(config=config, headless=headless)
    
    try:
        automation.Start()
        
        if not automation.Login():
            print("\n[ERROR] Failed to login to Plesk. Aborting.")
            automation.TakeScreenshot("login_error.png")
            return
        
        if emails:
            print(f"Emails to process: {emails}")
            deleted_count = automation.DeleteMailAccountsByEmail(emails, preview_only=preview_only)
        else:
            deleted_count = automation.DeleteAllCreatedMails(file_handler.file_path, preview_only=preview_only)
        
        print("\n" + "=" * 60)
        if preview_only:
            print(f"[PREVIEW] Selected {deleted_count} mail account(s) - NOT deleted")
            print("[INFO] Check browser to see selected items")
            input("[PRESS ENTER to close browser...]")
        else:
            print(f"[RESULT] Deleted {deleted_count} mail account(s)")
            
            if deleted_count > 0 and not emails:
                print("=" * 60)
                clear_choice = input("\n[?] ต้องการล้างไฟล์ created_mails.txt ด้วยไหม? (y/n): ").strip().lower()
                if clear_choice in ['y', 'yes']:
                    file_handler.ClearFile()
                    print("[INFO] ล้างไฟล์ created_mails.txt เรียบร้อยแล้ว")
                else:
                    print("[INFO] เก็บไฟล์ created_mails.txt ไว้")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] An error occurred: {str(e)}")
        automation.TakeScreenshot("delete_error.png")
    finally:
        automation.Stop()


def ValidateConfig(config: PleskConfig, is_dry_run: bool) -> bool:
    if not config.mail_domain:
        print("[ERROR] Mail domain is not configured. Please set MAIL_DOMAIN in .env file")
        return False
    
    if not is_dry_run:
        if not config.url:
            print("[ERROR] Plesk URL is not configured. Please set PLESK_URL in .env file")
            return False
        if not config.username or not config.password:
            print("[ERROR] Plesk credentials not configured. Please set PLESK_USERNAME and PLESK_PASSWORD in .env file")
            return False
    
    return True


def ValidateWindsurfConfig(config: PleskConfig) -> bool:
    if not config.username or not config.password:
        print("[ERROR] Credentials not configured. Please set PLESK_USERNAME and PLESK_PASSWORD in .env file")
        print("[INFO] Windsurf uses the same email/password as Plesk configuration")
        return False
    return True


def Main() -> None:
    args = ParseArguments()
    
    if args.show_saved:
        ShowSavedAccounts()
        return
    
    config = PleskConfig.LoadFromEnv()
    
    if args.windsurf_cancel or args.windsurf_delete or args.windsurf_full:
        print(f"Configuration:")
        print(f"  - Source: created_mails.txt")
        print(f"  - Headless: {args.headless}")
        
        if args.windsurf_full:
            print(f"  - Mode: Full cleanup (Cancel + Delete)")
            RunWindsurfMode(config, args.headless, mode="full")
        elif args.windsurf_cancel:
            print(f"  - Mode: Cancel plan only")
            RunWindsurfMode(config, args.headless, mode="cancel")
        elif args.windsurf_delete:
            print(f"  - Mode: Delete account only")
            RunWindsurfMode(config, args.headless, mode="delete")
        
        print("\n[DONE] Windsurf process completed\n")
        return
    
    if args.delete or args.delete_emails or args.delete_preview:
        if args.domain:
            config.mail_domain = args.domain
        if args.url:
            config.url = args.url
        
        if not ValidateConfig(config, False):
            sys.exit(1)
        
        print(f"Configuration:")
        print(f"  - Plesk URL: {config.url}")
        print(f"  - Headless: {args.headless}")
        print(f"  - Preview only: {args.delete_preview}")
        
        RunDeleteMode(config, args.headless, args.delete_emails, preview_only=args.delete_preview)
        print("\n[DONE] Process completed\n")
        return
    
    if args.domain:
        config.mail_domain = args.domain
    if args.url:
        config.url = args.url
    
    count = args.count
    
    if not ValidateConfig(config, args.dry_run):
        sys.exit(1)
    
    print(f"Configuration:")
    print(f"  - Domain: {config.mail_domain}")
    print(f"  - Accounts to create: {count}")
    
    if not args.dry_run:
        print(f"  - Plesk URL: {config.url}")
        print(f"  - Headless: {args.headless}")
    
    print()
    
    if args.dry_run:
        RunDryMode(config, count)
    else:
        RunFullMode(config, count, args.headless)
    
    print("\n[DONE] Process completed\n")


if __name__ == "__main__":
    Main()
