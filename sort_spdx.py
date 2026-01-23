#!/usr/bin/env python3
"""
Sort SPDX JSON files deterministically for meaningful git diffs.

This script:
- Sorts all object keys alphabetically
- Sorts arrays by relevant identifying fields
- Handles nested structures recursively
"""

import json
import sys
from typing import Any, Dict, List


def sort_array_by_field(arr: List[Dict], *fields: str) -> List[Dict]:
    """Sort an array of objects by one or more fields."""
    def get_sort_key(item):
        return tuple(item.get(field, "") for field in fields)
    
    return sorted(arr, key=get_sort_key)


def sort_spdx_structure(data: Any) -> Any:
    """
    Recursively sort SPDX JSON structure.
    
    - Sorts all object keys alphabetically
    - Sorts specific arrays by their identifying fields
    """
    if isinstance(data, dict):
        # Sort dictionary keys
        sorted_dict = {}
        for key in sorted(data.keys()):
            value = data[key]
            
            # Handle specific SPDX array fields
            if key == "packages" and isinstance(value, list):
                value = sort_array_by_field(value, "SPDXID", "spdxId", "name")
            elif key == "files" and isinstance(value, list):
                value = sort_array_by_field(value, "SPDXID", "spdxId", "fileName")
            elif key == "relationships" and isinstance(value, list):
                value = sort_array_by_field(
                    value, 
                    "spdxElementId", 
                    "relationshipType", 
                    "relatedSpdxElement"
                )
            elif key == "externalRefs" and isinstance(value, list):
                value = sort_array_by_field(
                    value,
                    "referenceCategory",
                    "referenceType",
                    "referenceLocator"
                )
            elif key == "annotations" and isinstance(value, list):
                value = sort_array_by_field(value, "annotationDate", "annotator")
            elif key == "checksums" and isinstance(value, list):
                value = sort_array_by_field(value, "algorithm", "checksumValue")
            elif key == "hasExtractedLicensingInfos" and isinstance(value, list):
                value = sort_array_by_field(value, "licenseId", "name")
            
            # Recursively sort the value
            sorted_dict[key] = sort_spdx_structure(value)
        
        return sorted_dict
    
    elif isinstance(data, list):
        # Sort list items recursively
        return [sort_spdx_structure(item) for item in data]
    
    else:
        # Return primitive values as-is
        return data


def main():
    """Main function to read, sort, and write SPDX JSON."""
    if len(sys.argv) > 1:
        # Read from file
        input_file = sys.argv[1]
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Sort the data
        sorted_data = sort_spdx_structure(data)
        
        # Determine output file
        if len(sys.argv) > 2:
            output_file = sys.argv[2]
        else:
            output_file = input_file
        
        # Write sorted data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(sorted_data, f, indent=2, ensure_ascii=False)
            f.write('\n')  # Add trailing newline
        
        print(f"Sorted SPDX file written to: {output_file}", file=sys.stderr)
    
    else:
        # Read from stdin, write to stdout
        data = json.load(sys.stdin)
        sorted_data = sort_spdx_structure(data)
        json.dump(sorted_data, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write('\n')


if __name__ == "__main__":
    main()
