source local.env
uv run python ./main.py workstation-chat \
  --max-tool-rounds 30 \
  --root ./ram/tmp/workstation-root

# What skills are available right now? Separate built-in workstation skills from imported skills.
# Import the skill file at trials/symbolsearch.skill.yaml into this workstation.
# Import the skill file at trials/python.skill.yaml into this workstation.
# What skills are available now? Group them by family and keep the titles short when you describe them.

# Use an implied skill
# Use the symbol search skill to find the Python class definition for BSSCController under src.

# Use another symbol-search shape
# Find every occurrence of the symbol BSSCController under src.

# Use Python read skill
# Use the Python read-text-file skill to read src/demo.py and show me the contents.

# Use Python write skill
# Use the Python write-text-file skill to create exports/summary.txt with a one-line summary of the classes in src/demo.py.

# Export a skill from chat
# Export the Python read-text-file skill to exports/python-read-text-file.yaml.
