with open('frontend/app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove width="stretch" parameter (with double quotes)
content = content.replace(', width="stretch"', '')

# Remove width='stretch' parameter (with single quotes) - just in case
content = content.replace(", width='stretch'", '')

with open('frontend/app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Removed all remaining width="stretch" parameters')