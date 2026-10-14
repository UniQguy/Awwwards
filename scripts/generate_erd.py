#!/usr/bin/env python3
"""
ELECTROCART Automated Entity-Relationship Diagram (ERD) Generator (WP1.2).
Inspects real Django models across all active applications and generates a canonical
Mermaid erDiagram representation of the database schema and foreign key relationships.
"""

import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

import django
django.setup()

from django.apps import apps
from django.db import models


def generate_mermaid_erd() -> str:
    lines = ["erDiagram"]

    target_apps = [
        "accounts",
        "catalog",
        "inventory",
        "cart",
        "orders",
        "payments",
        "promotions",
        "shipping",
        "wishlist",
    ]

    relationships = []
    entity_blocks = []

    for app_name in target_apps:
        try:
            app_config = apps.get_app_config(app_name)
        except LookupError:
            continue

        for model in app_config.get_models():
            model_name = model.__name__
            fields_desc = []

            for field in model._meta.fields:
                field_name = field.name
                internal_type = field.get_internal_type()

                # Clean Mermaid-safe type
                type_map = {
                    "CharField": "string",
                    "TextField": "text",
                    "IntegerField": "int",
                    "PositiveIntegerField": "int",
                    "DecimalField": "decimal",
                    "BooleanField": "bool",
                    "DateTimeField": "datetime",
                    "DateField": "date",
                    "UUIDField": "uuid",
                    "ForeignKey": "int_fk",
                    "OneToOneField": "int_fk",
                    "BigAutoField": "id",
                    "AutoField": "id",
                }
                clean_type = type_map.get(internal_type, "string")

                constraints = []
                if field.primary_key:
                    constraints.append("PK")
                if isinstance(field, (models.ForeignKey, models.OneToOneField)):
                    constraints.append("FK")

                constraint_str = f' "{",".join(constraints)}"' if constraints else ""
                fields_desc.append(f"        {clean_type} {field_name}{constraint_str}")

                # Capture Relationship
                if isinstance(field, models.OneToOneField):
                    rel_model = field.related_model.__name__
                    relationships.append(f"    {model_name} |o--|| {rel_model} : references")
                elif isinstance(field, models.ForeignKey):
                    rel_model = field.related_model.__name__
                    # Many to one
                    relationships.append(f"    {model_name} }}o--|| {rel_model} : references")

            block = [f"    {model_name} {{"]
            block.extend(fields_desc[:12])  # Limit to 12 most prominent fields for clarity
            if len(fields_desc) > 12:
                block.append(f"        string more_fields \"+{len(fields_desc)-12} columns\"")
            block.append("    }")
            entity_blocks.append("\n".join(block))

    # Assemble diagram
    # 1. Relationships first
    unique_rels = sorted(list(set(relationships)))
    lines.extend(unique_rels)
    lines.append("")
    # 2. Entity definitions
    lines.extend(entity_blocks)

    return "\n".join(lines)


def main():
    erd_markdown = generate_mermaid_erd()
    if len(sys.argv) > 1 and sys.argv[1] == "--write":
        output_file = BASE_DIR / "docs" / "ERD.mermaid"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(erd_markdown)
        print(f"Successfully generated ERD at {output_file}")
    else:
        print(erd_markdown)


if __name__ == "__main__":
    main()
