#!/usr/bin/env python3

# Source:
# MCPで変わるAIエージェント開発 #LLM - Qiita
# https://qiita.com/ksonoda/items/1c681a563a95a93975ff#%E8%BF%BD%E5%8A%A0%E3%81%99%E3%82%8Bmcp%E3%82%B5%E3%83%BC%E3%83%90%E3%83%BC

from langchain_experimental.utilities import PythonREPL
from typing import Annotated
from mcp.server.fastmcp import FastMCP
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import japanize_matplotlib

import base64
from io import BytesIO
import contextlib
import sys
import re


def tategaki(label: str):
    """縦軸のラベルを縦書きにする関数

    Args:
        label (str): 横書きの文字列

    Returns:
        string: 縦書きで表示されることを前提とする文字列

    Note:
        参考:
        【matplotlib】軸ラベルを縦書きにしたい【python】 - 統計を学ぶ化学系技術者の記録
        https://chemstat.hatenablog.com/entry/2023/10/20/173700

        ggplot2で描画したグラフの軸タイトル・ラベルに，縦書きで日本語を書くための一案 - researchmap
        https://researchmap.jp/blogs/blog_entries/view/770208/9c9909e0702509937adf56b491673ec0?frame_id=1410143
    """
    # 文字の置換
    table = str.maketrans(
        {
            "ー": "丨",  # 長音符
            "（": "︵",  # 丸括弧開き
            "）": "︶",  # 丸括弧閉じ
            "「": "﹁",  # かぎ括弧開き
            "」": "﹂",  # かぎ括弧閉じ
            "『": "﹃",  # 二重かぎ括弧開き
            "』": "﹄",  # 二重かぎ括弧閉じ
        }
    )
    label = label.translate(table)
    # すべての文字の間に改行を挿入
    # 先頭と末尾以外のすべての間に\nを挿入
    return re.sub(r"(?<=.)(?=.)", "\n", label)


# MCP Server のインスタンス作成
mcp = FastMCP("PythonREPL")

# Python REPL ユーティリティの初期化
repl = PythonREPL()


@mcp.tool()
def python_repl(
    code: Annotated[str, "チャートを生成するために実行する Python コード"],
) -> str:
    """_summary_

    Args:
        code (Annotated[str, ): チャートを生成するために実行する Python コード

    Returns:
        str: グラフ作成成否のメッセージ
    """
    try:
        # stdout の捕捉
        stdout = BytesIO()
        with contextlib.redirect_stdout(sys.stdout):
            exec(code, globals())

        # matplotlibの画像を base64 に変換
        buf = BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        img_base64 = base64.b64encode(buf.read()).decode("utf-8")
        buf.close()
        plt.close()

        return f"Successfully executed:\n```python\n{code}\n```\n\n![chart](data:image/png;base64,{img_base64})"
    except BaseException as e:
        return f"Failed to execute. Error: {repr(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
