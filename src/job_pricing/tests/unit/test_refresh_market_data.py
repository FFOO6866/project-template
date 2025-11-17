"""
Unit Tests for refresh_market_data Celery Task

Tests the market data refresh task that runs daily to update Mercer and SSG data.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

from src.job_pricing.worker import refresh_market_data


class TestRefreshMarketDataTask:
    """Tests for refresh_market_data Celery task"""

    @patch('src.job_pricing.worker.get_db')
    @patch('src.job_pricing.worker.MercerJobLibraryLoader')
    @patch('src.job_pricing.worker.SSGJobRolesLoader')
    @patch('src.job_pricing.worker.Path')
    def test_refresh_market_data_success_both_sources(
        self,
        mock_path,
        mock_ssg_loader,
        mock_mercer_loader,
        mock_get_db
    ):
        """Test successful market data refresh from both Mercer and SSG"""
        # Setup mocks
        mock_db_session = MagicMock()
        mock_get_db.return_value = iter([mock_db_session])

        # Mock file paths exist
        mock_mercer_file = MagicMock()
        mock_mercer_file.exists.return_value = True
        mock_ssg_file = MagicMock()
        mock_ssg_file.exists.return_value = True

        mock_data_dir = MagicMock()
        mock_data_dir.__truediv__ = lambda self, x: mock_mercer_file if 'mercer' in str(x) else mock_ssg_file

        mock_path.return_value.__truediv__.return_value = mock_data_dir

        # Mock loader statistics
        mock_mercer_result = MagicMock()
        mock_mercer_result.statistics.successful = 150
        mock_mercer_result.statistics.total_records = 150

        mock_ssg_result = MagicMock()
        mock_ssg_result.statistics.successful = 200
        mock_ssg_result.statistics.total_records = 200

        mock_mercer_instance = MagicMock()
        mock_mercer_instance.load_from_excel.return_value = mock_mercer_result
        mock_mercer_loader.return_value = mock_mercer_instance

        mock_ssg_instance = MagicMock()
        mock_ssg_instance.load_from_excel.return_value = mock_ssg_result
        mock_ssg_loader.return_value = mock_ssg_instance

        # Execute task
        result = refresh_market_data()

        # Assertions
        assert result["success"] is True
        assert result["mercer_updated"] == 150
        assert result["ssg_updated"] == 200
        assert len(result["errors"]) == 0
        assert result["execution_time_seconds"] >= 0

    @patch('src.job_pricing.worker.get_db')
    @patch('src.job_pricing.worker.Path')
    def test_refresh_market_data_no_files_found(
        self,
        mock_path,
        mock_get_db
    ):
        """Test market data refresh when data files don't exist"""
        # Setup mocks
        mock_db_session = MagicMock()
        mock_get_db.return_value = iter([mock_db_session])

        # Mock file paths don't exist
        mock_file = MagicMock()
        mock_file.exists.return_value = False

        mock_data_dir = MagicMock()
        mock_data_dir.__truediv__ = lambda self, x: mock_file

        mock_path.return_value.__truediv__.return_value = mock_data_dir

        # Execute task
        result = refresh_market_data()

        # Assertions
        assert result["success"] is False
        assert result["mercer_updated"] == 0
        assert result["ssg_updated"] == 0

    @patch('src.job_pricing.worker.get_db')
    @patch('src.job_pricing.worker.MercerJobLibraryLoader')
    @patch('src.job_pricing.worker.Path')
    def test_refresh_market_data_mercer_error_continues(
        self,
        mock_path,
        mock_mercer_loader,
        mock_get_db
    ):
        """Test that SSG loading continues even if Mercer fails"""
        # Setup mocks
        mock_db_session = MagicMock()
        mock_get_db.return_value = iter([mock_db_session])

        # Mock file paths exist
        mock_file = MagicMock()
        mock_file.exists.return_value = True

        mock_data_dir = MagicMock()
        mock_data_dir.__truediv__ = lambda self, x: mock_file

        mock_path.return_value.__truediv__.return_value = mock_data_dir

        # Mock Mercer loader raises exception
        mock_mercer_loader.side_effect = Exception("Mercer API error")

        # Execute task
        result = refresh_market_data()

        # Assertions
        assert result["mercer_updated"] == 0
        assert len(result["errors"]) > 0
        assert any("Mercer" in error for error in result["errors"])

    @patch('src.job_pricing.worker.get_db')
    def test_refresh_market_data_database_error(
        self,
        mock_get_db
    ):
        """Test market data refresh handles database errors gracefully"""
        # Setup mocks to raise database error
        mock_get_db.side_effect = Exception("Database connection failed")

        # Execute task
        result = refresh_market_data()

        # Assertions
        assert result["success"] is False
        assert len(result["errors"]) > 0

    @patch('src.job_pricing.worker.get_db')
    @patch('src.job_pricing.worker.MercerJobLibraryLoader')
    @patch('src.job_pricing.worker.Path')
    def test_refresh_market_data_loader_configuration(
        self,
        mock_path,
        mock_mercer_loader,
        mock_get_db
    ):
        """Test that loaders are configured correctly"""
        # Setup mocks
        mock_db_session = MagicMock()
        mock_get_db.return_value = iter([mock_db_session])

        # Mock file paths exist
        mock_file = MagicMock()
        mock_file.exists.return_value = True

        mock_data_dir = MagicMock()
        mock_data_dir.__truediv__ = lambda self, x: mock_file

        mock_path.return_value.__truediv__.return_value = mock_data_dir

        # Mock loader result
        mock_result = MagicMock()
        mock_result.statistics.successful = 100
        mock_result.statistics.total_records = 100

        mock_mercer_instance = MagicMock()
        mock_mercer_instance.load_from_excel.return_value = mock_result
        mock_mercer_loader.return_value = mock_mercer_instance

        # Execute task
        refresh_market_data()

        # Verify loader was configured correctly
        mock_mercer_loader.assert_called_once_with(
            session=mock_db_session,
            batch_size=100,
            continue_on_error=True,
            show_progress=False
        )

    def test_refresh_market_data_execution_time_tracking(self):
        """Test that execution time is tracked"""
        with patch('src.job_pricing.worker.get_db') as mock_get_db:
            mock_db_session = MagicMock()
            mock_get_db.return_value = iter([mock_db_session])

            with patch('src.job_pricing.worker.Path') as mock_path:
                # Mock files don't exist
                mock_file = MagicMock()
                mock_file.exists.return_value = False

                mock_data_dir = MagicMock()
                mock_data_dir.__truediv__ = lambda self, x: mock_file

                mock_path.return_value.__truediv__.return_value = mock_data_dir

                # Execute task
                result = refresh_market_data()

                # Verify execution time is tracked
                assert "execution_time_seconds" in result
                assert isinstance(result["execution_time_seconds"], (int, float))
                assert result["execution_time_seconds"] >= 0


class TestRefreshMarketDataIntegration:
    """Integration tests for refresh_market_data (requires real infrastructure)"""

    @pytest.mark.integration
    def test_refresh_market_data_with_real_database(self):
        """Test refresh_market_data with real database connection"""
        # This would require actual database and data files
        # Skip if not in integration test environment
        pytest.skip("Requires real database and data files")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
