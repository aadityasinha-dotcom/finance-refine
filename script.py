import re
import mysql.connector
from mysql.connector import Error
from datetime import datetime
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SEC13FProcessor:
    def __init__(self, host='localhost', database='sec_filings', user='root', password=''):
        self.db_config = {
            'host': host,
            'database': database,
            'user': user,
            'password': password
        }
        self.conn = None
        
    def connect_db(self):
        """Connect to MySQL database"""
        try:
            self.conn = mysql.connector.connect(**self.db_config)
            if self.conn.is_connected():
                logger.info(f"Connected to database: {self.db_config['database']}")
                return True
        except Error as e:
            logger.error(f"Database connection failed: {e}")
            return False
    
    def setup_tables(self):
        """Create database tables if they don't exist"""
        cursor = self.conn.cursor()
        
        company_table = """
        CREATE TABLE IF NOT EXISTS company_info (
            id INT AUTO_INCREMENT PRIMARY KEY,
            company_name VARCHAR(255) NOT NULL,
            cik VARCHAR(20) NOT NULL,
            irs_number VARCHAR(20),
            state VARCHAR(5),
            form_type VARCHAR(10),
            report_period DATE,
            filing_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            INDEX idx_cik (cik),
            INDEX idx_filing_date (filing_date)
        )
        """
        
        holdings_table = """
        CREATE TABLE IF NOT EXISTS holdings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            company_id INT,
            issuer_name VARCHAR(255),
            title_class VARCHAR(100),
            cusip VARCHAR(20),
            value_thousands DECIMAL(15,2),
            shares BIGINT,
            share_type VARCHAR(10),
            put_call VARCHAR(10),
            discretion VARCHAR(20),
            other_manager VARCHAR(255),
            vote_sole BIGINT,
            vote_shared BIGINT,
            vote_none BIGINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES company_info(id),
            INDEX idx_cusip (cusip),
            INDEX idx_company (company_id)
        )
        """
        
        cursor.execute(company_table)
        cursor.execute(holdings_table)
        self.conn.commit()
        logger.info("Database tables ready")
    
    def parse_company_data(self, content):
        """Extract company information from filing header"""
        patterns = {
            'company_name': r'COMPANY CONFORMED NAME:\s+(.+)',
            'cik': r'CENTRAL INDEX KEY:\s+(\d+)',
            'irs_number': r'IRS NUMBER:\s+(\d+)',
            'state': r'STATE OF INCORPORATION:\s+([A-Z]{2})',
            'form_type': r'FORM TYPE:\s+([A-Z0-9-]+)',
            'filing_date': r'FILED AS OF DATE:\s+(\d{8})'
        }
        
        company_data = {}
        
        for field, pattern in patterns.items():
            match = re.search(pattern, content)
            if match:
                value = match.group(1).strip()
                if field == 'filing_date':
                    try:
                        company_data[field] = datetime.strptime(value, '%Y%m%d').date()
                    except ValueError:
                        logger.warning(f"Invalid filing date format: {value}")
                else:
                    company_data[field] = value
        
        # Extract report period
        period_match = re.search(r'Report for the Calendar Year or Quarter Ended:\s+(.+)', content)
        if period_match:
            period_str = period_match.group(1).strip()
            try:
                company_data['report_period'] = datetime.strptime(period_str, '%B %d, %Y').date()
            except ValueError:
                logger.warning(f"Could not parse report period: {period_str}")
        
        return company_data
    
    def find_table_section(self, content):
        """Locate the holdings table in the filing"""
        table_start = content.find('<TABLE>')
        table_end = content.find('</TABLE>')
        
        if table_start == -1 or table_end == -1:
            logger.warning("No <TABLE> tags found, searching for alternative markers")
            # Look for other table indicators
            alt_markers = ['Name of Issuer', 'CUSIP', 'Column 1']
            for marker in alt_markers:
                pos = content.find(marker)
                if pos != -1:
                    table_start = pos
                    table_end = len(content)
                    break
        
        if table_start == -1:
            return None
            
        return content[table_start:table_end]
    
    def parse_holdings_table(self, table_content):
        """Extract holdings from table section"""
        lines = [line.strip() for line in table_content.split('\n') if line.strip()]
        holdings = []
        
        # Skip header lines and find data start
        data_start = 0
        for i, line in enumerate(lines):
            if any(marker in line for marker in ['----', 'Name of Issuer']):
                data_start = i + 1
                break
        
        # Process each line
        for line in lines[data_start:]:
            if self._is_data_line(line):
                holding = self._parse_holding_line(line)
                if holding:
                    holdings.append(holding)
        
        logger.info(f"Parsed {len(holdings)} holdings from table")
        return holdings
    
    def _is_data_line(self, line):
        """Check if line contains holdings data"""
        if (not line or 
            len(line) < 20 or
            line.startswith(('Column', 'Name of Issuer', '----', 'Grand Total', 'Total'))):
            return False
        
        # Must contain CUSIP-like pattern and numbers
        return bool(re.search(r'[A-Z0-9]{9}', line) and re.search(r'\d{3,}', line))
    
    def _parse_holding_line(self, line):
        """Parse individual holding line with multiple strategies"""
        # Strategy 1: Fixed width parsing
        if len(line) > 80:
            result = self._parse_fixed_width(line)
            if result:
                return result
        
        # Strategy 2: Regex pattern matching
        result = self._parse_with_regex(line)
        if result:
            return result
        
        # Strategy 3: Split and extract
        return self._parse_by_splitting(line)
    
    def _parse_fixed_width(self, line):
        """Parse assuming fixed column widths"""
        try:
            issuer = line[0:28].strip()
            title = line[28:40].strip() or 'COM'
            cusip = line[40:49].strip()
            
            # Extract all numbers
            numbers = [int(n.replace(',', '')) for n in re.findall(r'[\d,]+', line[49:])]
            
            if not issuer or len(numbers) < 2:
                return None
            
            return {
                'issuer_name': issuer,
                'title_class': title,
                'cusip': cusip,
                'value_thousands': numbers[0],
                'shares': numbers[1],
                'share_type': 'SH' if 'SH' in line else 'PRN',
                'put_call': 'PUT' if 'PUT' in line.upper() else ('CALL' if 'CALL' in line.upper() else ''),
                'discretion': self._extract_discretion(line),
                'other_manager': '',
                'vote_sole': numbers[-3] if len(numbers) >= 3 else 0,
                'vote_shared': numbers[-2] if len(numbers) >= 2 else 0,
                'vote_none': numbers[-1] if len(numbers) >= 1 else 0
            }
        except (ValueError, IndexError):
            return None
    
    def _parse_with_regex(self, line):
        """Use regex patterns for parsing"""
        patterns = [
            r'^(.{1,30}?)\s+(COM|CL A|CL B|ADR)\s+([A-Z0-9]{9})\s+([\d,]+)\s+([\d,]+)',
            r'^(.+?)\s+([A-Z0-9]{9})\s+COM\s+([\d,]+)\s+([\d,]+)'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                numbers = [int(n.replace(',', '')) for n in re.findall(r'[\d,]+', line)]
                return {
                    'issuer_name': match.group(1).strip(),
                    'title_class': match.group(2) if len(match.groups()) > 3 else 'COM',
                    'cusip': match.group(-2),  # Second to last group
                    'value_thousands': numbers[0] if numbers else 0,
                    'shares': numbers[1] if len(numbers) > 1 else 0,
                    'share_type': 'SH',
                    'put_call': '',
                    'discretion': 'SOLE',
                    'other_manager': '',
                    'vote_sole': numbers[-1] if numbers else 0,
                    'vote_shared': 0,
                    'vote_none': 0
                }
        return None
    
    def _parse_by_splitting(self, line):
        """Parse by splitting on whitespace"""
        try:
            parts = re.split(r'\s{2,}', line)
            numbers = [int(n.replace(',', '')) for n in re.findall(r'[\d,]+', line)]
            
            if len(parts) < 2 or len(numbers) < 2:
                return None
            
            cusip = ''
            for part in parts:
                if re.match(r'^[A-Z0-9]{9}$', part):
                    cusip = part
                    break
            
            return {
                'issuer_name': parts[0],
                'title_class': 'COM',
                'cusip': cusip,
                'value_thousands': numbers[0],
                'shares': numbers[1],
                'share_type': 'SH',
                'put_call': '',
                'discretion': 'SOLE',
                'other_manager': '',
                'vote_sole': numbers[-1] if len(numbers) > 2 else numbers[1],
                'vote_shared': 0,
                'vote_none': 0
            }
        except (ValueError, IndexError):
            return None
    
    def _extract_discretion(self, line):
        """Extract investment discretion from line"""
        line_upper = line.upper()
        if 'SOLE' in line_upper:
            return 'SOLE'
        elif 'SHARED' in line_upper:
            return 'SHARED'
        elif 'NONE' in line_upper:
            return 'NONE'
        return 'SOLE'
    
    def save_company_data(self, company_data):
        """Insert company information into database"""
        cursor = self.conn.cursor()
        
        query = """
        INSERT INTO company_info 
        (company_name, cik, irs_number, state, form_type, report_period, filing_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            company_data.get('company_name'),
            company_data.get('cik'),
            company_data.get('irs_number'),
            company_data.get('state'),
            company_data.get('form_type'),
            company_data.get('report_period'),
            company_data.get('filing_date')
        )
        
        cursor.execute(query, values)
        self.conn.commit()
        company_id = cursor.lastrowid
        logger.info(f"Company data saved with ID: {company_id}")
        return company_id
    
    def save_holdings_data(self, holdings, company_id):
        """Insert holdings data into database"""
        cursor = self.conn.cursor()
        
        query = """
        INSERT INTO holdings 
        (company_id, issuer_name, title_class, cusip, value_thousands, shares, 
         share_type, put_call, discretion, other_manager, vote_sole, vote_shared, vote_none)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        success_count = 0
        for holding in holdings:
            try:
                values = (
                    company_id,
                    holding['issuer_name'][:255],
                    holding['title_class'][:100],
                    holding['cusip'][:20],
                    holding['value_thousands'],
                    holding['shares'],
                    holding['share_type'][:10],
                    holding['put_call'][:10],
                    holding['discretion'][:20],
                    holding['other_manager'][:255],
                    holding['vote_sole'],
                    holding['vote_shared'],
                    holding['vote_none']
                )
                
                cursor.execute(query, values)
                success_count += 1
            except Error as e:
                logger.error(f"Failed to insert {holding.get('issuer_name', 'Unknown')}: {e}")
        
        self.conn.commit()
        logger.info(f"Saved {success_count}/{len(holdings)} holdings to database")
    
    def process_filing(self, file_path):
        """Main processing function"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            logger.info(f"Processing {file_path} ({len(content):,} characters)")
            
            if not self.connect_db():
                return False
            
            self.setup_tables()
            
            # Parse company information
            company_data = self.parse_company_data(content)
            if not company_data:
                logger.error("Could not extract company information")
                return False
            
            company_id = self.save_company_data(company_data)
            
            # Parse holdings data
            table_content = self.find_table_section(content)
            if not table_content:
                logger.error("Could not locate holdings table")
                return False
            
            holdings = self.parse_holdings_table(table_content)
            if holdings:
                self.save_holdings_data(holdings, company_id)
                logger.info("Processing completed successfully")
                return True
            else:
                logger.warning("No holdings data found")
                return False
                
        except Exception as e:
            logger.error(f"Processing failed: {e}")
            return False
        finally:
            if self.conn and self.conn.is_connected():
                self.conn.close()

def run_extraction():
    """Run the SEC 13F extraction process"""
    config = {
        'host': 'localhost',
        'database': 'sec_filings',
        'user': 'root',
        'password': 'cmipl2012'  # Update with your password
    }
    
    file_path = '0001536411-12-000005.txt'  # Update with your file path
    
    processor = SEC13FProcessor(**config)
    success = processor.process_filing(file_path)
    
    if success:
        print("SEC 13F data extraction completed successfully!")
    else:
        print("Extraction failed - check logs for details")

if __name__ == "__main__":
    run_extraction()
