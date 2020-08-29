# Telegram async api

## Self-signed certificate
Run this command to create the `.pem` and `.key` files needed:

> `openssl req -newkey rsa:2048 -sha256 -nodes -keyout YOURPRIVATE.key -x509 -days 365 -out YOURPUBLIC.pem -subj "/CN=YOURHOST"`
