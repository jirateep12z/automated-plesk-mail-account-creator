# Plesk Mail Auto Creator

Automated tool for creating and deleting mail accounts on Plesk Web Host Edition

## ✨ Features

### Plesk Mail Management

- ✅ Automatic login to Plesk Panel
- ✅ Create multiple mail accounts at once
- ✅ Random alphanumeric usernames (e.g., `0xK42h2w`, `Jvp6LvKc`)
- ✅ Fixed password from `.env` or auto-generate
- ✅ **Delete mail accounts** with file cleanup confirmation
- ✅ Preview mode before actual deletion
- ✅ Save data to `created_mails.txt`
- ✅ Dry-run mode support for testing

## 📋 Requirements

- Python 3.8+
- Microsoft Edge Browser
- Plesk Web Host Edition access

## 🚀 Installation

1. **Create and activate Virtual Environment:**

**Windows:**

```bash
python -m venv venv
.\venv\Scripts\Activate
```

**Mac/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

3. **Set up configuration:**

```bash
# Copy example file
copy .env.example .env

# Edit .env file with your values
```

4. **Edit `.env` file:**

```env
# Plesk Configuration
PLESK_URL=https://your-server.com:8443
PLESK_USERNAME=
PLESK_PASSWORD=

# Mail Domain
MAIL_DOMAIN=

# Fixed password for all created mail accounts
MAIL_PASSWORD=

# Number of mail accounts to create per run
MAIL_COUNT=2

```

## 💻 Usage

### Create 2 mail accounts (Default)

```bash
python main.py
```

### Create specific number of mail accounts

```bash
python main.py -c 5
```

### Dry-run mode (test without Plesk login)

```bash
python main.py --dry-run
```

### Headless mode (no browser display)

```bash
python main.py --headless
```

### Show saved mail accounts

```bash
python main.py --show-saved
```

### Delete all saved mail accounts

```bash
python main.py --delete
```

### Delete specific mail accounts

```bash
python main.py --delete-emails user1@domain.com user2@domain.com
```

### Specify different domain

```bash
python main.py -d "otherdomain.com"
```

## 🌊 Windsurf Commands

> **Note:** Windsurf uses the same credentials as Plesk (`PLESK_USERNAME` and `PLESK_PASSWORD` from `.env`)

### Cancel Windsurf subscription only

```bash
python main.py --windsurf-cancel
```

### Delete Windsurf account only

```bash
python main.py --windsurf-delete
```

### Full cleanup (Cancel + Delete)

```bash
python main.py --windsurf-full
```

### Windsurf with headless mode

```bash
python main.py --windsurf-full --headless
```

## ⚠️ Notes

- Make sure Microsoft Edge is installed
- Plesk panel must be accessible from your network
- Generated passwords include: lowercase, uppercase, numbers, and special characters
- Screenshots will be saved for debugging if errors occur

## 🔧 Troubleshooting

### Login failed

- Verify PLESK_URL is correct (including port e.g., :8443)
- Check username/password
- See screenshot `login_error.png`

### Cannot create mail

- Verify domain exists in Plesk
- Check user permissions
- See screenshot `creation_error.png`
