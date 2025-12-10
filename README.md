# HPB分析ツール

ホットペッパービューティーのサロンページを分析・比較するツールです。

## 機能

- **サロン分析**: HPBのサロンページをAIが自動分析
- **競合比較**: 最大3店舗（自店舗+競合2店舗）を比較
- **スコアリング**: 4項目で5段階評価
  - PV獲得力（閲覧数を増やす力）
  - CV転換力（予約につなげる力）
  - 価格競争力
  - 差別化ポイント
- **AIチャット**: 分析結果について質問可能
- **PDF出力**: レポートをPDFでダウンロード

## セットアップ

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. APIキーの設定

#### ローカル実行の場合

`.env`ファイルを作成:

```bash
cp .env.example .env
```

`.env`を編集してGemini APIキーを設定:

```
GEMINI_API_KEY=your_api_key_here
```

#### Streamlit Cloudの場合

1. Streamlit Cloudのダッシュボードにアクセス
2. アプリの設定 → Secrets
3. 以下を追加:

```toml
GEMINI_API_KEY = "your_api_key_here"
```

### 3. アプリの起動

```bash
streamlit run app.py
```

## Gemini APIキーの取得

1. [Google AI Studio](https://aistudio.google.com/app/apikey)にアクセス
2. Googleアカウントでログイン
3. 「Create API Key」をクリック
4. 生成されたAPIキーをコピー

## 使い方

1. 自店舗のホットペッパービューティーURLを入力
2. （任意）競合店舗のURLを入力（最大2つ）
3. 「分析を開始」をクリック
4. 結果を確認（スコア、チャート、改善提案）
5. 必要に応じてAIに質問
6. PDFレポートをダウンロード

## Streamlit Cloudへのデプロイ

1. GitHubにリポジトリを作成してプッシュ
2. [Streamlit Cloud](https://streamlit.io/cloud)にアクセス
3. 「New app」をクリック
4. GitHubリポジトリを選択
5. メインファイルに`app.py`を指定
6. Secretsに`GEMINI_API_KEY`を設定
7. 「Deploy」をクリック

## ファイル構成

```
hpb_comparison/
├── app.py                  # メインアプリケーション
├── modules/
│   ├── __init__.py
│   ├── analyzer.py         # Gemini API連携
│   ├── chart.py            # チャート生成
│   └── pdf_generator.py    # PDF出力
├── prompts/
│   ├── __init__.py
│   └── analysis_prompts.py # プロンプトテンプレート
├── .streamlit/
│   ├── config.toml         # Streamlit設定
│   └── secrets.toml.example
├── requirements.txt
├── .env.example
└── README.md
```

## 注意事項

- Gemini APIの利用制限に注意してください
- 分析には2-3分程度かかることがあります
- スマートフォンでの利用に最適化されています
