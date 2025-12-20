from openai import AzureOpenAI
import json

class GPT4oClient:
    def __init__(self, endpoint: str, key: str, version: str, deployment: str):
        self.client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=key,
            api_version=version
        )
        self.model = deployment

    def json(self, system: str, user: str) -> dict:
        r = self.client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[{"role":"system","content":system},{"role":"user","content":user}]
        )
        return json.loads(r.choices[0].message.content)

    def answer(self, system: str, user: str) -> str:
        r = self.client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            messages=[{"role":"system","content":system},{"role":"user","content":user}]
        )
        return r.choices[0].message.content
