import json


class Config:

    def __init__(self, path):
        with open(path, 'r') as f:
            self.configData = json.loads(f.read())

    def get(self, key, default=None):
        return self.configData.get(key, default)
