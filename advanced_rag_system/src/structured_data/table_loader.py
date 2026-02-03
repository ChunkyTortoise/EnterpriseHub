"""Table loader for ingesting structured data files.

This module provides functionality for loading structured data from various
formats (CSV, Excel, JSON) and converting them to DocumentChunk objects for
vector storage and retrieval.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from uuid import UUID, uuid4

import pandas as pd

from src.core.exceptions import ValidationError
from src.core.types import DocumentChunk, Metadata


@dataclass
class TableLoadOptions:
    """Options for loading table data.

    Attributes:
        encoding: File encoding (default: utf-8)
        delimiter: CSV delimiter (default: comma)
        header_row: Row to use as header (default: 0)
        sheet_name: Excel sheet name or index (default: 0)
        skip_rows: Number of rows to skip at beginning
        na_values: Values to treat as NA/null
        dtype: Column data types
        parse_dates: Columns to parse as dates
        max_rows: Maximum rows to read
    """

    encoding: str = "utf-8"
    delimiter: str = ","
    header_row: Union[int, List[int]] = 0
    sheet_name: Union[str, int] = 0
    skip_rows: Optional[int] = None
    na_values: Optional[List[str]] = None
    dtype: Optional[Dict[str, Any]] = None
    parse_dates: Optional[List[str]] = None
    max_rows: Optional[int] = None


@dataclass
class InferredSchema:
    """Inferred schema for a table.

    Attributes:
        columns: Dictionary of column names to their types
        row_count: Number of rows in the table
        sample_data: Sample rows from the table
    """

    columns: Dict[str, str] = field(default_factory=dict)
    row_count: int = 0
    sample_data: List[Dict[str, Any]] = field(default_factory=list)


class TableLoader:
    """Loader for structured data tables.

    This class provides methods to load structured data from various file
    formats (CSV, Excel, JSON) and convert them to DocumentChunk objects
    suitable for vector storage and semantic search.

    Features:
    - Automatic schema inference
    - Support for CSV, Excel, and JSON formats
    - Conversion to DocumentChunk objects
    - Metadata extraction from headers
    - Configurable loading options

    Example:
        ```python
        loader = TableLoader()

        # Load CSV file
        df = loader.load_csv("data.csv")

        # Load Excel file
        df = loader.load_excel("data.xlsx", sheet_name="Sheet1")

        # Infer schema
        schema = loader.infer_schema(df)

        # Convert to DocumentChunks
        chunks = loader.convert_to_documents(df, source="data.csv")
        ```
    """

    def __init__(self) -> None:
        """Initialize the table loader."""
        self._loaded_data: Dict[str, pd.DataFrame] = {}
        self._schemas: Dict[str, InferredSchema] = {}

    def load_csv(
        self,
        path: Union[str, Path],
        options: Optional[TableLoadOptions] = None,
    ) -> pd.DataFrame:
        """Load a CSV file into a DataFrame.

        Args:
            path: Path to the CSV file
            options: Loading options

        Returns:
            DataFrame containing the CSV data

        Raises:
            ValidationError: If file doesn't exist or is invalid
        """
        path = Path(path)
        options = options or TableLoadOptions()

        if not path.exists():
            raise ValidationError(
                message=f"CSV file not found: {path}",
                details={"path": str(path)},
            )

        try:
            df = pd.read_csv(
                path,
                encoding=options.encoding,
                delimiter=options.delimiter,
                header=options.header_row,
                skiprows=options.skip_rows,
                na_values=options.na_values,
                dtype=options.dtype,
                parse_dates=options.parse_dates,
                nrows=options.max_rows,
            )

            # Store loaded data
            self._loaded_data[str(path)] = df

            return df

        except pd.errors.EmptyDataError:
            raise ValidationError(
                message=f"CSV file is empty: {path}",
                details={"path": str(path)},
            )
        except pd.errors.ParserError as e:
            raise ValidationError(
                message=f"Failed to parse CSV file: {path}",
                details={"path": str(path), "error": str(e)},
            )
        except Exception as e:
            raise ValidationError(
                message=f"Failed to load CSV file: {path}",
                details={"path": str(path), "error": str(e)},
            )

    def load_excel(
        self,
        path: Union[str, Path],
        sheet_name: Optional[Union[str, int]] = None,
        options: Optional[TableLoadOptions] = None,
    ) -> pd.DataFrame:
        """Load an Excel file into a DataFrame.

        Args:
            path: Path to the Excel file
            sheet_name: Sheet name or index (overrides options.sheet_name)
            options: Loading options

        Returns:
            DataFrame containing the Excel data

        Raises:
            ValidationError: If file doesn't exist or is invalid
        """
        path = Path(path)
        options = options or TableLoadOptions()

        if not path.exists():
            raise ValidationError(
                message=f"Excel file not found: {path}",
                details={"path": str(path)},
            )

        # Use provided sheet_name or from options
        sheet = sheet_name if sheet_name is not None else options.sheet_name

        try:
            df = pd.read_excel(
                path,
                sheet_name=sheet,
                header=options.header_row,
                skiprows=options.skip_rows,
                na_values=options.na_values,
                dtype=options.dtype,
                parse_dates=options.parse_dates,
                nrows=options.max_rows,
            )

            # Store loaded data
            key = f"{path}#{sheet}"
            self._loaded_data[key] = df

            return df

        except ValueError as e:
            raise ValidationError(
                message=f"Sheet '{sheet}' not found in Excel file: {path}",
                details={"path": str(path), "sheet": sheet, "error": str(e)},
            )
        except Exception as e:
            raise ValidationError(
                message=f"Failed to load Excel file: {path}",
                details={"path": str(path), "error": str(e)},
            )

    def load_json(
        self,
        path: Union[str, Path],
        orient: Optional[str] = None,
        options: Optional[TableLoadOptions] = None,
    ) -> pd.DataFrame:
        """Load a JSON file into a DataFrame.

        Args:
            path: Path to the JSON file
            orient: JSON orientation (records, index, columns, values, split)
            options: Loading options

        Returns:
            DataFrame containing the JSON data

        Raises:
            ValidationError: If file doesn't exist or is invalid
        """
        path = Path(path)
        options = options or TableLoadOptions()

        if not path.exists():
            raise ValidationError(
                message=f"JSON file not found: {path}",
                details={"path": str(path)},
            )

        try:
            with open(path, "r", encoding=options.encoding) as f:
                data = json.load(f)

            # Convert to DataFrame
            if orient:
                df = pd.read_json(path, orient=orient, encoding=options.encoding)
            elif isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Try to normalize nested JSON
                df = pd.json_normalize(data)
            else:
                raise ValidationError(
                    message=f"Unsupported JSON structure in file: {path}",
                    details={"path": str(path)},
                )

            # Store loaded data
            self._loaded_data[str(path)] = df

            return df

        except json.JSONDecodeError as e:
            raise ValidationError(
                message=f"Invalid JSON in file: {path}",
                details={"path": str(path), "error": str(e)},
            )
        except Exception as e:
            raise ValidationError(
                message=f"Failed to load JSON file: {path}",
                details={"path": str(path), "error": str(e)},
            )

    def infer_schema(self, data: pd.DataFrame) -> InferredSchema:
        """Infer the schema of a DataFrame.

        Args:
            data: DataFrame to analyze

        Returns:
            Inferred schema with column types and sample data
        """
        columns = {}
        for col in data.columns:
            dtype = data[col].dtype
            if pd.api.types.is_integer_dtype(dtype):
                columns[str(col)] = "integer"
            elif pd.api.types.is_float_dtype(dtype):
                columns[str(col)] = "float"
            elif pd.api.types.is_bool_dtype(dtype):
                columns[str(col)] = "boolean"
            elif pd.api.types.is_datetime64_any_dtype(dtype):
                columns[str(col)] = "datetime"
            else:
                columns[str(col)] = "string"

        # Get sample data (first 5 rows)
        sample = data.head(5).to_dict("records")

        return InferredSchema(
            columns=columns,
            row_count=len(data),
            sample_data=sample,
        )

    def convert_to_documents(
        self,
        data: pd.DataFrame,
        source: Optional[str] = None,
        text_columns: Optional[List[str]] = None,
        metadata_columns: Optional[List[str]] = None,
        document_id: Optional[UUID] = None,
    ) -> List[DocumentChunk]:
        """Convert DataFrame rows to DocumentChunk objects.

        Args:
            data: DataFrame to convert
            source: Source identifier for the data
            text_columns: Columns to include in the content text
                         (defaults to all non-numeric columns)
            metadata_columns: Columns to include as metadata
                            (defaults to all columns)
            document_id: Parent document ID

        Returns:
            List of DocumentChunk objects
        """
        if data.empty:
            return []

        doc_id = document_id or uuid4()

        # Determine text columns if not specified
        if text_columns is None:
            text_columns = [
                col
                for col in data.columns
                if data[col].dtype == "object" or pd.api.types.is_string_dtype(data[col])
            ]

        # Determine metadata columns if not specified
        if metadata_columns is None:
            metadata_columns = list(data.columns)

        chunks = []
        for idx, row in data.iterrows():
            # Build content from text columns
            content_parts = []
            for col in text_columns:
                if col in row and pd.notna(row[col]):
                    content_parts.append(f"{col}: {row[col]}")

            content = "\n".join(content_parts) if content_parts else str(row.to_dict())

            # Build metadata
            metadata_dict: Dict[str, Any] = {"source": source or "unknown"}
            for col in metadata_columns:
                if col in row and pd.notna(row[col]):
                    # Convert to serializable types
                    value = row[col]
                    if isinstance(value, (int, float, str, bool)):
                        metadata_dict[str(col)] = value
                    elif pd.api.types.is_datetime64_any_dtype(type(value)):
                        metadata_dict[str(col)] = value.isoformat()
                    else:
                        metadata_dict[str(col)] = str(value)

            metadata = Metadata(
                source=source,
                custom=metadata_dict,
            )

            chunk = DocumentChunk(
                document_id=doc_id,
                content=content,
                metadata=metadata,
                index=int(idx),
            )
            chunks.append(chunk)

        return chunks

    def get_loaded_data(self, key: str) -> Optional[pd.DataFrame]:
        """Get previously loaded data by key.

        Args:
            key: Key used when loading (file path or path#sheet)

        Returns:
            DataFrame if found, None otherwise
        """
        return self._loaded_data.get(key)

    def list_loaded_sources(self) -> List[str]:
        """List all loaded data source keys.

        Returns:
            List of source keys
        """
        return list(self._loaded_data.keys())

    def clear_loaded_data(self) -> None:
        """Clear all loaded data from memory."""
        self._loaded_data.clear()
        self._schemas.clear()

    def get_column_statistics(self, data: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """Get statistics for each column in the DataFrame.

        Args:
            data: DataFrame to analyze

        Returns:
            Dictionary of column statistics
        """
        stats = {}
        for col in data.columns:
            col_stats = {
                "dtype": str(data[col].dtype),
                "null_count": int(data[col].isnull().sum()),
                "unique_count": int(data[col].nunique()),
            }

            # Add numeric statistics if applicable
            if pd.api.types.is_numeric_dtype(data[col]):
                col_stats.update({
                    "min": float(data[col].min()) if not data[col].isnull().all() else None,
                    "max": float(data[col].max()) if not data[col].isnull().all() else None,
                    "mean": float(data[col].mean()) if not data[col].isnull().all() else None,
                })

            stats[str(col)] = col_stats

        return stats
