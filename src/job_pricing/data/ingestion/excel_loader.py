"""
Excel Loader

Mixin class for loading data from Excel files.
Provides pandas integration with data cleaning utilities.
"""

from typing import List, Dict, Any, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


class ExcelLoader:
    """
    Mixin class for Excel file loading functionality.

    Can be mixed with BaseDataLoader to add Excel reading capabilities.

    Example:
        >>> class MercerJobLoader(BaseDataLoader, ExcelLoader):
        ...     def transform_record(self, data):
        ...         return MercerJobLibrary(**data)
        ...
        >>> loader = MercerJobLoader(session, repo)
        >>> data = loader.read_excel("jobs.xlsx", sheet_name="Jobs")
        >>> result = loader.load_data(data)
    """

    @staticmethod
    def read_excel(
        file_path: str,
        sheet_name: Optional[str] = None,
        header: int = 0,
        skiprows: Optional[int] = None,
        usecols: Optional[List[str]] = None,
        dtype: Optional[Dict[str, Any]] = None,
        na_values: Optional[List[str]] = None,
        clean_data: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Read Excel file and return list of dictionaries.

        Args:
            file_path: Path to Excel file
            sheet_name: Name or index of sheet to read (None = first sheet)
            header: Row number to use as column names (0-indexed)
            skiprows: Number of rows to skip at start
            usecols: List of column names to read (None = all columns)
            dtype: Dictionary of column types
            na_values: Additional strings to recognize as NA
            clean_data: If True, apply data cleaning

        Returns:
            List of dictionaries (one per row)

        Raises:
            FileNotFoundError: If Excel file doesn't exist
            ValueError: If sheet name not found
        """
        logger.info(f"Reading Excel file: {file_path}")

        try:
            # Read Excel file
            df = pd.read_excel(
                file_path,
                sheet_name=sheet_name or 0,  # Default to first sheet
                header=header,
                skiprows=skiprows,
                usecols=usecols,
                dtype=dtype,
                na_values=na_values,
                engine='openpyxl'  # Modern Excel format
            )

            logger.info(f"Read {len(df)} rows from {file_path}")

            # Clean data if requested
            if clean_data:
                df = ExcelLoader.clean_dataframe(df)

            # Convert to list of dictionaries
            records = df.to_dict('records')

            return records

        except FileNotFoundError:
            logger.error(f"Excel file not found: {file_path}")
            raise

        except Exception as e:
            logger.error(f"Error reading Excel file {file_path}: {e}")
            raise

    @staticmethod
    def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean DataFrame with common data quality fixes.

        Cleaning operations:
        - Trim whitespace from string columns
        - Convert empty strings to None
        - Strip special characters from column names
        - Replace pandas NA with None

        Args:
            df: DataFrame to clean

        Returns:
            Cleaned DataFrame
        """
        # Clean column names: lowercase, replace spaces with underscores
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('[^a-z0-9_]', '', regex=True)

        # Trim whitespace from string columns
        string_columns = df.select_dtypes(include=['object']).columns
        for col in string_columns:
            df[col] = df[col].str.strip() if hasattr(df[col], 'str') else df[col]

        # Convert empty strings to None
        df = df.replace('', None)
        df = df.replace('nan', None)
        df = df.replace('NaN', None)

        # Replace pandas NA with Python None
        df = df.where(pd.notna(df), None)

        logger.debug(f"Cleaned DataFrame: {len(df)} rows, {len(df.columns)} columns")

        return df

    @staticmethod
    def read_multiple_sheets(
        file_path: str,
        sheet_names: Optional[List[str]] = None,
        clean_data: bool = True
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Read multiple sheets from an Excel file.

        Args:
            file_path: Path to Excel file
            sheet_names: List of sheet names to read (None = all sheets)
            clean_data: If True, apply data cleaning

        Returns:
            Dictionary mapping sheet name to list of records

        Example:
            >>> data = ExcelLoader.read_multiple_sheets(
            ...     "data.xlsx",
            ...     sheet_names=["Jobs", "Market Data"]
            ... )
            >>> jobs = data["Jobs"]
            >>> market_data = data["Market Data"]
        """
        logger.info(f"Reading multiple sheets from: {file_path}")

        try:
            # Read all sheets or specified sheets
            if sheet_names is None:
                excel_file = pd.ExcelFile(file_path)
                sheet_names = excel_file.sheet_names

            result = {}

            for sheet_name in sheet_names:
                logger.info(f"Reading sheet: {sheet_name}")

                df = pd.read_excel(
                    file_path,
                    sheet_name=sheet_name,
                    engine='openpyxl'
                )

                if clean_data:
                    df = ExcelLoader.clean_dataframe(df)

                records = df.to_dict('records')
                result[sheet_name] = records

                logger.info(f"Sheet '{sheet_name}': {len(records)} records")

            return result

        except Exception as e:
            logger.error(f"Error reading multiple sheets from {file_path}: {e}")
            raise

    @staticmethod
    def validate_columns(
        df: pd.DataFrame,
        required_columns: List[str],
        raise_on_missing: bool = True
    ) -> List[str]:
        """
        Validate that DataFrame contains required columns.

        Args:
            df: DataFrame to validate
            required_columns: List of required column names
            raise_on_missing: If True, raise ValueError on missing columns

        Returns:
            List of missing column names

        Raises:
            ValueError: If required columns are missing and raise_on_missing=True
        """
        actual_columns = set(df.columns)
        required_set = set(required_columns)

        missing_columns = required_set - actual_columns

        if missing_columns:
            logger.warning(f"Missing columns: {missing_columns}")

            if raise_on_missing:
                raise ValueError(f"Missing required columns: {missing_columns}")

        return list(missing_columns)

    @staticmethod
    def map_columns(
        df: pd.DataFrame,
        column_mapping: Dict[str, str]
    ) -> pd.DataFrame:
        """
        Rename DataFrame columns using a mapping.

        Args:
            df: DataFrame to rename columns
            column_mapping: Dictionary mapping old names to new names

        Returns:
            DataFrame with renamed columns

        Example:
            >>> mapping = {
            ...     "Job Code": "job_code",
            ...     "Job Title": "job_title",
            ...     "Career Level": "career_level"
            ... }
            >>> df = ExcelLoader.map_columns(df, mapping)
        """
        df = df.rename(columns=column_mapping)
        logger.debug(f"Mapped {len(column_mapping)} columns")
        return df

    @staticmethod
    def get_excel_info(file_path: str) -> Dict[str, Any]:
        """
        Get metadata about an Excel file without reading all data.

        Args:
            file_path: Path to Excel file

        Returns:
            Dictionary with file metadata

        Example:
            >>> info = ExcelLoader.get_excel_info("data.xlsx")
            >>> print(f"Sheets: {info['sheet_names']}")
            >>> print(f"Total rows: {info['total_rows']}")
        """
        try:
            excel_file = pd.ExcelFile(file_path)

            info = {
                "file_path": file_path,
                "sheet_names": excel_file.sheet_names,
                "sheet_count": len(excel_file.sheet_names),
                "sheets": {}
            }

            total_rows = 0

            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name, nrows=0)

                # Get row count by reading with chunking
                row_count = sum(1 for _ in pd.read_excel(
                    excel_file,
                    sheet_name=sheet_name,
                    chunksize=1000
                ))

                info["sheets"][sheet_name] = {
                    "columns": list(df.columns),
                    "column_count": len(df.columns),
                    "row_count": row_count
                }

                total_rows += row_count

            info["total_rows"] = total_rows

            logger.info(f"Excel file info: {sheet_count} sheets, {total_rows} total rows")

            return info

        except Exception as e:
            logger.error(f"Error reading Excel file info: {e}")
            raise

    @staticmethod
    def sample_excel(
        file_path: str,
        sheet_name: Optional[str] = None,
        n: int = 5
    ) -> pd.DataFrame:
        """
        Read a sample of rows from Excel file for inspection.

        Args:
            file_path: Path to Excel file
            sheet_name: Sheet name to sample (None = first sheet)
            n: Number of rows to sample

        Returns:
            DataFrame with sample rows

        Example:
            >>> sample = ExcelLoader.sample_excel("data.xlsx", n=10)
            >>> print(sample.head())
        """
        try:
            df = pd.read_excel(
                file_path,
                sheet_name=sheet_name or 0,
                nrows=n,
                engine='openpyxl'
            )

            logger.info(f"Sampled {len(df)} rows from {file_path}")

            return df

        except Exception as e:
            logger.error(f"Error sampling Excel file: {e}")
            raise
