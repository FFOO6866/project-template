#!/usr/bin/env python3
"""
Direct PostgreSQL Schema Migration
Creates all DataFlow tables by directly inspecting production_models.py
and generating SQL DDL statements
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import re

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Database connection string
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://horme_user:horme_password@localhost:5433/horme_db")


def generate_sql_type(python_type: str, field_info: dict) -> str:
    """Convert Python type annotations to PostgreSQL types"""
    type_mapping = {
        'str': 'TEXT',
        'int': 'INTEGER',
        'float': 'DOUBLE PRECISION',
        'bool': 'BOOLEAN',
        'datetime': 'TIMESTAMP WITH TIME ZONE',
        'Decimal': 'NUMERIC(12,2)',
        'dict': 'JSONB',
        'list': 'JSONB',
        'Dict': 'JSONB',
        'List': 'JSONB',
        'Optional[str]': 'TEXT',
        'Optional[int]': 'INTEGER',
        'Optional[float]': 'DOUBLE PRECISION',
        'Optional[datetime]': 'TIMESTAMP WITH TIME ZONE',
        'Optional[Decimal]': 'NUMERIC(12,2)',
        'Optional[dict]': 'JSONB',
        'Optional[Dict]': 'JSONB',
        'Optional[list]': 'JSONB',
        'Optional[List]': 'JSONB',
    }

    # Extract base type from Optional
    if 'Optional' in python_type:
        match = re.search(r'Optional\[(.*?)\]', python_type)
        if match:
            base_type = match.group(1)
            return type_mapping.get(base_type, 'TEXT')

    # Extract from List/Dict
    if 'List' in python_type or 'Dict' in python_type:
        return 'JSONB'

    return type_mapping.get(python_type, 'TEXT')


def parse_production_models():
    """Parse production_models.py to extract model definitions"""
    models_file = Path(__file__).parent.parent / "src" / "models" / "production_models.py"

    with open(models_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extract model definitions
    models = {}
    current_model = None
    current_fields = []
    current_config = {}
    current_indexes = []

    in_model = False
    in_dataflow_config = False
    in_indexes = False

    for line in content.split('\n'):
        stripped = line.strip()

        # Detect model start
        if stripped.startswith('@db.model'):
            in_model = True
            current_fields = []
            current_config = {}
            current_indexes = []
            continue

        # Detect class definition
        if in_model and stripped.startswith('class '):
            match = re.search(r'class\s+(\w+)', stripped)
            if match:
                current_model = match.group(1)
                continue

        # Detect field definitions
        if in_model and current_model and ':' in stripped and not stripped.startswith('__') and not stripped.startswith('#'):
            # Parse field: field_name: type = default
            match = re.match(r'(\w+):\s*([^=]+)(?:\s*=\s*(.+))?', stripped)
            if match:
                field_name = match.group(1)
                field_type = match.group(2).strip()
                default_value = match.group(3).strip() if match.group(3) else None

                current_fields.append({
                    'name': field_name,
                    'type': field_type,
                    'default': default_value,
                    'nullable': 'Optional' in field_type or default_value == 'None'
                })

        # Detect __dataflow__ config
        if in_model and '__dataflow__' in stripped:
            in_dataflow_config = True
            continue

        if in_dataflow_config:
            if '}' in stripped:
                in_dataflow_config = False
            elif ':' in stripped:
                match = re.search(r"'(\w+)':\s*(\w+)", stripped)
                if match:
                    current_config[match.group(1)] = match.group(2) == 'True'

        # Detect __indexes__
        if in_model and '__indexes__' in stripped:
            in_indexes = True
            continue

        if in_indexes:
            if ']' in stripped and not '{' in stripped:
                in_indexes = False
            elif 'name' in stripped and 'fields' in stripped:
                # Extract index definition
                name_match = re.search(r"'name':\s*'([^']+)'", stripped)
                fields_match = re.search(r"'fields':\s*\[([^\]]+)\]", stripped)
                unique_match = re.search(r"'unique':\s*True", stripped)
                type_match = re.search(r"'type':\s*'([^']+)'", stripped)

                if name_match and fields_match:
                    current_indexes.append({
                        'name': name_match.group(1),
                        'fields': [f.strip().strip("'\"") for f in fields_match.group(1).split(',')],
                        'unique': unique_match is not None,
                        'type': type_match.group(1) if type_match else None
                    })

        # Detect end of model
        if in_model and stripped == '' and current_fields:
            if current_model:
                models[current_model] = {
                    'fields': current_fields,
                    'config': current_config,
                    'indexes': current_indexes
                }
                current_model = None
                in_model = False

    return models


def generate_create_table_sql(model_name: str, model_def: dict) -> str:
    """Generate CREATE TABLE SQL for a model"""
    table_name = model_def['config'].get('table_name', model_name.lower())

    # Start CREATE TABLE
    sql = f"CREATE TABLE IF NOT EXISTS dataflow.{table_name} (\n"

    # Always add id column
    sql += "    id SERIAL PRIMARY KEY,\n"

    # Add model fields
    field_lines = []
    for field in model_def['fields']:
        sql_type = generate_sql_type(field['type'], field)
        nullable = "NULL" if field['nullable'] else "NOT NULL"

        # Handle defaults
        default_clause = ""
        if field['default'] and field['default'] != 'None':
            if field['default'] in ['True', 'False']:
                default_clause = f" DEFAULT {field['default'].lower()}"
            elif field['default'] == '[]' or field['default'] == '{}':
                default_clause = f" DEFAULT '{field['default']}'::jsonb"
            elif field['type'] == 'datetime' or 'datetime' in field['type']:
                default_clause = " DEFAULT CURRENT_TIMESTAMP"
            elif field['default'].startswith('"') or field['default'].startswith("'"):
                default_clause = f" DEFAULT {field['default']}"

        field_lines.append(f"    {field['name']} {sql_type}{default_clause} {nullable}")

    # Add enterprise fields if configured
    config = model_def['config']
    if config.get('soft_delete'):
        field_lines.append("    deleted_at TIMESTAMP WITH TIME ZONE NULL")

    if config.get('versioned'):
        field_lines.append("    version INTEGER DEFAULT 1 NOT NULL")

    # Always add timestamps
    if not any('created_at' in f['name'] for f in model_def['fields']):
        field_lines.append("    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP")

    if not any('updated_at' in f['name'] for f in model_def['fields']):
        field_lines.append("    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP")

    sql += ",\n".join(field_lines)
    sql += "\n);"

    return sql


def generate_indexes_sql(model_name: str, model_def: dict) -> list:
    """Generate CREATE INDEX SQL for a model"""
    table_name = model_def['config'].get('table_name', model_name.lower())
    index_sqls = []

    for index in model_def['indexes']:
        index_name = index['name']
        fields = index['fields']
        unique = "UNIQUE " if index.get('unique') else ""
        index_type = f"USING {index['type']}" if index.get('type') else ""

        # Handle GIN indexes for JSONB
        if index.get('type') == 'gin':
            # For full-text search on text fields
            if any('name' in f or 'description' in f for f in fields):
                field_expr = f"to_tsvector('english', {fields[0]})"
            else:
                field_expr = ', '.join(fields)
        else:
            field_expr = ', '.join(fields)

        sql = f"CREATE {unique}INDEX IF NOT EXISTS {index_name} ON dataflow.{table_name} {index_type} ({field_expr});"
        index_sqls.append(sql)

    return index_sqls


def generate_complete_migration_sql():
    """Generate complete migration SQL"""
    print("=" * 80)
    print("DataFlow Schema Migration SQL Generator")
    print("=" * 80)

    print("\nParsing production_models.py...")
    models = parse_production_models()
    print(f"Found {len(models)} models")

    migration_sql = []

    # Header
    migration_sql.append("-- DataFlow Schema Migration")
    migration_sql.append(f"-- Generated: {datetime.now().isoformat()}")
    migration_sql.append("-- Source: src/models/production_models.py")
    migration_sql.append("")
    migration_sql.append("BEGIN;")
    migration_sql.append("")
    migration_sql.append("-- Ensure dataflow schema exists")
    migration_sql.append("CREATE SCHEMA IF NOT EXISTS dataflow;")
    migration_sql.append("")

    # Drop old tables (optional - comment out to preserve data)
    migration_sql.append("-- Drop old tables (CAUTION: Data loss)")
    migration_sql.append("-- Uncomment if fresh migration is needed")
    migration_sql.append("/*")
    migration_sql.append("DROP TABLE IF EXISTS dataflow.product_enrichment CASCADE;")
    migration_sql.append("DROP TABLE IF EXISTS dataflow.product_suppliers CASCADE;")
    migration_sql.append("DROP TABLE IF EXISTS dataflow.quotations CASCADE;")
    migration_sql.append("DROP TABLE IF EXISTS dataflow.products CASCADE;")
    migration_sql.append("DROP TABLE IF EXISTS dataflow.suppliers CASCADE;")
    migration_sql.append("*/")
    migration_sql.append("")

    # Create tables
    migration_sql.append("-- Create tables from DataFlow models")
    migration_sql.append("")

    for model_name in sorted(models.keys()):
        model_def = models[model_name]
        migration_sql.append(f"-- Model: {model_name}")
        migration_sql.append(generate_create_table_sql(model_name, model_def))
        migration_sql.append("")

    # Create indexes
    migration_sql.append("-- Create indexes")
    migration_sql.append("")

    for model_name in sorted(models.keys()):
        model_def = models[model_name]
        index_sqls = generate_indexes_sql(model_name, model_def)
        if index_sqls:
            migration_sql.append(f"-- Indexes for {model_name}")
            migration_sql.extend(index_sqls)
            migration_sql.append("")

    # Create update trigger function
    migration_sql.append("-- Update timestamp trigger function")
    migration_sql.append("""
