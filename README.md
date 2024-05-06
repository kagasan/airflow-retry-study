# airflow-retry-study
Airflowの自動リトライ設定をいい感じにカスタマイズしてヒューマンオペレーションを楽にしよう。という勉強のまとめ。
- 異常の早期把握
- PF障害の突破
- わかりやすいSlack通知

このようなリトライと通知を目指します。
![image](https://github.com/kagasan/airflow-retry-study/assets/2450046/44ee4db8-4144-4194-b2d6-657f4cca9680)

## 異常の早期把握
異常を早めに把握できるとステークホルダーへの連絡や原因調査を早めに始められます。

on_retry_callbackを導入するとよいです。
- https://airflow.apache.org/docs/apache-airflow/stable/administration-and-deployment/logging-monitoring/callbacks.html

on_retry_callbackは最初のリトライ時に呼ばれるため、リトライ回数やリトライ間隔を多めに設定していても早めに状況を把握できます。
![image](https://github.com/kagasan/airflow-retry-study/assets/2450046/fb970b01-79fc-45d7-9a5b-ec7b5999babc)


## PF障害の突破
あらかじめPF障害がどのようなものか想定できていると、それに合わせたリトライ設計できます。
逆にこれを満たしていないと、PF障害のたびにヒューマンオペレーションが発生しそう。

設計の例。
- 50%で失敗する->10回くらいリトライ設定しておく(10連続で失敗を引く確率はかなり低い)
- 3時間くらい失敗する時間帯が発生する->リトライ回数×リトライ間隔を3時間以上にする。30分間隔*10回とか。

想定される障害が複数通りある場合はリトライ設計を固定しにくい。この場合exponential backoffでリトライ間隔を数分～1時間と徐々に増やしていける。
この記事が詳しい。
- https://zenn.dev/c6tower/articles/c43e9f2fa93f5a

## わかりやすいSlack通知
同一タスクからの通知を1か所にまとめるとSlackでの確認が楽になる。
リトライ通知をスレッドにつなげていったり、リトライに成功したらスレッド起点の投稿にリアクションを付けてみる。

スレッド形式での返信やリアクションの追加には対象投稿のチャンネルとタイムスタンプがわかっていればよく、投稿時に返却されるタイムスタンプをリトライ間で共有することで通知を集約できる。
- https://api.slack.com/methods

Airflowのタスク間で情報を共有するといえばtask_instanceのxcomだが、冪等性確保のためリトライでxcomの情報がリセットされてしまう。外部のMySQLやKVSなどに情報を置くか、検証目的なら乱暴にvariablesを使ってしまうのがよいだろう。
- https://github.com/apache/airflow/issues/18917
- https://airflow.apache.org/docs/apache-airflow/stable/core-concepts/variables.html

## 全部まとめたコード例
50%で失敗するタスクを5つ直列接続したDAGを用意しました。
slack通知用のモジュールとkey-valueでデータ保持するモジュールを補助的に用意しています。

いくつかのポイントを押さえています。
- 最初のリトライ時にSlackに通知される
- 追加のリトライ情報と失敗と成功の通知はスレッドに追記される
- リトライで失敗した場合は:ng:が起点の投稿につけられる
- リトライで成功した場合は:ok:が起点の投稿につけられる
- リトライの間隔は1分から60分まで徐々に伸びていく
  - 今回のDAGならリトライ間隔固定でいいといわれるとまあそう...

