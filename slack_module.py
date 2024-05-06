"""
slackパーミッションは以下の通りに設定しておく
channels:read
chat:write
reactions:write
投稿させたいチャンネルにbotを招待しておく
"""
import requests
import json

class SlackModule:
    def __init__(self):
        self.token = 'xoxb-ほにゃららら～～'  # ボットのトークンに置き換えてください
    def get_channel_id(self, channel_name):
        url = 'https://slack.com/api/conversations.list'
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        params = {
            "limit": 1000  # リストの上限を1000に設定
        }
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            channels = response.json().get('channels', [])
            for channel in channels:
                if channel['name'] == channel_name:
                    return channel['id']
        return None
    def post_slack(self, message, channel_name, thread_ts=None):
        channel_id = self.get_channel_id(channel_name)
        if channel_id is None:
            print("Channel not found")
            return
        url = 'https://slack.com/api/chat.postMessage'
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.token}"
        }
        payload = {
            "channel": str(channel_id),
            "text": message
        }
        if thread_ts is not None:
            payload["thread_ts"] = thread_ts
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            json_response = response.json()
            if json_response.get("ok"):
                return json_response.get("ts")  # メッセージのタイムスタンプを返す
            else:
                print("Error in posting message:", json_response.get("error"))
        else:
            print("Failed to post message, status code:", response.status_code)
        return None
    
    def add_reaction(self, emoji_name, channel_name, timestamp):
        channel_id = self.get_channel_id(channel_name)
        url = 'https://slack.com/api/reactions.add'
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "name": emoji_name,
            "channel": channel_id,
            "timestamp": timestamp
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            json_response = response.json()
            if json_response.get("ok"):
                print("Reaction added successfully")
            else:
                print("Error in adding reaction:", json_response.get("error"))
        else:
            print("Failed to add reaction, status code:", response.status_code)
    
    def remove_reaction(self, emoji_name, channel_name, timestamp):
        channel_id = self.get_channel_id(channel_name)
        url = 'https://slack.com/api/reactions.remove'
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        payload = {
            "name": emoji_name,
            "channel": channel_id,
            "timestamp": timestamp
        }
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        if response.status_code == 200:
            json_response = response.json()
            if json_response.get("ok"):
                print("Reaction removed successfully")
            # else:
            #     print("Error in removing reaction:", json_response.get("error"))
        else:
            print("Failed to remove reaction, status code:", response.status_code)
    
    def add_and_remove_reaction(self, add_emoji_list, remove_emoji_list, channel_name, timestamp):
        for emoji_name in add_emoji_list:
            self.add_reaction(emoji_name, channel_name, timestamp)
        for emoji_name in remove_emoji_list:
            self.remove_reaction(emoji_name, channel_name, timestamp)
    
