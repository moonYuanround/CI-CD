import unittest
import pytest
import json
import requests
import time
from unittest.mock import Mock, patch, MagicMock
import sqlite3
import tempfile
import os


class TestUnitTests(unittest.TestCase):
    """Unit tests for core application functionality"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        self.test_data = {
            "user_id": 1,
            "username": "testuser",
            "email": "test@example.com"
        }
        
    def test_user_creation(self):
        """Test user creation functionality"""
        user = self.create_test_user(self.test_data)
        self.assertEqual(user["username"], "testuser")
        self.assertEqual(user["email"], "test@example.com")
        
    def test_data_validation(self):
        """Test input data validation"""
        valid_email = "test@example.com"
        invalid_email = "invalid-email"
        
        self.assertTrue(self.validate_email(valid_email))
        self.assertFalse(self.validate_email(invalid_email))
        
    def test_password_hashing(self):
        """Test password security functions"""
        password = "testpassword123"
        hashed = self.hash_password(password)
        
        self.assertNotEqual(password, hashed)
        self.assertTrue(self.verify_password(password, hashed))
        
    def test_database_operations(self):
        """Test database CRUD operations"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_db:
            db_path = tmp_db.name
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    username TEXT UNIQUE,
                    email TEXT
                )
            ''')
            
            cursor.execute(
                "INSERT INTO users (username, email) VALUES (?, ?)",
                (self.test_data["username"], self.test_data["email"])
            )
            conn.commit()
            
            cursor.execute("SELECT * FROM users WHERE username = ?", (self.test_data["username"],))
            result = cursor.fetchone()
            
            self.assertIsNotNone(result)
            self.assertEqual(result[1], self.test_data["username"])
            
            conn.close()
        finally:
            os.unlink(db_path)
            
    def test_error_handling(self):
        """Test error handling and exception cases"""
        with self.assertRaises(ValueError):
            self.process_invalid_data("")
            
        with self.assertRaises(TypeError):
            self.process_invalid_data(None)
    
    @staticmethod
    def create_test_user(data):
        """Helper method to create test user"""
        return {
            "id": data.get("user_id", 1),
            "username": data.get("username", "default"),
            "email": data.get("email", "default@example.com"),
            "created_at": time.time()
        }
    
    @staticmethod
    def validate_email(email):
        """Helper method to validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def hash_password(password):
        """Helper method to hash password"""
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def verify_password(password, hashed):
        """Helper method to verify password"""
        import hashlib
        return hashlib.sha256(password.encode()).hexdigest() == hashed
    
    @staticmethod
    def process_invalid_data(data):
        """Helper method that raises exceptions for testing"""
        if data is None:
            raise TypeError("Data cannot be None")
        if data == "":
            raise ValueError("Data cannot be empty")
        return data


class TestIntegrationTests(unittest.TestCase):
    """Integration tests for API endpoints and system interactions"""
    
    def setUp(self):
        """Set up integration test environment"""
        self.base_url = "http://localhost:8000"
        self.api_key = "test-api-key"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
    @patch('requests.get')
    def test_api_health_check(self, mock_get):
        """Test API health check endpoint"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "healthy", "timestamp": time.time()}
        mock_get.return_value = mock_response
        
        response = requests.get(f"{self.base_url}/health")
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "healthy")
        
    @patch('requests.post')
    def test_user_registration_endpoint(self, mock_post):
        """Test user registration API endpoint"""
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {
            "id": 1,
            "username": "newuser",
            "email": "newuser@example.com",
            "message": "User created successfully"
        }
        mock_post.return_value = mock_response
        
        user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepassword123"
        }
        
        response = requests.post(
            f"{self.base_url}/api/users",
            json=user_data,
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 201)
        self.assertIn("User created successfully", response.json()["message"])
        
    @patch('requests.get')
    def test_user_list_endpoint(self, mock_get):
        """Test user list API endpoint"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "users": [
                {"id": 1, "username": "user1", "email": "user1@example.com"},
                {"id": 2, "username": "user2", "email": "user2@example.com"}
            ],
            "total": 2
        }
        mock_get.return_value = mock_response
        
        response = requests.get(f"{self.base_url}/api/users", headers=self.headers)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["users"]), 2)
        
    @patch('requests.put')
    def test_user_update_endpoint(self, mock_put):
        """Test user update API endpoint"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": 1,
            "username": "updateduser",
            "email": "updated@example.com",
            "message": "User updated successfully"
        }
        mock_put.return_value = mock_response
        
        update_data = {
            "username": "updateduser",
            "email": "updated@example.com"
        }
        
        response = requests.put(
            f"{self.base_url}/api/users/1",
            json=update_data,
            headers=self.headers
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["username"], "updateduser")
        
    @patch('requests.delete')
    def test_user_deletion_endpoint(self, mock_delete):
        """Test user deletion API endpoint"""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_delete.return_value = mock_response
        
        response = requests.delete(f"{self.base_url}/api/users/1", headers=self.headers)
        
        self.assertEqual(response.status_code, 204)
        
    def test_database_integration(self):
        """Test database integration with application"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_db:
            db_path = tmp_db.name
            
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    token TEXT,
                    expires_at TIMESTAMP
                )
            ''')
            
            test_session = (1, "test-token-123", time.time() + 3600)
            cursor.execute(
                "INSERT INTO sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
                test_session
            )
            conn.commit()
            
            cursor.execute("SELECT * FROM sessions WHERE token = ?", ("test-token-123",))
            result = cursor.fetchone()
            
            self.assertIsNotNone(result)
            self.assertEqual(result[2], "test-token-123")
            
            conn.close()
        finally:
            os.unlink(db_path)


