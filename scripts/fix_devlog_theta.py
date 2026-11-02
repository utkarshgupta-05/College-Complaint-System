with open('docs/development-log.md', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace('\theta = 0.60', r'\theta = 0.60').replace('\t' + 'heta = 0.60', r'\theta = 0.60')
with open('docs/development-log.md', 'w', encoding='utf-8') as f:
    f.write(text)
print('Fixed!')

