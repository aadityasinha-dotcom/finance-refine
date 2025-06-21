SEC 13F Data Extractor
This tool extracts and processes SEC 13F filings into a MySQL database for analysis. It parses company
information and holdings data from SEC filing text files.

Prerequisites
• Python 3.7+
• MySQL Server 5.7+ or 8.0+
• SEC 13F filing files (.txt format)

Installation
1. Install Python Dependencies
2. MySQL Setup
3. 
Option A: Fresh MySQL Installation
Ubuntu/Debian:
Windows:
• Download MySQL installer from mysql.com
• Run installer and follow setup wizard
• Choose "Developer Default" setup type
macOS:

`pip install mysql-connector-pythonmysql-connector-python`

```
sudosudo aptapt updateupdate
sudo apt install mysql-server=
sudo mysql_secure_installation
```

```
brew install mysql
brew services start mysql
mysql_secure_install
```

Option B: Using Existing MySQL
Make sure MySQL is running:
`systemctl status mysql    # Linux`
`brew services list mysql`

3. Database Setup
Connect to MySQL and create the database:
Configuration
1. Update Database Credentials
Edit the config dictionary in the script:
2. Set File Path


# Check if MySQL is running# Check if MySQL is running
systemctl status mysqlsystemctl status mysql # Linux# Linux
brew services list mysqlbrew services list mysql # macOS# macOS
sql
mysqlmysql --u rootu root --pp
-- Create database-- Create database
CREATECREATE DATABASEDATABASE sec_filingssec_filings CHARACTERCHARACTER SETSET utf8mb4utf8mb4 COLLATECOLLATE utf8mb4_unicode_ciutf8mb4_unicode_ci;;
-- Create user (optional, for security)-- Create user (optional, for security)
CREATECREATE USERUSER 'sec_user''sec_user'@'localhost'@'localhost' IDENTIFIEDIDENTIFIED BYBY 'your_password_here''your_password_here';;
GRANTGRANT ALLALL PRIVILEGESPRIVILEGES ONON sec_filingssec_filings..** TOTO 'sec_user''sec_user'@'localhost'@'localhost';;
FLUSHFLUSH PRIVILEGESPRIVILEGES;;
-- Verify database creation-- Verify database creation
SHOWSHOW DATABASESDATABASES;;
USEUSE sec_filingssec_filings;;
python
configconfig == {{
'host''host':: 'localhost''localhost',,
'database''database':: 'sec_filings''sec_filings',,
'user''user':: 'root''root',, # or 'sec_user' if you created one# or 'sec_user' if you created one
'password''password':: 'your_password_here''your_password_here'
}}
Update the file_path variable with your SEC filing location:
Usage
Basic Usage
Processing Multiple Files
Modify the script to process multiple files:
Command Line Arguments (Optional Enhancement)
You can modify the script to accept command line arguments:
python
file_pathfile_path == '/path/to/your/sec_filing.txt''/path/to/your/sec_filing.txt'
bash
python sec_extractor.pypython sec_extractor.py