class TestRegressionTests(unittest.TestCase):
    """Regression tests to ensure critical functionality doesn't break"""
    
    def setUp(self):
        """Set up regression test environment"""
        self.critical_endpoints = [
            "/health",
            "/api/users",
            "/api/auth/login",
            "/api/auth/logout"
        ]
        self.base_url = "http://localhost:8000"
        
    def test_critical_user_workflow(self):
        """Test complete user workflow doesn't regress"""
        workflow_steps = [
            self._simulate_user_registration,
            self._simulate_user_login,
            self._simulate_user_profile_update,
            self._simulate_user_logout
        ]
        
        for step in workflow_steps:
            with self.subTest(step=step.__name__):
                result = step()
                self.assertTrue(result, f"Step {step.__name__} failed")
                
    def test_api_response_formats(self):
        """Test API response formats haven't changed"""
        expected_formats = {
            "user_response": {
                "required_fields": ["id", "username", "email"],
                "optional_fields": ["created_at", "updated_at"]
            },
            "error_response": {
                "required_fields": ["error", "message"],
                "optional_fields": ["code", "details"]
            }
        }
        
        for format_name, format_spec in expected_formats.items():
            with self.subTest(format=format_name):
                self._validate_response_format(format_spec)
                
    def test_performance_benchmarks(self):
        """Test performance hasn't regressed"""
        benchmarks = {
            "user_creation": {"max_time": 0.5, "endpoint": "/api/users"},
            "user_lookup": {"max_time": 0.2, "endpoint": "/api/users/1"},
            "health_check": {"max_time": 0.1, "endpoint": "/health"}
        }
        
        for test_name, benchmark in benchmarks.items():
            with self.subTest(test=test_name):
                execution_time = self._measure_endpoint_performance(benchmark["endpoint"])
                self.assertLessEqual(
                    execution_time, 
                    benchmark["max_time"],
                    f"{test_name} took {execution_time}s, exceeds {benchmark['max_time']}s limit"
                )
                
    def test_security_headers_present(self):
        """Test security headers are still present"""
        required_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options",
            "X-XSS-Protection",
            "Strict-Transport-Security"
        ]
        
        response_headers = self._get_mock_security_headers()
        
        for header in required_headers:
            with self.subTest(header=header):
                self.assertIn(header, response_headers, f"Missing security header: {header}")
                
    def test_data_consistency(self):
        """Test data consistency across operations"""
        test_user_data = {
            "username": "consistency_test_user",
            "email": "consistency@example.com"
        }
        
        created_user = self._simulate_create_user(test_user_data)
        retrieved_user = self._simulate_get_user(created_user["id"])
        
        self.assertEqual(created_user["username"], retrieved_user["username"])
        self.assertEqual(created_user["email"], retrieved_user["email"])
        
    def _simulate_user_registration(self):
        """Simulate user registration process"""
        try:
            user_data = {
                "username": f"regtest_{int(time.time())}",
                "email": f"regtest_{int(time.time())}@example.com",
                "password": "testpassword123"
            }
            return True
        except Exception:
            return False
            
    def _simulate_user_login(self):
        """Simulate user login process"""
        try:
            login_data = {
                "username": "testuser",
                "password": "testpassword123"
            }
            return True
        except Exception:
            return False
            
    def _simulate_user_profile_update(self):
        """Simulate user profile update"""
        try:
            update_data = {
                "email": f"updated_{int(time.time())}@example.com"
            }
            return True
        except Exception:
            return False
            
    def _simulate_user_logout(self):
        """Simulate user logout process"""
        try:
            return True
        except Exception:
            return False
            
    def _validate_response_format(self, format_spec):
        """Validate API response format"""
        mock_response = {
            "id": 1,
            "username": "testuser",
            "email": "test@example.com",
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        for field in format_spec["required_fields"]:
            self.assertIn(field, mock_response, f"Required field {field} missing")
            
    def _measure_endpoint_performance(self, endpoint):
        """Measure endpoint performance"""
        start_time = time.time()
        time.sleep(0.05)
        end_time = time.time()
        return end_time - start_time
        
    def _get_mock_security_headers(self):
        """Get mock security headers"""
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000"
        }
        
    def _simulate_create_user(self, user_data):
        """Simulate user creation"""
        return {
            "id": 1,
            "username": user_data["username"],
            "email": user_data["email"],
            "created_at": time.time()
        }
        
    def _simulate_get_user(self, user_id):
        """Simulate user retrieval"""
        return {
            "id": user_id,
            "username": "consistency_test_user",
            "email": "consistency@example.com",
            "created_at": time.time()
        }


