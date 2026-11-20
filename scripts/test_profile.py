import urllib.request
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
url = "https://www.fut.gg/players/237067-pele/27-237067/"
req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=8) as r:
    html = r.read().decode('utf-8', errors='ignore')

# find "nationality":"..."
m = re.findall(r'"nationality"\s*:\s*"([^"]+)"', html)
print("Nationality match:", m)

# find "birthDate":"..."
b = re.findall(r'"birthDate"\s*:\s*"([^"]+)"', html)
print("BirthDate match:", b)

# find "name":"..."
n = re.findall(r'"name"\s*:\s*"([^"]+)"', html)
print("Name match:", n[:5])
