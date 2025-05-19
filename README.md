# MCP 勉強用

## 概要

Model Context Protocol (MCP)を手元で構築しながら理解する

下記記事のコードを自分の手元で再現

MCP で変わる AI エージェント開発 #LLM - Qiita
https://qiita.com/ksonoda/items/1c681a563a95a93975ff#%E8%BF%BD%E5%8A%A0%E3%81%99%E3%82%8Bmcp%E3%82%B5%E3%83%BC%E3%83%90%E3%83%BC

上掲記事との違い

- langchain_mcp_adapters のバージョン 0.1.0 で動作することを前提にコードを書き換え
- yahoofinace_client.py におけるユーザーメッセージを，コマンドライン入力で入力できるように書き換え

### TODO

- yahoofinace_client.py において，メッセージのやり取りを記憶できるようにしなければならない
  - なぜなら，現状では会話履歴がないため，「○○ は？」のような以前の会話を前提とする入力に回答できないからだ

## ライセンス

MIT
