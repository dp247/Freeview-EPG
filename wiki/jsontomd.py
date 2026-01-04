import os
import json
import argparse

from datetime import datetime


def json_to_markdown(json_data, column_mapping):
    """Converts JSON data to a Markdown table."""

    # headers = list(column_mapping.values())
    headers = [text.replace('_', ' ') for text in column_mapping.values()]
    keys = list(column_mapping.keys())

    md_table = "| " + " | ".join(headers) + " |\n"
    md_table += "|" + "|".join(["---"] * len(headers)) + "|\n"

    for item in json_data:
        row = []
        for key in keys:
            value = str(item.get(key, ""))
            # If the column contains a URL, embed it as an image
            if value.startswith("http") and (".png" in value or ".jpg" in value or ".jpeg" in value or ".gif" in value):
                value = f'<img src="{value}" height="150px" />'
            row.append(value)
        md_table += "| " + " | ".join(row) + " |\n"

    return md_table


def save_markdown(filename, content, *args):
    """Saves the markdown content into the 'wiki' folder."""
    os.makedirs("wiki", exist_ok=True)
    filepath = os.path.join("wiki", filename)
    with open(filepath, "w", encoding="utf-8") as file:
        file.write(f"Channel list current as of {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n")
        file.write(content)
    print(f"Markdown file saved: {filepath}")


def main():
    parser = argparse.ArgumentParser(description="Convert JSON to Markdown table.")
    parser.add_argument("json_file", help="Path to the JSON file")
    parser.add_argument("output_file", help="Output Markdown filename")
    parser.add_argument("--columns", nargs='+', help="Custom column mapping in the format 'json_key:Display Name'",
                        required=True)
    parser.add_argument("--json_root", nargs='+', help="Root of JSON file to load",
                        required=False)
    args = parser.parse_args()

    with open(args.json_file, "r", encoding="utf-8") as file:
        json_data = json.load(file)

    if isinstance(json_data, dict):
        json_data = [json_data]
        if len(json_data) == 1:
            if args.json_root:
                json_data = json_data[0][args.json_root[0]]
            else:
                json_data = json_data[0]
    elif not isinstance(json_data, list):
        raise ValueError("Invalid JSON structure. Expected a list or object.")

    # Process column mappings
    column_mapping = dict(mapping.split(":") for mapping in args.columns)

    # Convert to markdown and save
    markdown_content = json_to_markdown(json_data, column_mapping)
    save_markdown(args.output_file, markdown_content)


if __name__ == "__main__":
    main()
