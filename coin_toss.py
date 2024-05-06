from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import random
from slack_module import SlackModule
from ttl_kvs_module import TTLKVSModule

slack_channel = 'airflow-alert'

# 失敗時のコールバック関数
def on_failure_callback(context):
    slackModule = SlackModule()
    kvsModule = TTLKVSModule()
    log_url = context['task_instance'].log_url
    dag_id = context['task_instance'].dag_id
    task_id = context['task_instance'].task_id
    execution_date = context['task_instance'].execution_date.isoformat()
    thread_ts_key = f'{dag_id}__{execution_date}__{task_id}__thread_ts'
    thread_ts = kvsModule.read(thread_ts_key)
    slack_message = f'{dag_id}の{task_id}でタスクが失敗しました {log_url}'
    new_thread_ts = slackModule.post_slack(slack_message, slack_channel, thread_ts=thread_ts)
    if not thread_ts:
        kvsModule.write(thread_ts_key, new_thread_ts)
        thread_ts = new_thread_ts
    slackModule.add_reaction('ng', slack_channel, thread_ts)

# リトライ時のコールバック関数
def on_retry_callback(context):
    slackModule = SlackModule()
    kvsModule = TTLKVSModule()
    log_url = context['task_instance'].log_url
    dag_id = context['task_instance'].dag_id
    task_id = context['task_instance'].task_id
    retry_number = context['task_instance'].try_number
    execution_date = context['task_instance'].execution_date.isoformat()
    thread_ts_key = f'{dag_id}__{execution_date}__{task_id}__thread_ts'
    thread_ts = kvsModule.read(thread_ts_key)
    slack_message = f'{dag_id}の{task_id}で{retry_number}回目のリトライを始めます {log_url}'
    new_thread_ts = slackModule.post_slack(slack_message, slack_channel, thread_ts=thread_ts)
    if not thread_ts:
        kvsModule.write(thread_ts_key, new_thread_ts)
        slackModule.add_reaction('repeat', slack_channel, new_thread_ts)

# 成功時のコールバック関数
def on_success_callback(context):
    slackModule = SlackModule()
    kvsModule = TTLKVSModule()
    log_url = context['task_instance'].log_url
    dag_id = context['task_instance'].dag_id
    task_id = context['task_instance'].task_id
    execution_date = context['task_instance'].execution_date.isoformat()
    thread_ts_key = f'{dag_id}__{execution_date}__{task_id}__thread_ts'
    thread_ts = kvsModule.read(thread_ts_key)
    slack_message = f'{dag_id}の{task_id}リトライ完了しました {log_url}'
    if thread_ts:
        slackModule.post_slack(slack_message, slack_channel, thread_ts=thread_ts)
        slackModule.add_reaction('ok', slack_channel, thread_ts)

# コイントス(裏が出たら失敗)のタスク
def coin_toss_task():
    random_value = random.random()
    if random_value < 0.5:
        raise Exception('裏が出たため失敗しました')
    print('表が出たため成功しました')

# DAGの定義
with DAG(
    'coin_toss',
    default_args={
        'owner': 'airflow',  # タスクの所有者
        'start_date': datetime(2024, 5, 5),  # DAGの開始日時
        'on_failure_callback': on_failure_callback,  # 失敗時のコールバック関数
        'on_retry_callback': on_retry_callback,  # リトライ発生時のコールバック関数
        'on_success_callback': on_success_callback,  # 成功時のコールバック関数
        'retries': 10,  # リトライ回数
        'retry_delay': timedelta(minutes=1),  # (最初の)リトライ間隔
        'retry_exponential_backoff': True,  # リトライ間隔を指数関数的に増加させるかどうか
        'max_retry_delay': timedelta(minutes=60),  # リトライ間隔の最大値
    },
    schedule_interval='0 3 * * *',  # ジョブのスケジュール間隔（JSTの12時に設定）
    catchup=False,  # 過去のジョブを実行するかどうか
) as dag:
    # コイントスタスク直列
    num_tasks = 5
    tasks = []
    for i in range(1, num_tasks + 1):
        task = PythonOperator(
            task_id=f'task_{i}',
            python_callable=coin_toss_task,
        )
        tasks.append(task)
        if len(tasks) > 1:
            tasks[-2] >> tasks[-1]
