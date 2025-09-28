import requests

url = "http://localhost:5000/process"
payload = {
    "audio_url": "https://github.com/anars/blank-audio/raw/master/1-second-of-silence.wav",
    "media_urls": [
        "https://cdn.pixabay.com/photo/2016/11/29/03/53/rocket-launch-1863372_1280.jpg",
        "https://cdn.pixabay.com/photo/2019/12/14/14/14/space-4691786_1280.jpg"
    ]
}

resp = requests.post(url, json=payload)

print("Status:", resp.status_code)
print("Raw response:")
print(resp.text)
