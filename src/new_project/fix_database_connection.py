"""
Database Connection Fix Script
=============================

Fixes PostgreSQL authentication and connection issues for the MCP server.
This script addresses:
1. PostgreSQL password authentication failures
2. Connection pool configuration issues
3. DataFlow database URL configuration
4. PostgreSQL service status verification

Usage:
    python fix_database_connection.py
"""

import os
import sys
import subprocess
import json
import time
import logging
from typing import Dict, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseConnectionFixer:
    """Comprehensive database connection fix utility"""
    
    def __init__(self):
        self.default_config = {
            'host': 'localhost',
            'port': 5432,
            'database': 'horme_classification_db',
            'user': 'horme_user',
            'password': 'horme_password'
        }
        
        self.test_results = {
            'postgresql_service': False,
            'database_exists': False,
            'user_exists': False,
            'connection_test': False,
            'permissions_test': False
        }
    
    def check_postgresql_service(self) -> bool:
        """Check if PostgreSQL service is running"""
        logger.info("🔍 Checking PostgreSQL service status...")
        
        try:
            # Try Windows service check
            result = subprocess.run(
                ['sc', 'query', 'postgresql-x64-14'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and 'RUNNING' in result.stdout:
                logger.info("✅ PostgreSQL service is running")
                self.test_results['postgresql_service'] = True
                return True
            else:
                logger.warning("⚠️ PostgreSQL service not running, attempting to start...")
                return self._start_postgresql_service()
                
        except Exception as e:
            logger.error(f"❌ Failed to check PostgreSQL service: {e}")
            return False
    
    def _start_postgresql_service(self) -> bool:
        """Attempt to start PostgreSQL service"""
        try:
            logger.info("🚀 Starting PostgreSQL service...")
            
            result = subprocess.run(
                ['net', 'start', 'postgresql-x64-14'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                logger.info("✅ PostgreSQL service started successfully")
                time.sleep(5)  # Wait for service to fully start
                self.test_results['postgresql_service'] = True
                return True
            else:
                logger.error(f"❌ Failed to start PostgreSQL service: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting PostgreSQL service: {e}")
            return False
    
    def test_basic_connection(self) -> bool:
        """Test basic PostgreSQL connection"""
        logger.info("🔍 Testing basic PostgreSQL connection...")
        
        try:
            import psycopg2
            
            # Try connecting to default postgres database first
            conn = psycopg2.connect(
                host=self.default_config['host'],
                port=self.default_config['port'],
                database='postgres',
                user='postgres',
                password='postgres'
            )
            
            conn.close()
            logger.info("✅ Basic PostgreSQL connection successful")
            return True
            
        except psycopg2.OperationalError as e:
            if "password authentication failed" in str(e):
                logger.warning("⚠️ Password authentication failed, trying alternative credentials...")
                return self._try_alternative_credentials()
            else:
                logger.error(f"❌ Connection failed: {e}")
                return False
        except ImportError:
            logger.error("❌ psycopg2 not installed. Installing...")
            return self._install_psycopg2()
        except Exception as e:
            logger.error(f"❌ Unexpected connection error: {e}")
            return False
    
    def _try_alternative_credentials(self) -> bool:
        """Try alternative PostgreSQL credentials"""
        logger.info("🔑 Trying alternative credentials...")
        
        credential_sets = [
            {'user': 'postgres', 'password': ''},
            {'user': 'postgres', 'password': 'admin'},
            {'user': 'postgres', 'password': 'password'},
            {'user': 'postgres', 'password': '123456'},
            {'user': self.default_config['user'], 'password': self.default_config['password']}
        ]
        
        try:
            import psycopg2
            
            for creds in credential_sets:
                try:
                    conn = psycopg2.connect(
                        host=self.default_config['host'],
                        port=self.default_config['port'],
                        database='postgres',
                        user=creds['user'],
                        password=creds['password']
                    )
                    
                    conn.close()
                    logger.info(f"✅ Connection successful with user: {creds['user']}")
                    
                    # Update default config with working credentials
                    self.default_config.update(creds)
                    return True
                    
                except psycopg2.OperationalError:
                    continue
            
            logger.error("❌ No working credentials found")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error trying alternative credentials: {e}")
            return False
    
    def _install_psycopg2(self) -> bool:
        """Install psycopg2 if missing"""
        try:
            logger.info("📦 Installing psycopg2...")
            
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', 'psycopg2-binary'],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                logger.info("✅ psycopg2 installed successfully")
                return self.test_basic_connection()
            else:
                logger.error(f"❌ Failed to install psycopg2: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error installing psycopg2: {e}")
            return False
    
    def create_database_and_user(self) -> bool:
        """Create database and user if they don't exist"""
        logger.info("📊 Creating database and user...")
        
        try:
            import psycopg2
            from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
            
            # Connect as superuser
            conn = psycopg2.connect(
                host=self.default_config['host'],
                port=self.default_config['port'],
                database='postgres',
                user=self.default_config['user'],
                password=self.default_config['password']
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            
            cursor = conn.cursor()
            
            # Create user if not exists
            try:
                cursor.execute(f"""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '{self.default_config['user']}') THEN
                            CREATE USER {self.default_config['user']} WITH PASSWORD '{self.default_config['password']}';
                        END IF;
                    END
                    $$;
                """)
                logger.info(f"✅ User {self.default_config['user']} created/verified")
                self.test_results['user_exists'] = True
            except Exception as e:
                logger.error(f"❌ Failed to create user: {e}")
            
            # Create database if not exists
            try:
                cursor.execute(f"""
                    SELECT 1 FROM pg_database WHERE datname = '{self.default_config['database']}'
                """)
                
                if not cursor.fetchone():
                    cursor.execute(f"CREATE DATABASE {self.default_config['database']} OWNER {self.default_config['user']}")
                    logger.info(f"✅ Database {self.default_config['database']} created")
                else:
                    logger.info(f"✅ Database {self.default_config['database']} already exists")
                
                self.test_results['database_exists'] = True
            except Exception as e:
                logger.error(f"❌ Failed to create database: {e}")
            
            # Grant permissions
            try:
                cursor.execute(f"GRANT ALL PRIVILEGES ON DATABASE {self.default_config['database']} TO {self.default_config['user']}")
                cursor.execute(f"ALTER USER {self.default_config['user']} CREATEDB")
                logger.info("✅ Permissions granted")
                self.test_results['permissions_test'] = True
            except Exception as e:
                logger.error(f"❌ Failed to grant permissions: {e}")
            
            cursor.close()
            conn.close()
            
            return self.test_results['user_exists'] and self.test_results['database_exists']
            
        except Exception as e:
            logger.error(f"❌ Error creating database and user: {e}")
            return False
    
    def test_application_connection(self) -> bool:
        """Test connection with application credentials"""
        logger.info("🔍 Testing application database connection...")
        
        try:
            import psycopg2
            
            conn = psycopg2.connect(
                host=self.default_config['host'],
                port=self.default_config['port'],
                database=self.default_config['database'],
                user=self.default_config['user'],
                password=self.default_config['password']
            )
            
            cursor = conn.cursor()
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            
            cursor.execute("CREATE TABLE IF NOT EXISTS connection_test (id SERIAL PRIMARY KEY, test_data TEXT)")
            cursor.execute("INSERT INTO connection_test (test_data) VALUES ('test')")
            cursor.execute("SELECT COUNT(*) FROM connection_test")
            count = cursor.fetchone()[0]
            
            cursor.execute("DROP TABLE connection_test")
            
            cursor.close()
            conn.close()
            
            logger.info(f"✅ Application connection test successful")
            logger.info(f"PostgreSQL version: {version[:50]}...")
            logger.info(f"Test records: {count}")
            
            self.test_results['connection_test'] = True
            return True
            
        except Exception as e:
            logger.error(f"❌ Application connection test failed: {e}")
            return False
    
    def update_dataflow_config(self) -> bool:
        """Update DataFlow configuration with working connection details"""
        logger.info("🔧 Updating DataFlow configuration...")
        
        try:
            # Create database URL
            database_url = (
                f"postgresql://{self.default_config['user']}:"
                f"{self.default_config['password']}@"
                f"{self.default_config['host']}:"
                f"{self.default_config['port']}/"
                f"{self.default_config['database']}"
            )
            
            # Update dataflow_classification_models.py
            models_file = Path(__file__).parent / "dataflow_classification_models.py"
            
            if models_file.exists():
                with open(models_file, 'r') as f:
                    content = f.read()
                
                # Replace database URL
                old_url_line = 'database_url="postgresql://horme_user:horme_password@localhost:5432/horme_classification_db"'
                new_url_line = f'database_url="{database_url}"'
                
                if old_url_line in content:
                    content = content.replace(old_url_line, new_url_line)
                    
                    with open(models_file, 'w') as f:
                        f.write(content)
                    
                    logger.info("✅ DataFlow configuration updated")
                else:
                    logger.warning("⚠️ Could not find database URL to replace")
            
            # Create environment file
            env_file = Path(__file__).parent / ".env.database"
            with open(env_file, 'w') as f:
                f.write(f"DATABASE_URL={database_url}\n")
                f.write(f"DB_HOST={self.default_config['host']}\n")
                f.write(f"DB_PORT={self.default_config['port']}\n")
                f.write(f"DB_NAME={self.default_config['database']}\n")
                f.write(f"DB_USER={self.default_config['user']}\n")
                f.write(f"DB_PASSWORD={self.default_config['password']}\n")
            
            logger.info(f"✅ Database environment file created: {env_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update DataFlow configuration: {e}")
            return False
    
    def generate_fix_report(self) -> Dict[str, Any]:
        """Generate comprehensive fix report"""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'test_results': self.test_results,
            'database_config': self.default_config,
            'fixes_applied': [],
            'recommendations': [],
            'overall_status': 'unknown'
        }
        
        # Determine overall status
        if all(self.test_results.values()):
            report['overall_status'] = 'healthy'
            report['fixes_applied'].append('All database connections working properly')
        elif self.test_results['connection_test']:
            report['overall_status'] = 'functional'
            report['fixes_applied'].append('Basic database connectivity established')
        else:
            report['overall_status'] = 'needs_attention'
            report['recommendations'].extend([
                'Check PostgreSQL installation and service status',
                'Verify database credentials and permissions',
                'Consider using Docker PostgreSQL for development'
            ])
        
        # Add specific recommendations
        if not self.test_results['postgresql_service']:
            report['recommendations'].append('Start PostgreSQL service or install PostgreSQL')
        
        if not self.test_results['user_exists']:
            report['recommendations'].append('Create database user with proper permissions')
        
        if not self.test_results['database_exists']:
            report['recommendations'].append('Create application database')
        
        return report
    
    def run_comprehensive_fix(self) -> Dict[str, Any]:
        """Run comprehensive database connection fix"""
        logger.info("🚀 Starting comprehensive database connection fix...")
        
        # Step 1: Check PostgreSQL service
        self.check_postgresql_service()
        
        # Step 2: Test basic connection
        if self.test_basic_connection():
            # Step 3: Create database and user
            self.create_database_and_user()
            
            # Step 4: Test application connection
            self.test_application_connection()
            
            # Step 5: Update configuration
            self.update_dataflow_config()
        
        # Generate report
        report = self.generate_fix_report()
        
        # Save report
        report_file = Path(__file__).parent / f"database_fix_report_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📊 Fix report saved: {report_file}")
        
        return report

def main():
    """Main entry point"""
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                    DATABASE CONNECTION FIXER                           ║
╠══════════════════════════════════════════════════════════════════╣
║ This script will fix PostgreSQL connection issues for the MCP server:     ║
║                                                                          ║
║ • Check PostgreSQL service status                                       ║
║ • Test database connectivity with various credentials                   ║
║ • Create database and user if needed                                    ║
║ • Update DataFlow configuration with working settings                   ║
║ • Generate comprehensive fix report                                     ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    fixer = DatabaseConnectionFixer()
    
    try:
        report = fixer.run_comprehensive_fix()
        
        print(f"\n📊 DATABASE FIX REPORT")
        print(f"="*50)
        print(f"Overall Status: {report['overall_status'].upper()}")
        print(f"Timestamp: {report['timestamp']}")
        print(f"\n🔍 Test Results:")
        
        for test, result in report['test_results'].items():
            status = "✅" if result else "❌"
            print(f"  {status} {test.replace('_', ' ').title()}: {result}")
        
        if report['fixes_applied']:
            print(f"\n✨ Fixes Applied:")
            for fix in report['fixes_applied']:
                print(f"  • {fix}")
        
        if report['recommendations']:
            print(f"\n💡 Recommendations:")
            for rec in report['recommendations']:
                print(f"  • {rec}")
        
        print(f"\n💾 Database Configuration:")
        config = report['database_config']
        database_url = f"postgresql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}"
        print(f"  URL: {database_url}")
        
        if report['overall_status'] == 'healthy':
            print(f"\n✅ SUCCESS: Database connection is now working properly!")
            print(f"You can now start the MCP server with:\n")
            print(f"  python fixed_production_mcp_server.py")
        elif report['overall_status'] == 'functional':
            print(f"\n⚠️ PARTIAL SUCCESS: Basic connectivity established but some issues remain.")
        else:
            print(f"\n❌ NEEDS ATTENTION: Database connection issues persist.")
            print(f"Please check the recommendations above.")
        
    except KeyboardInterrupt:
        print(f"\n🛑 Fix interrupted by user")
    except Exception as e:
        logger.error(f"❌ Fix failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
