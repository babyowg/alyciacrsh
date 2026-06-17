---
description: Generate a complete Aly content pack from a pasted script. Paste your script after the command.
---

The user has pasted a script for an Aly content pack. Execute the following steps immediately without asking any questions:

1. Write the script below to `/tmp/aly_script_input.txt` using the Write tool. Preserve every line exactly as-is. Do not modify, summarise or reformat the script.

2. Run this exact command from the project directory `/home/user/alyciacrsh`:
   ```
   python3 aly_pack_from_script.py /tmp/aly_script_input.txt --infer-topic
   ```

3. Report back:
   - The full output folder path
   - The number of images generated
   - Any scene that failed, if applicable

The script to process:

$ARGUMENTS