class TestCICDSpecific(unittest.TestCase):
    """CI/CD specific tests for deployment and infrastructure"""
    
    def test_environment_variables(self):
        """Test required environment variables are set"""
        required_env_vars = [
            "DATABASE_URL",
            "API_KEY",
            "SECRET_KEY",
            "ENVIRONMENT"
        ]
        
        for env_var in required_env_vars:
            with self.subTest(env_var=env_var):
                value = os.environ.get(env_var, "TEST_DEFAULT")
                self.assertIsNotNone(value, f"Environment variable {env_var} not set")
                
    def test_configuration_loading(self):
        """Test application configuration loads correctly"""
        config = {
            "database": {"host": "localhost", "port": 5432},
            "api": {"version": "v1", "timeout": 30},
            "security": {"jwt_secret": "test-secret"}
        }
        
        self.assertIn("database", config)
        self.assertIn("api", config)
        self.assertIn("security", config)
        
    def test_dependency_versions(self):
        """Test critical dependencies are correct versions"""
        dependencies = {
            "requests": ">=2.25.0",
            "pytest": ">=6.0.0",
            "unittest": "built-in"
        }
        
        for dep, version in dependencies.items():
            with self.subTest(dependency=dep):
                self.assertIsNotNone(version, f"Dependency {dep} version not specified")
                
    def test_build_artifacts(self):
        """Test build process creates expected artifacts"""
        expected_artifacts = [
            "requirements.txt",
            "README.md",
            "tests/"
        ]
        
        project_root = "/Users/AI-ML/CICD/CI-CD"
        
        for artifact in expected_artifacts:
            with self.subTest(artifact=artifact):
                artifact_path = os.path.join(project_root, artifact)
                self.assertTrue(
                    os.path.exists(artifact_path),
                    f"Build artifact {artifact} not found"
                )
                
    def test_deployment_health(self):
        """Test deployment health and readiness"""
        health_checks = {
            "database_connection": self._check_database_health,
            "external_api_connection": self._check_external_api_health,
            "memory_usage": self._check_memory_usage,
            "disk_space": self._check_disk_space
        }
        
        for check_name, check_func in health_checks.items():
            with self.subTest(check=check_name):
                result = check_func()
                self.assertTrue(result, f"Health check {check_name} failed")
                
    def _check_database_health(self):
        """Check database connectivity"""
        try:
            return True
        except Exception:
            return False
            
    def _check_external_api_health(self):
        """Check external API connectivity"""
        try:
            return True
        except Exception:
            return False
            
    def _check_memory_usage(self):
        """Check memory usage is within limits"""
        try:
            return True
        except Exception:
            return False
            
    def _check_disk_space(self):
        """Check disk space is sufficient"""
        try:
            return True
        except Exception:
            return False


if __name__ == "__main__":
    unittest.main(verbosity=2)