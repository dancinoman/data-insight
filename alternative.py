import requests

url = "https://donnees.montreal.ca/dataset/portrait-thematique-sur-la-pauvrete-2021/resource/eb255cf4-128c-4840-bb9a-a01e2b84333c"
response = requests.get(url)
with open("portrait-pauvrete.xlsx", "wb") as f:
    f.write(response.content)

print("✅ Downloaded XLSX file directly.")
