import base64

with open('logocerto2.png', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = 'logo_b64 = get_logo_base64()\nlogo_html = f\'<img src="data:image/png;base64,{logo_b64}" style="height:240px; margin-bottom:0.5rem;">\' if logo_b64 else \'<div class="adaga-wordmark">A<span>D</span>AGA</div>\''

new = f'LOGO_B64 = "{b64}"\nlogo_html = f\'<img src="data:image/png;base64,{{LOGO_B64}}" style="height:240px; margin-bottom:0.5rem;">\''

if old in content:
    content = content.replace(old, new)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Logo embutido com sucesso!')
else:
    print('Trecho nao encontrado')