CREATE OR REPLACE FUNCTION dataflow.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';
""")

    # Apply triggers to all tables
    migration_sql.append("-- Apply update triggers to all tables")
    for model_name in sorted(models.keys()):
        table_name = models[model_name]['config'].get('table_name', model_name.lower())
        migration_sql.append(f"""
DROP TRIGGER IF EXISTS update_{table_name}_updated_at ON dataflow.{table_name};
CREATE TRIGGER update_{table_name}_updated_at
    BEFORE UPDATE ON dataflow.{table_name}
    FOR EACH ROW EXECUTE FUNCTION dataflow.update_updated_at_column();
""")

    migration_sql.append("")
    migration_sql.append("COMMIT;")
    migration_sql.append("")
    migration_sql.append(f"-- Total tables: {len(models)}")
    migration_sql.append("-- Migration complete")

    return "\n".join(migration_sql)


def main():
    """Main execution"""
    try:
        # Generate SQL
        sql = generate_complete_migration_sql()

        # Save to file
        output_file = Path(__file__).parent.parent / "migrations" / "dataflow_schema_migration.sql"
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(sql)

        print(f"\n✓ Migration SQL generated: {output_file}")
        print(f"  File size: {len(sql)} bytes")
        print(f"  SQL statements: {sql.count(';')} ")

        print("\nNext steps:")
        print("  1. Review the generated SQL file")
        print("  2. Apply migration:")
        print(f"     docker exec -i horme-postgres psql -U horme_user -d horme_db < {output_file}")
        print("  3. Verify tables:")
        print("     docker exec horme-postgres psql -U horme_user -d horme_db -c \"\\dt dataflow.*\"")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
