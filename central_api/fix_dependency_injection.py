#!/usr/bin/env python3
"""Script to add dependency injection to all router functions."""

import re
from pathlib import Path


def fix_config_router():
    """Add ConfigManager dependency to all functions in config router."""
    router_path = Path("app/routers/config.py")

    with router_path.open("r") as f:
        lines = f.readlines()

    new_lines = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this line starts a function definition
        if re.match(r"^\s*(?:async )?def \w+\(", line):
            # Collect the full function signature
            func_lines = [line]
            indent = len(line) - len(line.lstrip())

            # Continue collecting lines until we find the closing ):
            j = i + 1
            while j < len(lines):
                func_lines.append(lines[j])
                if lines[j].strip().endswith("):"):
                    break
                j += 1

            # Join the function signature
            full_signature = "".join(func_lines)

            # Check if it already has the dependency
            if "Depends(get_config_manager)" not in full_signature:
                # Find the position of "):
                close_pos = full_signature.rfind("):")
                if close_pos != -1:
                    # Insert the dependency before the closing ):
                    before = full_signature[:close_pos]

                    # Check if there are existing parameters
                    if "(" in before and before.strip().endswith(","):
                        # Already has trailing comma
                        dependency = (
                            "\n"
                            + " " * (indent + 4)
                            + "config: ConfigManager = Depends(get_config_manager)"
                        )
                    elif "()" in before:
                        # No parameters
                        dependency = "config: ConfigManager = Depends(get_config_manager)"
                        before = before.replace("()", "(")
                    else:
                        # Has parameters, add comma
                        dependency = (
                            ",\n"
                            + " " * (indent + 4)
                            + "config: ConfigManager = Depends(get_config_manager)"
                        )

                    after = full_signature[close_pos:]
                    full_signature = before + dependency + after

            # Add the modified signature
            new_lines.extend(full_signature.splitlines(keepends=True))
            i = j + 1
        else:
            new_lines.append(line)
            i += 1

    # Write back
    with router_path.open("w") as f:
        f.writelines(new_lines)

    print(f"✓ Updated {router_path}")


if __name__ == "__main__":
    fix_config_router()
