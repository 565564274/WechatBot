import openai

from openai import OpenAI
from pathlib import Path
from datetime import datetime

from utils import resource_pool
from utils.log import logger_manager
from utils.root_path import DEFAULT_TEMP_PATH


logger = logger_manager.logger


class ChatgptApi:

    def __init__(self, key=None):
        api_key = "sk-zpAHa2F4LeepcXwOzR8PASFWFbPxSRN6Cy4r31NuiNjLwpsq"
        api_base = "https://api.chatanywhere.tech/v1"
        self.client = OpenAI(
            api_key=key if key else resource_pool["chatgpt"]["api_key"],
            max_retries=1,
            timeout=30
        )
        self.model_name = resource_pool["chatgpt"]["model_name"]

    def model(self):
        return self.client.models.list()

    def get_key(self):
        return self.client.api_key

    def update_key_self(self):
        logger.info("********************************" * 6)
        used = self.get_key()
        if used not in resource_pool["chatgpt"]["api_key_option"]:
            logger.info(f"开始自更新OpenAI的api_key【{used}】,替换为api_key_option")
            new = resource_pool["chatgpt"]["api_key_option"][0]
        else:
            logger.info(f"开始自更新OpenAI的api_key【{used}】,更换api_key_option")
            index = resource_pool["chatgpt"]["api_key_option"].index(used)
            if index < len(resource_pool["chatgpt"]["api_key_option"]) - 1:
                index += 1
            else:
                index = len(resource_pool["chatgpt"]["api_key_option"]) - 1
            new = resource_pool["chatgpt"]["api_key_option"][index]

        self.client = OpenAI(
            api_key=new,
            max_retries=1,
            timeout=30
        )
        logger.info("自更新完成: " + str(self.get_key()))
        logger.info("********************************" * 6)

    def chat(self, messages, first=True, role=None):
        result = []
        if role:
            result[0] = {"role": "system", "content": role}
        for message in messages:
            result.append(
                {
                    "role": message[0],
                    "content": message[1]
                }
            )
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=result,
                timeout=30
            )
        except Exception as e:
            logger.error(e)
            if "This model's maximum context length" in str(e):
                return {"role": "assistant", "content": "已达到该Model最大对话长度，请重新回复【开始聊天】，重新开始与chatgpt对话"}
            elif "check your plan and billing details" in str(e):
                # Error code: 429 - {'error': {'message': 'You exceeded your current quota, please check your plan and billing details.', 'type': 'insufficient_quota', 'param': None, 'code': 'insufficient_quota'}}
                self.update_key_self()
                if first:
                    return self.chat(messages, first=False)
                return {"role": "assistant", "content": "这个ChatGPT账号没钱不能玩了，快去提醒他充值"}
            elif "Incorrect API key provided" in str(e):
                self.update_key_self()
                if first:
                    return self.chat(messages, first=False)
                return {"role": "assistant", "content": "这个ChatGPT账号的API key不对，快去提醒他看看"}
            elif "Rate limit reached" in str(e):
                # Rate limit reached for default-gpt-3.5-turbo-16k in organization org-vwVh2d6OFgt2xjsjnSEQJp8Z on requests per min. Limit: 3 / min.
                # Please try again in 20s. Contact us through our help center at help.openai.com if you continue to have issues.
                # Please add a payment method to your account to increase your rate limit. Visit https://platform.openai.com/account/billing to add a payment method.
                return {"role": "assistant", "content": "请求频率太高了，稍后再试"}
            else:
                return {"role": "assistant", "content": "未知错误，请重新回复【开始聊天】，重新开始与chatgpt对话"}
        return {"role": "assistant", "content": response.choices[0].message.content}

    def whisper(self, audio_file, first=True):
        try:
            transcription = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        except openai.APIError as e:
            logger.error(e)
            if e.code == "invalid_api_key":
                self.update_key_self()
                if first:
                    return self.whisper(audio_file, first=False)
                return False, "这个ChatGPT账号的API key不对，快去提醒他看看"
            elif "billing" in str(e):
                self.update_key_self()
                if first:
                    return self.whisper(audio_file, first=False)
                return False, "这个ChatGPT账号没钱不能玩了，快去提醒他充值"
            else:
                return False, "未知问题，生成失败\n请重新输入"
        except Exception as e:
            logger.error(e)
            return False, "未知问题，生成失败\n请重新输入"
        return True, transcription

    def tts(self, text, wx_id, first=True):
        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text,
            )
            wx_id_folder = DEFAULT_TEMP_PATH / wx_id
            if not Path(wx_id_folder).is_dir():
                Path(wx_id_folder).mkdir(exist_ok=True)
            output_path = wx_id_folder / f"{datetime.strftime(datetime.now(), '%Y-%m-%d_%H-%M-%S')}.mp3"
            response.stream_to_file(output_path)
        except openai.APIError as e:
            logger.error(e)
            if e.code == "invalid_api_key":
                self.update_key_self()
                if first:
                    return self.tts(text, wx_id, first=False)
                return False, "这个ChatGPT账号的API key不对，快去提醒他看看"
            elif "billing" in str(e):
                self.update_key_self()
                if first:
                    return self.tts(text, wx_id, first=False)
                return False, "这个ChatGPT账号没钱不能玩了，快去提醒他充值"
            else:
                return False, "未知问题，生成失败\n请重新输入"
        except Exception as e:
            logger.error(e)
            return False, "未知问题，生成失败\n请重新输入"
        return True, output_path


if __name__ == '__main__':
    a = ChatgptApi()
    # res = a.chat(
    #     [["user", "你好"], ["user", "你好"]]
    # )
    res = a.image(
        "比萨斜塔"
    )
    print(res)
