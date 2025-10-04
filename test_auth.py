import asyncio
from src.services.youtube_uploader import AuthManager, AuthConfig

async def test():
    auth = AuthManager(AuthConfig(client_secrets_path="client_secrets.json"))
    print("🔐 Starting OAuth2 flow...")
    print("📱 Browser will open for authorization")
    creds = await auth.authenticate(account_name="main")
    print(f"✅ Success! Channel: {creds.channel_title}")

asyncio.run(test())
