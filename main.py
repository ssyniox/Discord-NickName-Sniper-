import json
import asyncio
import aiohttp
from datetime import datetime

class UsernameSniper:
    def __init__(self):
        with open('config.json', 'r') as f:
            config = json.load(f)
        self.token = config['token']
        self.password = config['password']
        self.target_user_id = config['target_user_id']
        self.webhook_url = config['webhook_url']
        self.current_username = None
        
    async def get_user_profile(self):
        headers = {'Authorization': self.token}
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://discord.com/api/v10/users/{self.target_user_id}/profile', headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('user', {}).get('username')
                return None

    async def send_webhook_log(self, title, description, color=0x000000, success=None):
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "timestamp": datetime.now().isoformat(),
            "footer": {"text": "made by quarz"}
        }
        
        if success is not None:
            embed["fields"] = [{"name": "Status", "value": "Success" if success else "Failed", "inline": True}]

        payload = {"embeds": [embed]}

        async with aiohttp.ClientSession() as session:
            try:
                await session.post(self.webhook_url, json=payload)
            except Exception as e:
                print(f"Webhook gönderim hatası: {e}")

    async def attempt_snipe(self, old_username):
        print(f"Attempting to snipe: {old_username}")

        headers = {
            'Authorization': self.token,
            'Content-Type': 'application/json'
        }

        payload = {
            'username': old_username,
            'password': self.password
        }

        async with aiohttp.ClientSession() as session:
            async with session.patch('https://discord.com/api/v10/users/@me', 
                                   headers=headers, json=payload) as resp:
                if resp.status == 200:
                    print(f"Successfully sniped: {old_username}")
                    await self.send_webhook_log(
                        "Username Successfully Sniped!",
                        f"**Sniped Username:** {old_username}\\n**Date:** {datetime.now().strftime('%Y.%m.%d %H:%M:%S.%f')[:-3]}",
                        success=True
                    )
                    return True
                else:
                    error = await resp.text()
                    print(f"Failed to snipe: {error}")
                    return False

    async def monitor_user(self):
        print(f"Monitoring user: {self.target_user_id}")

        username = await self.get_user_profile()
        if username:
            self.current_username = username
            print(f"Current username: {username}")
        else:
            print("Failed to get user profile")
            return

        while True:
            try:
                new_username = await self.get_user_profile()
                
                if new_username and new_username != self.current_username:
                    now = datetime.now()
                    timestamp = now.strftime("%Y.%m.%d %H:%M:%S.%f")[:-3]
                    
                    print(f"[{timestamp}] Username changed!")
                    print(f"Old: {self.current_username}")
                    print(f"New: {new_username}")
                    
                    await self.send_webhook_log(
                        f"{self.current_username}",
                        f"**Changed Date:** {timestamp}\\n**New Username:** {new_username}"
                    )

                    await self.attempt_snipe(self.current_username)
                    self.current_username = new_username
                
                await asyncio.sleep(0.5)

            except Exception as e:
                print(f"Monitoring error: {e}")
                await asyncio.sleep(5)

    async def start(self):
        print("Username Sniper starting.")
        await self.monitor_user()

if __name__ == "__main__":
    sniper = UsernameSniper()
    asyncio.run(sniper.start())
