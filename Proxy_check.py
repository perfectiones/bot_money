import requests

# Проверка прокси
proxies = {
    'https': 'http://ee786b82be39e964fd708ea74c11cbeac0676f6f676c652e636f6d@tg.netstatus.click:2053'
}
TOKEN ='8533867582:AAHng4IOlG42jZ7uPICmQrl5vbWZJSdS3Cs'

try:
    r = requests.get('https://api.telegram.org/bot' + TOKEN + '/getMe', proxies=proxies, timeout=10)
    print("✅ Прокси работает:", r.json())
except Exception as e:
    print("❌ Прокси не работает:", e)