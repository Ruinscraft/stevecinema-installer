import base64
encoded = base64.b64encode(open("profile_icon.png", "rb").read())
print(encoded)