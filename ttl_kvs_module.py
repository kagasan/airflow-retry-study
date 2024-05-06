from airflow.models import Variable
from datetime import datetime, timedelta

class TTLKVSModule:
    # TTL付きのKVSを提供するモジュール
    # キーの有効期限が切れた場合はNoneを返す
    # キーの有効期限は日数で指定する
    # Variableに保存します
    def __init__(self, global_key='ttl_kvs_global'):
        self.global_key = global_key
        if not Variable.get(self.global_key, default_var={}, deserialize_json=True):
            Variable.set(self.global_key, {}, serialize_json=True)

    def read(self, key):
        # 指定されたキーの値を読み取る
        global_value = Variable.get(self.global_key, deserialize_json=True)
        if key in global_value:
            value = global_value[key]
            if value['ttl'] < datetime.now().timestamp():
                return None
            return value['value']
        return None

    def write(self, key, value, ttldays=1):
        # 指定されたキーと値を書き込む
        global_value = Variable.get(self.global_key, deserialize_json=True)
        global_value = {k: v for k, v in global_value.items() if v['ttl'] >= datetime.now().timestamp()}
        global_value[key] = {'value': value, 'ttl': (datetime.now() + timedelta(days=ttldays)).timestamp()}
        Variable.set(self.global_key, global_value, serialize_json=True)
