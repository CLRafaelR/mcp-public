#!/usr/bin/env python3

# Source:
# MCPで変わるAIエージェント開発 #LLM - Qiita
# https://qiita.com/ksonoda/items/1c681a563a95a93975ff#mcp%E3%82%B5%E3%83%BC%E3%83%90%E3%83%BC%E3%81%AE%E3%82%B3%E3%83%BC%E3%83%89

from mcp.server.fastmcp import FastMCP
from typing import Annotated
import yfinance as yf
import pandas as pd

# MCPサーバーインスタンスの作成
mcp = FastMCP("StockData")


# 株価データ取得関数
@mcp.tool()
def get_stock_data(
    ticker: Annotated[str, "企業のティッカーシンボル（例：AAPL、7203.T）"],
    start_date: Annotated[str, "データ取得の開始日 (YYYY-MM-DD)"],
    end_date: Annotated[str, "データ取得の終了日 (YYYY-MM-DD)"],
) -> str:
    """
    Yahooファイナンスから株価情報（日付, 始値, 高値, 安値, 終値, 出来高, 銘柄）を取得します。
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)

        if df.empty:
            return f"{ticker} のデータが見つかりませんでした。"

        df = df.reset_index()
        df["Ticker"] = ticker
        df = df.rename(
            columns={
                "Date": "日付",
                "Open": "始値",
                "High": "高値",
                "Low": "安値",
                "Close": "終値",
                "Volume": "出来高",
                "Ticker": "銘柄",
            }
        )

        result = df[
            ["日付", "銘柄", "始値", "高値", "安値", "終値", "出来高"]
        ].to_string(index=False)
        return f"{ticker} の株価データ:\n```\n{result}\n```"

    except Exception as e:
        return f"データ取得中にエラーが発生しました: {repr(e)}"


# サーバー起動（stdio）
if __name__ == "__main__":
    mcp.run(transport="stdio")
