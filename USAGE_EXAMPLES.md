# Playwright Search Tool - 使用例集

## Claude Code からの使用方法

### 基本的なWebサーチ
```bash
# シンプルな検索
psearch search "Python プログラミング チュートリアル"

# 結果数を指定
psearch search "機械学習" -n 5

# 検索エンジンを指定  
psearch search "ウェブスクレイピング" -e bing

# すべてのエンジンで検索
psearch search "AI ニュース" -e all -n 3
```

### 高度な検索オプション
```bash
# コンテンツ抽出付きで検索
psearch search "データサイエンス" --extract-content

# JSON形式で出力
psearch search "ウェブ開発" --json

# 詳細ログ付きで実行
psearch search "デバッグ技法" --verbose

# ヘッドレスモードを無効化（ブラウザを表示）
psearch search "自動化テスト" --no-headless
```

### コンテンツ抽出
```bash
# 特定URLからコンテンツを抽出
psearch extract https://example.com/article

# JSON形式で抽出
psearch extract https://example.com/article --json
```

## 実用的な使用例

### 1. 開発情報の収集
```bash
# 最新のPythonライブラリ情報を取得
psearch search "Python ライブラリ 2024年 おすすめ" -n 10 --extract-content

# 特定のエラーメッセージの解決策を検索
psearch search "AttributeError: module has no attribute" -e all
```

### 2. 技術文書の検索
```bash
# Django関連のチュートリアルを検索
psearch search "Django チュートリアル 初心者" -n 5 --json > django_tutorials.json

# API仕様書を検索
psearch search "REST API ドキュメント ベストプラクティス" -e google
```

### 3. 市場調査・競合分析
```bash
# 競合他社の情報を収集
psearch search "プロジェクト管理ツール 比較" --extract-content

# 業界動向を調査
psearch search "AI開発 トレンド 2024" -e all -n 8
```

### 4. 学習リソース探し
```bash
# プログラミング学習サイトを検索
psearch search "プログラミング 学習サイト 無料" -n 15

# 特定技術の詳細記事を抽出
psearch search "Docker コンテナ 入門" --extract-content --json
```

## 自動化スクリプトでの使用

### Bash スクリプト例
```bash
#!/bin/bash
# research.sh - 自動リサーチスクリプト

TOPIC="$1"
if [ -z "$TOPIC" ]; then
    echo "Usage: $0 <research-topic>"
    exit 1
fi

echo "Researching: $TOPIC"

# Google検索
echo "=== Google Results ===" 
psearch search "$TOPIC" -e google -n 5 --json > "google_${TOPIC}.json"

# Bing検索  
echo "=== Bing Results ==="
psearch search "$TOPIC" -e bing -n 5 --json > "bing_${TOPIC}.json"

# DuckDuckGo検索
echo "=== DuckDuckGo Results ==="
psearch search "$TOPIC" -e duckduckgo -n 5 --json > "ddg_${TOPIC}.json"

echo "Research completed. Results saved to JSON files."
```

### Python スクリプト例
```python
#!/usr/bin/env python3
# auto_research.py

import subprocess
import json
import sys

def search_and_analyze(query, max_results=5):
    """検索を実行して結果を分析"""
    
    # 検索実行
    result = subprocess.run([
        'psearch', 'search', query, 
        '-n', str(max_results), 
        '--json', '-e', 'all'
    ], capture_output=True, text=True)
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        
        # 結果の分析
        print(f"Query: {query}")
        print(f"Total results: {len(data)}")
        
        for i, item in enumerate(data[:3], 1):
            print(f"{i}. {item['title']}")
            print(f"   URL: {item['url']}")
            print(f"   Source: {item['source']}")
            print()
            
        return data
    else:
        print(f"Search failed: {result.stderr}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 auto_research.py <query>")
        sys.exit(1)
        
    query = " ".join(sys.argv[1:])
    search_and_analyze(query)
```

## パフォーマンス最適化

### 高速検索設定
```bash
# タイムアウトを短縮
psearch search "クイック検索" --timeout 15

# 結果数を制限
psearch search "効率的な検索" -n 3

# 特定エンジンのみ使用
psearch search "高速検索" -e duckduckgo
```

### バッチ処理
```bash
# 複数のクエリを順次実行
queries=("Python" "JavaScript" "Go" "Rust")
for query in "${queries[@]}"; do
    echo "Searching for: $query"
    psearch search "$query programming" -n 3 --json >> "all_results.jsonl"
done
```

## トラブルシューティング

### 一般的な問題と解決法

1. **ブラウザインストールエラー**
   ```bash
   # Playwrightブラウザを再インストール
   uv run playwright install chromium
   ```

2. **検索結果が取得できない場合**
   ```bash
   # 異なるエンジンを試す
   psearch search "your query" -e bing
   psearch search "your query" -e duckduckgo
   
   # タイムアウトを延長
   psearch search "your query" --timeout 60
   ```

3. **ヘッドレスモードでの問題**
   ```bash
   # ブラウザを表示して確認
   psearch search "your query" --no-headless
   ```

## 設定とカスタマイズ

### 環境変数
```bash
export PLAYWRIGHT_HEADLESS=false  # ブラウザを表示
export PLAYWRIGHT_TIMEOUT=60000   # タイムアウト設定
export PLAYWRIGHT_SLOW_MO=1000    # 動作を遅く
```

### エイリアス設定
```bash
# ~/.bashrc に追加
alias search="psearch search"
alias extract="psearch extract"
alias qsearch="psearch search -n 3 -e google"  # クイック検索
```

## 応用例

### 1. ニュース収集
```bash
psearch search "技術ニュース 今日" -e all --extract-content --json > today_tech_news.json
```

### 2. 学術論文検索
```bash
psearch search "machine learning research papers 2024" -n 20 --extract-content
```

### 3. 価格比較
```bash
psearch search "ノートパソコン 価格比較" -e all -n 15 --json
```

これらの例を参考に、あなたの具体的な用途に合わせてPlaywright Search Toolを活用してください。