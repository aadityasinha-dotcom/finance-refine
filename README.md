
## Prerequisites
1. Python 3.7+
2. MySQL Server 5.7+ or 8.0+
3. SEC 13F filing files (.txt format)

Installation
1. Install Python Dependencies
`pip install mysql-connector-python`

2. MySQL Setup

Option A: Fresh MySQL Installation

Ubuntu/Debian:
```
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
```

Windows:
• Download MySQL installer from mysql.com
• Run installer and follow setup wizard
• Choose "Developer Default" setup type

macOS:

```
brew install mysql
brew services start mysql
mysql_secure_installation
```


Option B: Using Existing MySQL

Make sure MySQL is running:
`systemctl status mysql    # Linux`
`brew services list mysql`

3. Database Setup
Connect to MySQL and create the database:
```
mysql -u root -p
CREATE DATABASE sec_filings CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sec_user'@'localhost' IDENTIFIED BY 'your_password_here';
GRANT ALL PRIVILEGES ON sec_filings.* TO 'sec_user'@'localhost';
FLUSH PRIVILEGES;
SHOW DATABASES;
USE sec_filings;
```

Configuration

1. Update Database Credentials
Edit the config dictionary in the script:
```
config = {
    'host': 'localhost',
    'database': 'sec_filings',
    'user': 'root',           # or 'sec_user' if you created one
    'password': 'your_password_here'
}
```

2. Set File Path
Update the file_path variable with your SEC filing location:
`file_path = '/path/to/your/sec_filing.txt'`

## Usage
#### Basic Usage
`python script.py`

Linux/Ubuntu
`python3 script.py`


bash
python sec_extractor.pypython sec_extractor.py

Prerequisites
• Python 3.7+
• MySQL Server 5.7+ or 8.0+
• SEC 13F filing files (.txt format)

Installation
1. Install Python Dependencies
`pip install mysql-connector-python`

2. MySQL Setup

Option A: Fresh MySQL Installation

Ubuntu/Debian:
```
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
```

Windows:
• Download MySQL installer from mysql.com
• Run installer and follow setup wizard
• Choose "Developer Default" setup type

macOS:

```
brew install mysql
brew services start mysql
mysql_secure_installation
```


Option B: Using Existing MySQL

Make sure MySQL is running:
`systemctl status mysql    # Linux`
`brew services list mysql`

3. Database Setup
Connect to MySQL and create the database:
```
mysql -u root -p
CREATE DATABASE sec_filings CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'sec_user'@'localhost' IDENTIFIED BY 'your_password_here';
GRANT ALL PRIVILEGES ON sec_filings.* TO 'sec_user'@'localhost';
FLUSH PRIVILEGES;
SHOW DATABASES;
USE sec_filings;
```

Configuration

1. Update Database Credentials
Edit the config dictionary in the script:
```
config = {
    'host': 'localhost',
    'database': 'sec_filings',
    'user': 'root',           # or 'sec_user' if you created one
    'password': 'your_password_here'
}
```

2. Set File Path
Update the file_path variable with your SEC filing location:
`file_path = '/path/to/your/sec_filing.txt'`

## Usage
#### Basic Usage
`python script.py`

Linux/Ubuntu
`python3 script.py`


bash
python sec_extractor.pypython sec_extractor.py
