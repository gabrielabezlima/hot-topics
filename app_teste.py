import requests
import xml.etree.ElementTree as ET

url = "https://trends.google.com/trending/rss?geo=BR"
resposta = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)

print("Status:", resposta.status_code)
print("Tamanho da resposta:", len(resposta.content))
print("Primeiros 500 caracteres:", resposta.content[:500])

root = ET.fromstring(resposta.content)
itens = root.findall(".//item")
print("Quantidade de itens encontrados:", len(itens))

for item in itens[:10]:
    print("-", item.find("title").text)