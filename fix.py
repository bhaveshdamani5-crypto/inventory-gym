import os

app_path = r'c:\Users\BHAVESH\Downloads\audit-gym\server\app.py'
with open(app_path, 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = 'return r"""'
end_marker = '"""'

start_idx = content.find(start_marker)
if start_idx != -1:
    content_start = start_idx + len(start_marker)
    end_idx = content.find(end_marker, content_start)
    if end_idx != -1:
        html_content = content[content_start:end_idx]
        
        templates_dir = r'c:\Users\BHAVESH\Downloads\audit-gym\server\templates'
        os.makedirs(templates_dir, exist_ok=True)
        with open(os.path.join(templates_dir, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(html_content)
            
        replacement = '''
    idx_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    with open(idx_path, "r", encoding="utf-8") as f:
        return f.read()
'''
        new_content = content[:start_idx] + replacement + content[end_idx+3:]
        with open(app_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("Success")
