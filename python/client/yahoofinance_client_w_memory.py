#!/usr/bin/env python3

# 参考:
# MCPで変わるAIエージェント開発 #LLM - Qiita
# https://qiita.com/ksonoda/items/1c681a563a95a93975ff#mcp%E3%82%B5%E3%83%BC%E3%83%90%E3%83%BC%E3%81%AE%E3%82%B3%E3%83%BC%E3%83%89

# awesome-agent-quickstart/langchain-mcp-adapters/clients/multi_server_client.py at main · ababdotai/awesome-agent-quickstart
# https://github.com/ababdotai/awesome-agent-quickstart/blob/main/langchain-mcp-adapters/clients/multi_server_client.py

# from openai import AzureOpenAI
# from openai import OpenAI
import asyncio
from langchain_openai import ChatOpenAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.prebuilt import create_react_agent

from langgraph.checkpoint.memory import InMemorySaver
from langchain_core.messages.utils import (
    trim_messages,
    count_tokens_approximately,
)

import getpass
import os
import sys
from dotenv import load_dotenv
import subprocess
from datetime import datetime

import re
import base64

import pprint

# cd python
# uv run python client/yahoofinance_client.pyで動かすことを前提にしたパスは以下
# 絶対パスを使うことも可能
load_dotenv(dotenv_path="../.env.local")

if not os.environ.get("OPENAI_API_KEY"):
    os.environ["OPENAI_API_KEY"] = getpass.getpass(
        "OpenAIのAPIキーを入力してください: "
    )

checkpointer = InMemorySaver()


def pre_model_hook(state):
    """会話履歴を一定の長さに制限する

    This function will be called every time before the node that calls LLM

    Args:
        state: ステート

    Returns:

    """
    trimmed_messages = trim_messages(
        state["messages"],
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=10_000,
        start_on="human",
        include_system=True,
        end_on=("human", "tool"),
    )
    return {"llm_input_messages": trimmed_messages}


def format_message(i, m, n):
    """メッセージの内容をフォーマットする

    各メッセージのtypeとindexに応じて、出力用の文字列を生成する。

    Args:
        i (int): メッセージのインデックス
        m (object): メッセージオブジェクト（.type, .content属性を持つ）
        n (int): メッセージ全体の数

    Returns:
        str: 出力用の文字列
    """
    if m.type == "human":
        return f"# User\n\n{m.content}\n{'-'*16}\n"
    elif m.type == "ai" and i == n - 1:
        return f"# Agent's response\n\n{m.content}\n{'='*16}\n"
    else:
        return f"# Agent's thought: Round {i}\n\n{m.content}\n{'-'*16}\n"


def display_and_save_base64_image(text, output_dir="output/image"):
    """Base64エンコード画像が含まれている場合に，画像を保存し、表示する

    Args:
        text (str): 検索対象の文字列
        output_dir (str): 画像を保存するディレクトリ

    Returns:
        str or None: 保存した画像ファイルのパス（画像がなければNone）
    """
    match = re.search(r"data:image/png;base64,([A-Za-z0-9+/=]+)", text)
    if match:
        image_data = match.group(1)
        os.makedirs(output_dir, exist_ok=True)
        # ファイル名にタイムスタンプを付与
        filename = f"image_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "wb") as f:
            f.write(base64.b64decode(image_data))
        # OSごとに画像を開く
        try:
            if sys.platform.startswith("linux"):
                print("次のメッセージを入力する際は，画像ビューアを閉じてください")
                subprocess.run(["xdg-open", filepath])
                # 標準出力・標準エラー出力を/dev/nullにリダイレクト
                # with open(os.devnull, "w") as devnull:
                # subprocess.run(
                # ["xdg-open", filepath],
                # check=True,
                # stdout=devnull,
                # stderr=devnull,
                # )
            elif sys.platform == "darwin":
                print("次のメッセージを入力する際は，画像ビューアを閉じてください")
                subprocess.run(["open", filepath])
            elif sys.platform == "win32":
                print("次のメッセージを入力する際は，画像ビューアを閉じてください")
                os.startfile(filepath)
            else:
                print(f"次のURLに画像を保存しました（画像表示は非対応）: {filepath}")
        except Exception as e:
            print(f"画像ビューア起動時にエラーが発生しましたが、処理を継続します: {e}")

        return filepath

    return None


# 入力プロンプトを理解するためのLLMの定義
model = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    max_completion_tokens=None,
    timeout=None,
    max_retries=2,
    # api_key="...",  # if you prefer to pass api key in directly instaed of using env vars
    # base_url="...",
    # organization="...",
    # other params...
)

# MCPサーバーの定義
client = MultiServerMCPClient(
    {
        "stock": {
            "command": "python",
            # cd python
            # uv run python client/yahoofinance_client.pyで動かすことを前提にしたパスは以下
            # 絶対パスを使うことも可能
            "args": ["server/yahoofinance_server.py"],
            "transport": "stdio",
        },
        "chart": {
            "command": "python",
            "args": ["server/repl_server.py"],
            "transport": "stdio",
        },
    }
)


async def main():
    # MCPサーバーをツールとして定義
    tools = await client.get_tools()

    # エージェントの定義(LangGraphでReActエージェントを定義)
    agent = create_react_agent(
        model,
        tools,
        pre_model_hook=pre_model_hook,
        checkpointer=checkpointer,
    )

    config = {"configurable": {"thread_id": "1"}}

    try:
        while True:
            # ユーザー入力の受付
            user_message = input("質問を入力してください（Ctrl+Cで終了）: ")

            # 入力プロンプトの定義
            agent_response = await agent.ainvoke(
                {"messages": user_message},
                config,
            )

            pprint.pprint(agent_response)

            # 出力結果の表示
            messages = agent_response["messages"]
            n = len(messages)

            print(
                "\n".join(
                    map(lambda im: format_message(im[0], im[1], n), enumerate(messages))
                )
            )

            # Agent's thoughtやAgent's responseに対して画像表示・保存
            [display_and_save_base64_image(m.content) for m in messages]
    except KeyboardInterrupt:
        print("会話を終了します")


if __name__ == "__main__":
    asyncio.run(main())
