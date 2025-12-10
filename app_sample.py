import streamlit as st
import google.genai as genai
from google.genai.types import GenerateContentConfig
from urllib.parse import urlparse
import re
from PIL import Image
import plotly.graph_objects as go
import numpy as np
from datetime import datetime


def create_salon_analysis_prompt(url1, url2=None):
    """
    美容サロンWebサイト分析用のプロンプトを生成する関数

    Args:
        url1 (str): 分析対象の1つ目のURL
        url2 (str, optional): 分析対象の2つ目のURL。Noneの場合は単一サイト分析

    Returns:
        str: 条件に応じたプロンプト文
    """

    # スタイリスト関連のURL判定
    is_stylist_url = "/stylist/" in url1 or (url2 and "/stylist/" in url2)

    # 単一URL分析の場合
    if url2 is None:
        if is_stylist_url:
            # スタイリスト専用の単一分析プロンプト
            prompt = f"""あなたは美容サロンマーケティングの専門家です。
                        必ず日本語で回答してください。

                        以下のスタイリストWebサイトを詳細に分析し、予約ユーザーの視点からマーケティング戦略を考察してください。

                        【分析対象URL】
                        URL: {url1}

                        【分析項目】
                        スタイリストサイトとして以下の観点から強み・弱みを分析してください：

                        1. **スタイリストブランディング**
                        - 個人ブランドの確立度
                        - 専門性・個性の訴求力
                        - プロフィール情報の充実度
                        - スタイルの一貫性

                        2. **信頼性・専門性の構築**
                        - 経歴・実績の提示
                        - 資格・受賞歴の明示
                        - 顧客からの評価・口コミ
                        - メディア掲載・SNS影響力

                        3. **ポートフォリオ・作品展示**
                        - 施術事例の質と量
                        - Before/After画像の説得力
                        - スタイル別カテゴリー分け
                        - 画像品質・見せ方の工夫

                        4. **予約体験の最適化**
                        - 予約システムの使いやすさ
                        - 料金体系の透明性
                        - カウンセリング重視のアピール
                        - 予約前の不安解消要素

                        5. **顧客コミュニケーション**
                        - 接客スタイルの伝達
                        - お客様との関係性構築
                        - アフターケア・フォローアップ
                        - SNSでの情報発信

                        6. **差別化・独自性**
                        - 他のスタイリストとの違い
                        - 特化した技術・サービス
                        - ターゲット層の明確化
                        - 価値提案の独自性

                        【予約ユーザー視点での改善提案】
                        予約を検討しているユーザーが「このスタイリストに任せたい」と思えるよう、以下の観点から具体的な改善提案を行ってください：
                        - 初回来店のハードルを下げる工夫
                        - 技術力・センスを伝える効果的な方法
                        - 安心感・信頼感を高める要素の追加
                        - 予約完了までの導線改善

                        【出力形式】
                        上記項目の詳細分析と、予約ユーザー視点での具体的な改善提案をまとめてください。

                        最後に要約したサマリテキストも作成してください。"【サマリテキスト】"以下に改行も含めた3行～5行程度の文章で記載してください。
                        """
        else:
            # 通常の単一分析プロンプト
            prompt = f"""あなたは美容サロンマーケティングの専門家です。
                        必ず日本語で回答してください。

                        以下の美容サロンWebサイトを詳細に分析し、マーケティング戦略の観点から考察してください。

                        【分析対象URL】
                        URL: {url1}

                        【分析項目】
                        以下の観点からサイトの強み・弱みを分析してください：

                        1. **ブランディング・デザイン**
                        - ビジュアルアイデンティティ
                        - ターゲット層への訴求力
                        - ブランドイメージの一貫性

                        2. **ユーザーエクスペリエンス（UX）**
                        - サイト構造・ナビゲーション
                        - 予約システムの使いやすさ
                        - モバイル対応度

                        3. **コンテンツマーケティング**
                        - サービス内容の訴求力
                        - 施術事例・Before/After画像
                        - お客様の声・口コミ活用

                        4. **SEO・集客戦略**
                        - 検索エンジン最適化
                        - SNS連携
                        - 地域密着型マーケティング

                        5. **価格戦略・プロモーション**
                        - 料金体系の分かりやすさ
                        - キャンペーン・特典の魅力
                        - 新規顧客獲得施策

                        6. **信頼性・専門性**
                        - スタッフ紹介
                        - 資格・実績の提示
                        - 衛生管理・安全性のアピール

                        【出力形式】
                        上記6項目の強み・弱みを明確に示し、総合的な評価と改善提案をまとめてください。

                        最後に要約したサマリテキストも作成してください。"【サマリテキスト】"以下に改行も含めた3行～5行程度の文章で記載してください。
                        """

    # 2つのURL比較分析の場合
    else:
        if is_stylist_url:
            # スタイリスト専用の比較分析プロンプト
            prompt = f"""あなたは美容サロンマーケティングの専門家です。
                        必ず日本語で回答してください。

                        以下の2つのスタイリストWebサイトを詳細に分析し、予約ユーザーの視点からマーケティング戦略を比較考察してください。

                        【分析対象URL】
                        URL1: {url1}
                        URL2: {url2}

                        【分析項目】
                        スタイリストサイトとして以下の観点から各サイトの強み・弱みを比較分析してください：

                        1. **スタイリストブランディング**
                        - 個人ブランドの確立度
                        - 専門性・個性の訴求力
                        - プロフィール情報の充実度
                        - スタイルの一貫性

                        2. **信頼性・専門性の構築**
                        - 経歴・実績の提示
                        - 資格・受賞歴の明示
                        - 顧客からの評価・口コミ
                        - メディア掲載・SNS影響力

                        3. **ポートフォリオ・作品展示**
                        - 施術事例の質と量
                        - Before/After画像の説得力
                        - スタイル別カテゴリー分け
                        - 画像品質・見せ方の工夫

                        4. **予約体験の最適化**
                        - 予約システムの使いやすさ
                        - 料金体系の透明性
                        - カウンセリング重視のアピール
                        - 予約前の不安解消要素

                        5. **顧客コミュニケーション**
                        - 接客スタイルの伝達
                        - お客様との関係性構築
                        - アフターケア・フォローアップ
                        - SNSでの情報発信

                        6. **差別化・独自性**
                        - 他のスタイリストとの違い
                        - 特化した技術・サービス
                        - ターゲット層の明確化
                        - 価値提案の独自性

                        【予約ユーザー視点での改善提案】
                        各スタイリストについて、予約を検討しているユーザーが「このスタイリストに任せたい」と思えるよう、以下の観点から具体的な改善提案を行ってください：
                        - 初回来店のハードルを下げる工夫
                        - 技術力・センスを伝える効果的な方法
                        - 安心感・信頼感を高める要素の追加
                        - 予約完了までの導線改善

                        【出力形式】
                        必ず以下の順序で出力してください：
                        
                        【URL1分析結果】
                        URL1について上記6項目の詳細分析
                        
                        【URL2分析結果】
                        URL2について上記6項目の詳細分析
                        
                        【比較総合評価】
                        両サイトの競争優位性の比較と改善提案
                        
                        【サマリテキスト】
                        3行～5行程度の要約
                        """
        else:
            # 元の比較分析プロンプト
            prompt = f"""あなたは美容サロンマーケティングの専門家です。
                        必ず日本語で回答してください。

                        以下の2つの美容サロンWebサイトを詳細に分析し、マーケティング戦略の観点から比較考察してください。

                        【分析対象URL】
                        URL1: {url1}
                        URL2: {url2}

                        【分析項目】
                        以下の観点から各サイトの強み・弱みを分析してください：

                        1. **ブランディング・デザイン**
                        - ビジュアルアイデンティティ
                        - ターゲット層への訴求力
                        - ブランドイメージの一貫性

                        2. **ユーザーエクスペリエンス（UX）**
                        - サイト構造・ナビゲーション
                        - 予約システムの使いやすさ
                        - モバイル対応度

                        3. **コンテンツマーケティング**
                        - サービス内容の訴求力
                        - 施術事例・Before/After画像
                        - お客様の声・口コミ活用

                        4. **SEO・集客戦略**
                        - 検索エンジン最適化
                        - SNS連携
                        - 地域密着型マーケティング

                        5. **価格戦略・プロモーション**
                        - 料金体系の分かりやすさ
                        - キャンペーン・特典の魅力
                        - 新規顧客獲得施策

                        6. **信頼性・専門性**
                        - スタッフ紹介
                        - 資格・実績の提示
                        - 衛生管理・安全性のアピール

                        【出力形式】
                        必ず以下の順序で出力してください：
                        
                        【URL1分析結果】
                        URL1について上記6項目の詳細分析
                        
                        【URL2分析結果】
                        URL2について上記6項目の詳細分析
                        
                        【比較総合評価】
                        両サイトの競争優位性の比較と改善提案
                        
                        【サマリテキスト】
                        3行～5行程度の要約
                        """

    return prompt


def extract_scores_from_analysis(analysis_text):
    """
    改善された分析結果テキストから6つの項目の得点を抽出する関数
    カテゴリ別の詳細なキーワード分析で一貫性のあるスコアを生成

    Args:
        analysis_text (str): Gemini APIからの分析結果テキスト

    Returns:
        dict: 各項目の得点（1-10点）
    """
    
    # カテゴリ別の詳細キーワード定義
    detailed_keywords = {
        'ブランディング・デザイン': {
            'excellent': ['統一されたビジュアル', 'プロフェッショナル', '洗練', 'ブランドアイデンティティ', 'デザインの一貫性', '高品質な画像', 'ブランドカラー', '美しいレイアウト'],
            'good': ['清潔感', '見やすい', '整理された', '統一感', 'シンプル', '分かりやすい', '美しい', '魅力的'],
            'average': ['普通', '標準的', '一般的', '基本的', 'まずまず', '可もなく不可もなく'],
            'poor': ['古い', '統一感がない', '分かりにくい', '雑然', 'ごちゃごちゃ', '低品質', '見づらい', 'デザインが古い']
        },
        'ユーザーエクスペリエンス': {
            'excellent': ['直感的', 'ナビゲーションが優秀', '使いやすい', 'スムーズ', '高速', 'モバイル最適化', '予約しやすい', 'UXが秀逸'],
            'good': ['使いやすい', 'ナビゲーションが良い', '操作しやすい', '分かりやすい', '便利', '快適'],
            'average': ['普通', '標準的', 'まずまず', '基本的な機能'],
            'poor': ['分かりにくい', '使いづらい', '複雑', '不便', '遅い', 'モバイル非対応', '予約が難しい']
        },
        'コンテンツマーケティング': {
            'excellent': ['豊富なコンテンツ', '魅力的な写真', 'ストーリーテリング', '充実したブログ', 'SNS連携', '継続的更新'],
            'good': ['コンテンツが豊富', '写真が魅力的', 'ブログ更新', 'SNS活用', '情報充実'],
            'average': ['普通のコンテンツ', '基本的な情報', 'まずまず'],
            'poor': ['コンテンツ不足', '更新されていない', '情報が少ない', '古い情報', '魅力に欠ける']
        },
        'SEO・集客戦略': {
            'excellent': ['SEO最適化', '検索上位', 'SNS活用', 'Web集客', 'デジタルマーケティング', '効果的な集客'],
            'good': ['SEO対策', 'SNS連携', 'Web活用', '集客施策'],
            'average': ['基本的なSEO', '普通の集客'],
            'poor': ['SEO対策不足', '集客力が弱い', 'Web活用が不十分', '検索されにくい']
        },
        '価格戦略・プロモーション': {
            'excellent': ['料金が明確', '魅力的な価格', 'お得なプラン', 'キャンペーン充実', '価格競争力'],
            'good': ['料金体系が分かりやすい', 'リーズナブル', 'キャンペーンあり', '価格設定が良い'],
            'average': ['普通の価格設定', '標準的な料金', 'まずまずの価格'],
            'poor': ['料金が不明確', '高すぎる', 'キャンペーンなし', '価格競争力がない', '料金体系が複雑']
        },
        '信頼性・専門性': {
            'excellent': ['資格保有者多数', '実績豊富', '専門知識', '技術力が高い', '信頼できる', '経験豊富'],
            'good': ['資格あり', '実績がある', '信頼できる', '技術力', '専門性'],
            'average': ['普通の実績', '基本的な技術', 'まずまず'],
            'poor': ['実績が少ない', '専門性に欠ける', '信頼性に疑問', '技術力不足', '情報不足']
        }
    }
    
    # 初期スコア設定
    scores = {
        'ブランディング・デザイン': 5,
        'ユーザーエクスペリエンス': 5,
        'コンテンツマーケティング': 5,
        'SEO・集客戦略': 5,
        '価格戦略・プロモーション': 5,
        '信頼性・専門性': 5
    }
    
    # 各カテゴリの分析
    for category, keywords in detailed_keywords.items():
        category_score = calculate_detailed_category_score(analysis_text, category, keywords)
        scores[category] = category_score
    
    return scores


def calculate_detailed_category_score(analysis_text, category, keywords):
    """
    カテゴリ別の詳細スコア計算
    
    Args:
        analysis_text (str): 分析テキスト
        category (str): 分析カテゴリ
        keywords (dict): カテゴリ別キーワード辞書
        
    Returns:
        int: 1-10のスコア
    """
    
    # カテゴリ関連のテキストを抽出（より広範囲で検索）
    category_patterns = [
        rf'{category}.*?(?=\d+\.|\n\n|\Z)',  # カテゴリ名から次の項目まで
        rf'(?:【{category}】|{category}|{category.replace("・", "")}).*?(?=【|\d+\.|\n\n|\Z)'  # より柔軟なパターン
    ]
    
    category_text = ""
    for pattern in category_patterns:
        matches = re.findall(pattern, analysis_text, re.DOTALL | re.IGNORECASE)
        if matches:
            category_text += " ".join(matches)
    
    # より広範囲でも関連キーワードを検索
    if not category_text:
        category_text = analysis_text
    
    # キーワードマッチング
    excellent_count = 0
    good_count = 0
    average_count = 0
    poor_count = 0
    
    # 各レベルのキーワードをカウント
    for keyword in keywords['excellent']:
        excellent_count += len(re.findall(rf'{re.escape(keyword)}', category_text, re.IGNORECASE))
    
    for keyword in keywords['good']:
        good_count += len(re.findall(rf'{re.escape(keyword)}', category_text, re.IGNORECASE))
    
    for keyword in keywords['average']:
        average_count += len(re.findall(rf'{re.escape(keyword)}', category_text, re.IGNORECASE))
        
    for keyword in keywords['poor']:
        poor_count += len(re.findall(rf'{re.escape(keyword)}', category_text, re.IGNORECASE))
    
    # スコア計算ロジック
    total_matches = excellent_count + good_count + average_count + poor_count
    
    if total_matches == 0:
        return 5  # デフォルトスコア
    
    # 重み付けスコア計算
    weighted_score = (
        excellent_count * 10 + 
        good_count * 7 + 
        average_count * 5 + 
        poor_count * 2
    ) / total_matches
    
    # 1-10の範囲に正規化
    final_score = max(1, min(10, round(weighted_score)))
    
    return final_score


def stabilize_scores(analysis_text, num_runs=3):
    """
    複数回実行して安定したスコアを取得
    
    Args:
        analysis_text (str): 分析テキスト
        num_runs (int): 実行回数
        
    Returns:
        dict: 安定化されたスコア
    """
    all_scores = []
    
    for _ in range(num_runs):
        scores = extract_scores_from_analysis(analysis_text)
        all_scores.append(scores)
    
    # 平均値で安定化
    stable_scores = {}
    categories = all_scores[0].keys()
    
    for category in categories:
        category_scores = [run[category] for run in all_scores]
        stable_scores[category] = round(sum(category_scores) / len(category_scores), 1)
    
    return stable_scores


def create_radar_chart(scores_url1, scores_url2=None, url1="URL1", url2="URL2"):
    """
    レーダーチャートを作成する関数

    Args:
        scores_url1 (dict): URL1の得点
        scores_url2 (dict, optional): URL2の得点
        url1 (str): URL1の表示名
        url2 (str): URL2の表示名

    Returns:
        plotly.graph_objects.Figure: レーダーチャート
    """

    categories = list(scores_url1.keys())

    fig = go.Figure()

    # URL1のデータ（線を閉じるために最初の値を最後に追加）
    values1 = list(scores_url1.values()) + [list(scores_url1.values())[0]]
    categories_closed = categories + [categories[0]]

    fig.add_trace(go.Scatterpolar(
        r=values1,
        theta=categories_closed,
        fill='toself',
        name=url1,
        line_color='rgb(0, 123, 255)',
        fillcolor='rgba(0, 123, 255, 0.2)',
        mode='lines+markers'
    ))

    # URL2のデータ（比較分析の場合）
    if scores_url2:
        values2 = list(scores_url2.values()) + [list(scores_url2.values())[0]]
        fig.add_trace(go.Scatterpolar(
            r=values2,
            theta=categories_closed,
            fill='toself',
            name=url2,
            line_color='rgb(255, 99, 71)',
            fillcolor='rgba(255, 99, 71, 0.2)',
            mode='lines+markers'
        ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickvals=[2, 4, 6, 8, 10],
                ticktext=['2', '4', '6', '8', '10']
            )
        ),
        showlegend=True,
        title="美容サロン分析 - レーダーチャート比較",
        font=dict(size=12),
        height=600
    )

    return fig


def extract_numerical_data(analysis_text):
    """
    分析結果から主要3つの数値データを抽出する関数

    Args:
        analysis_text (str): 分析結果テキスト

    Returns:
        dict: 抽出された数値データ（評価スコア、レビュー数、女性比率）
    """

    numerical_data = {}

    # 1. 評価スコアの抽出（4.0-5.0範囲）
    score_patterns = [
        r'(\d+\.\d+).*?(?:点|星|★)',
        r'(?:評価|スコア|点数|rating|score).*?(\d+\.\d+)',
        r'(\d+\.\d+).*?(?:/5|out\s+of\s+5)',
        r'(\d+\.\d+).*?(?:rating|score)',
    ]

    for pattern in score_patterns:
        matches = re.findall(pattern, analysis_text, re.IGNORECASE)
        if matches:
            try:
                score = float(matches[0])
                if 1.0 <= score <= 5.0:  # 妥当な評価スコア範囲
                    numerical_data['評価スコア'] = score
                    break
            except:
                continue

    # 2. レビュー数の抽出
    review_patterns = [
        r'(\d+,?\d*).*?(?:件|個|つ).*?(?:口コミ|レビュー|評価|review)',
        r'(?:口コミ|レビュー|評価|review).*?(\d+,?\d*).*?(?:件|個|つ)',
        r'(\d+,?\d*).*?(?:reviews?|ratings?)',
        r'based\s+on\s+(\d+,?\d*)',
    ]

    for pattern in review_patterns:
        matches = re.findall(pattern, analysis_text, re.IGNORECASE)
        if matches:
            try:
                review_str = matches[0].replace(',', '')
                review_count = int(review_str)
                if 1 <= review_count <= 50000:  # 妥当なレビュー数範囲
                    numerical_data['レビュー数'] = review_count
                    break
            except:
                continue

    # 3. 女性比率の抽出
    female_ratio_patterns = [
        r'女性.*?(\d+)%',
        r'(\d+)%.*?女性',
        r'女性.*?(\d+)\s*パーセント',
        r'女性客.*?(\d+)%',
        r'female.*?(\d+)%',
        r'(\d+)%.*?female',
        r'女性の利用者.*?(\d+)%',
    ]

    for pattern in female_ratio_patterns:
        matches = re.findall(pattern, analysis_text, re.IGNORECASE)
        if matches:
            try:
                ratio = int(matches[0])
                if 0 <= ratio <= 100:  # 妥当なパーセンテージ範囲
                    numerical_data['女性比率'] = ratio
                    break
            except:
                continue

    return numerical_data


def create_comparison_bar_chart(data_url1, data_url2, url1_name="URL1", url2_name="URL2"):
    """
    主要3指標の比較棒グラフを作成する関数

    Args:
        data_url1 (dict): URL1の数値データ
        data_url2 (dict): URL2の数値データ
        url1_name (str): URL1の表示名
        url2_name (str): URL2の表示名

    Returns:
        plotly.graph_objects.Figure: 比較棒グラフ
    """

    # 優先順位付きの指標リスト
    priority_keys = ['評価スコア', 'レビュー数', '女性比率']

    # 共通する指標のみを使用（優先順位順）
    common_keys = []
    for key in priority_keys:
        if key in data_url1 and key in data_url2:
            common_keys.append(key)

    if not common_keys:
        return None

    values1 = [data_url1[key] for key in common_keys]
    values2 = [data_url2[key] for key in common_keys]

    # 評価スコアは10倍して見やすくする
    normalized_values1 = []
    normalized_values2 = []
    y_axis_labels = []

    for i, key in enumerate(common_keys):
        if key == '評価スコア':
            normalized_values1.append(values1[i] * 2)  # 2倍して視認性向上
            normalized_values2.append(values2[i] * 2)
            y_axis_labels.append(f"{key} (×2)")
        else:
            normalized_values1.append(values1[i])
            normalized_values2.append(values2[i])
            y_axis_labels.append(key)

    fig = go.Figure(data=[
        go.Bar(
            name=url1_name,
            x=y_axis_labels,
            y=normalized_values1,
            marker_color='rgb(0, 123, 255)',
            text=[f"{val:.1f}" if isinstance(val, float) else f"{val:,}" for val in values1],
            textposition='auto'
        ),
        go.Bar(
            name=url2_name,
            x=y_axis_labels,
            y=normalized_values2,
            marker_color='rgb(255, 99, 71)',
            text=[f"{val:.1f}" if isinstance(val, float) else f"{val:,}" for val in values2],
            textposition='auto'
        )
    ])

    fig.update_layout(
        barmode='group',
        title="主要指標比較",
        font=dict(size=11),
        height=350,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(t=60, b=40, l=40, r=40)
    )

    # Y軸の調整
    fig.update_yaxis(title="値")

    return fig


def extract_site_name(url, analysis_text=""):
    """
    URLや分析結果から店舗名・スタイリスト名を抽出する関数

    Args:
        url (str): 対象URL
        analysis_text (str): 分析結果テキスト

    Returns:
        str: 抽出された名前
    """

    if not url:
        return "未設定"

    # 分析結果から店舗名・スタイリスト名を抽出（より幅広いパターン）
    name_patterns = [
        # 直接的な店舗名・スタイリスト名の記載
        r'(?:店舗名|サロン名|店名|美容院名)\s*[：:]\s*([^\n\r。,]+)',
        r'(?:スタイリスト名?|美容師名?)\s*[：:]\s*([^\n\r。,]+)',

        # カッコ内の名前
        r'「([^」]{3,20})」',
        r'『([^』]{3,20})』',
        r'\[([^\]]{3,20})\]',

        # 一般的なサロン名パターン
        r'([A-Za-z\s]{3,20}(?:サロン|Salon|SALON|ヘア|Hair|HAIR|美容|Beauty|BEAUTY))',
        r'((?:サロン|ヘア|美容)\s*[A-Za-z\s]{3,20})',

        # ホットペッパー特有のパターン
        r'beauty\.hotpepper\.jp/.*?/([^/]{3,20})/',

        # 地名 + サロンパターン
        r'([^\s]{2,10}(?:駅前|店|サロン|美容室))',
    ]

    for pattern in name_patterns:
        matches = re.findall(pattern, analysis_text, re.IGNORECASE)
        if matches:
            name = matches[0].strip()
            # 短すぎる名前や一般的すぎる単語は除外
            if len(name) >= 3 and name not in ['サロン', 'ヘア', '美容', 'Salon', 'Hair', 'Beauty']:
                return name

    # URL パスから抽出を試行
    try:
        if 'beauty.hotpepper.jp' in url:
            path_parts = url.split('/')
            for i, part in enumerate(path_parts):
                if part in ['slnH', 'stylist'] and i + 1 < len(path_parts):
                    code = path_parts[i + 1][:8]  # 8文字に制限
                    if '/stylist/' in url:
                        return f"スタイリスト({code})"
                    else:
                        return f"サロン({code})"
    except:
        pass

    # 最終的なフォールバック
    if '/stylist/' in url:
        return "スタイリスト"
    else:
        return "サロン"


# チャット機能関数群
def display_chat_cta_and_section():
    """CTAボタン付きのチャット機能を表示"""
    # Phase 1: 視覚的強調のためのCSS
    st.markdown("""
    <style>
    .chat-highlight {
        background: linear-gradient(135deg, #e3f2fd 0%, #f0f8ff 100%);
        border: 2px solid #2196f3;
        border-radius: 15px;
        padding: 25px;
        margin: 25px 0;
        box-shadow: 0 6px 20px rgba(33, 150, 243, 0.2);
        animation: pulse-border 3s infinite;
    }
    
    @keyframes pulse-border {
        0% { box-shadow: 0 6px 20px rgba(33, 150, 243, 0.2); }
        50% { box-shadow: 0 8px 25px rgba(33, 150, 243, 0.4); }
        100% { box-shadow: 0 6px 20px rgba(33, 150, 243, 0.2); }
    }
    
    .chat-cta {
        text-align: center;
        padding: 20px;
        margin: 20px 0;
    }
    
    .chat-title {
        font-size: 1.3em;
        font-weight: bold;
        color: #1976d2;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # CTAボタンエリア
    st.markdown("---")
    st.markdown('<div class="chat-cta">', unsafe_allow_html=True)
    
    # 目立つタイトル
    st.markdown('<div class="chat-title">💬 分析結果について詳しく質問しませんか？</div>', unsafe_allow_html=True)
    st.markdown("**AIアシスタントが改善提案をサポートします！**")
    
    # CTAボタン
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        chat_clicked = st.button(
            "🚀 チャットで深掘り分析を開始", 
            type="primary", 
            use_container_width=True,
            help="分析結果について詳しく質問できます"
        )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # チャットが開かれた状態を管理
    if 'chat_opened' not in st.session_state:
        st.session_state['chat_opened'] = False
    
    if chat_clicked:
        st.session_state['chat_opened'] = True
        st.rerun()
    
    # チャットセクション（強調表示で囲む）
    if st.session_state['chat_opened']:
        st.markdown('<div class="chat-highlight">', unsafe_allow_html=True)
        display_chat_section()
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # プレビュー表示
        with st.expander("💡 こんな質問ができます（プレビュー）", expanded=False):
            st.markdown("""
            **📋 よくある質問例：**
            - 🎯 どの項目を最優先で改善すべきか？
            - 💰 改善にはどのくらいの予算が必要？
            - 📈 具体的な改善アクションプランは？
            - 🔍 競合他社との差別化ポイントは？
            - 📱 モバイル対応の改善方法は？
            - 🎨 ブランディング強化の具体的な手法は？
            """)


def display_chat_section():
    """チャット機能を表示"""
    st.subheader("💬 AI改善提案アシスタント")
    st.markdown("🎯 **専門的なアドバイスを即座に提供**　｜　💡 **具体的な改善案が得られます**")

    # チャット履歴の初期化
    if 'chat_messages' not in st.session_state:
        st.session_state['chat_messages'] = []
        # ウェルカムメッセージ
        st.session_state['chat_messages'].append({
            "role": "assistant",
            "content": "こんにちは！分析結果について何でもお聞きください。\n\n📈 **改善提案や具体的な実装方法についてお答えできます：**\n• 予約率向上の具体的な施策\n• ブランディング強化の方法\n• UX改善のポイント\n• 競合との差別化戦略\n• 費用対効果の高い改善案\n\nお気軽にご質問ください！",
            "timestamp": datetime.now()
        })

    # よくある質問ボタン
    display_quick_question_buttons()

    # フリーメッセージ入力エリア
    st.markdown("---")
    st.markdown("### ✍️ 自由に質問してください")
    
    # 3行のテキストエリア（目立つスタイル付き）
    st.markdown("""
    <style>
    .stTextArea > div > div > textarea {
        background: linear-gradient(135deg, #fff3e0 0%, #fff8e1 100%);
        border: 2px solid #ff9800;
        border-radius: 10px;
        padding: 15px;
        font-size: 16px;
        box-shadow: 0 4px 12px rgba(255, 152, 0, 0.2);
    }
    .stTextArea > div > div > textarea:focus {
        border-color: #f57c00;
        box-shadow: 0 6px 20px rgba(255, 152, 0, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)
    
    user_input = st.text_area(
        "💬 分析結果について詳しく質問してください：",
        placeholder="例: ブランディングをもっと具体的に改善するにはどうすればいいですか？\n競合との差別化を図るための具体的なアクションプランを教えてください。\n改善にはどの程度の予算が必要でしょうか？",
        height=120,
        help="詳しい質問ほど、より具体的で実践的なアドバイスを提供できます"
    )
    
    # 送信ボタン（目立つデザイン）
    col1, col2, col3 = st.columns([2, 1, 2])
    with col2:
        send_clicked = st.button(
            "📤 質問を送信", 
            type="primary",
            use_container_width=True,
            disabled=not user_input.strip() if user_input else True
        )
    
    if send_clicked and user_input and user_input.strip():
        handle_chat_input(user_input.strip())

    # チャット履歴表示
    st.markdown("---")
    st.markdown("### 💬 チャット履歴")

    # チャット履歴を表示
    for message in st.session_state['chat_messages']:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            st.caption(f"🕐 {message['timestamp'].strftime('%H:%M:%S')}")

    # チャット履歴クリアボタン
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("🗑️ チャット履歴をクリア", key="clear_chat_history", type="secondary"):
            st.session_state['chat_messages'] = []
            st.success("チャット履歴をクリアしました")
            st.rerun()

def display_quick_question_buttons():
    """よくある質問のボタン群"""
    st.markdown("**💡 よくある質問**")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📈 予約率向上策", key="btn_conversion"):
            handle_predefined_question("分析結果を基に、予約率を向上させるための具体的な改善策を教えてください。優先順位も含めて提案してください。")

    with col2:
        if st.button("🎯 改善優先順位", key="btn_priority"):
            handle_predefined_question("分析結果から、どの項目を最優先で改善すべきか教えてください。費用対効果も考慮して具体的に説明してください。")

    with col3:
        if st.button("💰 費用対効果", key="btn_cost"):
            handle_predefined_question("提案された改善の費用対効果と実装期間を教えてください。予算別の改善プランも提案してください。")

def handle_chat_input(user_message):
    """チャット入力の処理"""
    # ユーザーメッセージを追加
    st.session_state['chat_messages'].append({
        "role": "user",
        "content": user_message,
        "timestamp": datetime.now()
    })

    # AI応答を生成
    with st.spinner("🤔 回答を生成中..."):
        try:
            response = generate_chat_response(user_message)
            st.session_state['chat_messages'].append({
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now()
            })
        except Exception as e:
            error_response = f"申し訳ございません。回答生成中にエラーが発生しました。もう一度お試しください。\n\nエラー詳細: {str(e)}"
            st.session_state['chat_messages'].append({
                "role": "assistant",
                "content": error_response,
                "timestamp": datetime.now()
            })

    st.rerun()

def handle_predefined_question(question):
    """定型質問の処理"""
    handle_chat_input(question)

def generate_chat_response(user_message):
    """分析結果を基にした応答を生成"""
    # 分析結果をコンテキストに含める
    analysis_context = st.session_state.get('analysis_result', '')
    current_url1 = st.session_state.get('current_url1', '')
    current_url2 = st.session_state.get('current_url2', '')

    # 過去の会話履歴を取得（最新10件）
    recent_messages = st.session_state['chat_messages'][-10:]
    chat_history = ""
    for msg in recent_messages:
        if msg['role'] != 'assistant' or len(msg['content']) < 300:  # 長すぎる応答は除外
            chat_history += f"{msg['role']}: {msg['content']}\n"

    context_prompt = f"""あなたは美容サロンマーケティングのプロフェッショナルコンサルタントです。

【分析対象情報】
URL1: {current_url1}
URL2: {current_url2}

【詳細分析結果】
{analysis_context}

【過去の会話履歴】
{chat_history}

【ユーザーの質問】
{user_message}

上記の分析結果を踏まえて、以下の点に注意して回答してください：
- 分析結果の具体的なデータや得点を根拠として活用
- 美容業界の専門知識を活かした実践的なアドバイス
- 改善提案は具体的かつ実行可能なものに
- 優先順位や費用対効果も考慮
- 必ず日本語で簡潔で実用的な内容に

具体的で実践的なアドバイスを提供してください。"""

    # API設定（他の部分と同じ設定を使用）
    api_key = st.secrets["gemini"]["GOOGLE_API_KEY"]

    # Gemini APIクライアントを作成
    client = genai.Client(api_key=api_key)

    # Gemini APIで応答生成
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=context_prompt,
        config=GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=2048
        )
    )

    # 安全にレスポンスを取得
    try:
        if hasattr(response, 'text') and response.text:
            return response.text
        elif hasattr(response, 'candidates') and response.candidates and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                    return candidate.content.parts[0].text
                elif hasattr(candidate.content, 'text'):
                    return candidate.content.text
        
        # フォールバック
        return "申し訳ございません。回答を生成できませんでした。もう一度お試しください。"
        
    except Exception as e:
        return f"レスポンス処理中にエラーが発生しました: {str(e)}"


# 使用例
# 単一URL分析の場合
# prompt = create_salon_analysis_prompt("https://example.com/salon")

# スタイリスト単一分析の場合
# prompt = create_salon_analysis_prompt("https://example.com/stylist/john")

# 2つのURL比較分析の場合
# prompt = create_salon_analysis_prompt("https://example.com/salon1", "https://example.com/salon2")

# スタイリスト比較分析の場合
# prompt = create_salon_analysis_prompt("https://example.com/stylist/john", "https://example.com/stylist/mary")



# ファビコン用画像を読み込み
favicon = Image.open('kuroco-icon.png')

# ページ設定
st.set_page_config(
    page_title="ホットペッパービューティー比較アプリ",
    page_icon=favicon,
    layout="wide"
)

# タイトル
st.title("🔍 ホットペッパービューティー比較アプリ")
st.markdown("---")

# API キーを設定ファイルから読み込み
api_key = st.secrets["gemini"]["GOOGLE_API_KEY"]

# メイン画面
col1, col2 = st.columns(2)

with col1:
    st.subheader("📝 URL入力")
    url1 = st.text_input(
        "URL 1",
        placeholder="https://example1.com",
        help="比較したい最初のURLを入力してください"
    )

    url2 = st.text_input(
        "URL 2",
        placeholder="https://example2.com",
        help="比較したい2つ目のURLを入力してください"
    )


prompt = create_salon_analysis_prompt(url1, url2)


with col2:
    st.subheader("ℹ️ 使用方法")
    st.markdown("""
    **美容サロン・スタイリスト専門分析ツール**

    📋 **対応URL**
    - ホットペッパービューティー サロンページ
    - ホットペッパービューティー スタイリストページ
    - その他美容関連サイト

    🔍 **分析パターン**
    - **比較分析**: URL1・URL2両方入力（2サイトの比較分析）

    📊 **操作手順**
    1. 左側に比較したい2つのURLを入力
    2. 「比較開始」ボタンをクリックして分析実行
    3. 詳細な分析結果を確認後、必要に応じてダウンロード

    💡 **分析項目**: ブランディング、UX、コンテンツ、SEO、価格戦略、信頼性など
    """)

st.markdown("---")


# URL検証関数
def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False


# 比較実行ボタン
if st.button("🚀 比較開始", type="primary", use_container_width=True):
    # 入力検証
    if not url1 or not url2:
        st.error("❌ 両方のURLを入力してください")
    elif not is_valid_url(url1) or not is_valid_url(url2):
        st.error("❌ 有効なURLを入力してください")
    else:
        try:
            # Gemini API設定
            client = genai.Client(api_key=api_key)
            model_id = "gemini-2.5-flash"
            tools = [
                      {"url_context": {}},
            ]
            with st.spinner("🔄 URL比較を実行中..."):

                # # URL比較プロンプト
                # prompt = f"""あなたは美容サロンマーケティングの専門家です。
                # 必ず日本語で回答してください。

                # 以下の2つの美容サロンWebサイトを詳細に分析し、マーケティング戦略の観点から比較考察してください。

                # 【分析対象URL】
                # URL1: {url1}
                # URL2: {url2}

                # 【分析項目】
                # 以下の観点から各サイトの強み・弱みを分析してください：

                # 1. **ブランディング・デザイン**
                # - ビジュアルアイデンティティ
                # - ターゲット層への訴求力
                # - ブランドイメージの一貫性

                # 2. **ユーザーエクスペリエンス（UX）**
                # - サイト構造・ナビゲーション
                # - 予約システムの使いやすさ
                # - モバイル対応度

                # 3. **コンテンツマーケティング**
                # - サービス内容の訴求力
                # - 施術事例・Before/After画像
                # - お客様の声・口コミ活用

                # 4. **SEO・集客戦略**
                # - 検索エンジン最適化
                # - SNS連携
                # - 地域密着型マーケティング

                # 5. **価格戦略・プロモーション**
                # - 料金体系の分かりやすさ
                # - キャンペーン・特典の魅力
                # - 新規顧客獲得施策

                # 6. **信頼性・専門性**
                # - スタッフ紹介
                # - 資格・実績の提示
                # - 衛生管理・安全性のアピール

                # 【出力形式】
                # 各サイトについて上記6項目の強み・弱みを明確に示し、最後に総合的な競争優位性を評価してください。改善提案も含めて分析結果をまとめてください。

                # 最後に要約したサマリテキストも作成してください。"【サマリテキスト】"以下に改行も含めた3行～5行程度の文章で記載してください。
                # """

                # 比較分析実行
                response = client.models.generate_content(
                    model=model_id,
                    # contents=f"Compare the ingredients and cooking times from the recipes at {url1} and {url2}",
                    contents=prompt,
                    config=GenerateContentConfig(
                        tools=tools,
                    )
                )
                # content = []

                # for each in response.candidates[0].content.parts:
                #     content.append(each.text)

                # response = client.models.generate_content(
                #     model="gemini-2.5-flash",
                #     contents=f"Translate the following English text to Japanese:\n\n{''.join(content)}"
                # )
                # print(response.text)

                all_text = response.candidates[0].content.parts[0].text
                match = re.search(r'【サマリテキスト】\n(.*)', all_text, re.DOTALL)
                if match:
                    summary_text = match.group(1).strip()
                else:
                    pass
                    # summary_text = "サマリテキストが見つかりませんでした。"

                # print(summary_text)


                st.success("✅ 比較分析が完了しました")

                # セッションステートに結果を保存（spinner内で保存のみ）
                st.session_state['analysis_result'] = all_text
                st.session_state['current_url1'] = url1
                st.session_state['current_url2'] = url2 if url2 else None

        except Exception as e:
            st.error(f"❌ エラーが発生しました: {str(e)}")

# 分析結果の表示（spinner外で常に表示）
if 'analysis_result' in st.session_state:
    st.markdown("---")
    st.subheader("📊 比較結果")

    # テキスト結果
    st.markdown(st.session_state['analysis_result'])

    # レーダーチャートの表示
    st.markdown("---")
    st.subheader("📈 分析結果可視化")

    try:
        # URL情報の取得
        current_url1 = st.session_state.get('current_url1', 'URL1')
        current_url2 = st.session_state.get('current_url2', None)

        # 分析結果から得点を抽出
        if current_url2:  # 比較分析の場合
            # URL1とURL2の分析結果を分離（改善版）
            full_text = st.session_state['analysis_result']
            
            # 【URL1分析結果】と【URL2分析結果】で分離
            url1_match = re.search(r'【URL1分析結果】(.*?)【URL2分析結果】', full_text, re.DOTALL)
            url2_match = re.search(r'【URL2分析結果】(.*?)(?:【比較総合評価】|【サマリテキスト】|$)', full_text, re.DOTALL)
            
            if url1_match and url2_match:
                url1_analysis = url1_match.group(1)
                url2_analysis = url2_match.group(1)
            else:
                # フォールバック: 従来の方法
                analysis_parts = full_text.split('URL2')
                url1_analysis = analysis_parts[0] if len(analysis_parts) > 1 else full_text
                url2_analysis = analysis_parts[1] if len(analysis_parts) > 1 else full_text

            # 店舗名・スタイリスト名を抽出
            url1_name = extract_site_name(current_url1, url1_analysis)
            url2_name = extract_site_name(current_url2, url2_analysis)

            scores_url1 = stabilize_scores(url1_analysis)
            scores_url2 = stabilize_scores(url2_analysis)

            # レーダーチャートと数値データを1行2列で配置
            chart_col1, chart_col2 = st.columns([1, 1])

            with chart_col1:
                st.markdown("**📈 レーダーチャート**")
                chart = create_radar_chart(scores_url1, scores_url2, "URL1", "URL2")
                st.plotly_chart(chart, use_container_width=True)

            with chart_col2:
                st.markdown("**📊 数値データ比較**")
                # 数値データ比較グラフ（一時的にコメントアウト）
                # numerical_data1 = extract_numerical_data(url1_analysis)
                # numerical_data2 = extract_numerical_data(url2_analysis)

                # if numerical_data1 and numerical_data2:
                #     bar_chart = create_comparison_bar_chart(numerical_data1, numerical_data2, f"URL1（{url1_name}）", f"URL2（{url2_name}）")
                #     if bar_chart:
                #         st.plotly_chart(bar_chart, use_container_width=True)

                #         # 数値データ詳細表示
                #         st.markdown("**数値詳細**")
                #         for key in numerical_data1.keys():
                #             if key in numerical_data2:
                #                 st.write(f"• {key}: {numerical_data1[key]:,} vs {numerical_data2[key]:,}")
                # else:
                #     st.info("数値データが十分に抽出できませんでした")

                st.info("数値データ比較グラフは一時的に無効化されています")

            # 得点表示
            st.markdown("---")
            st.subheader("📋 項目別得点")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**URL1（{url1_name}）得点**")
                for category, score in scores_url1.items():
                    st.write(f"• {category}: {score}/10")

            with col2:
                st.markdown(f"**URL2（{url2_name}）得点**")
                for category, score in scores_url2.items():
                    st.write(f"• {category}: {score}/10")

        else:  # 単一分析の場合
            # 店舗名・スタイリスト名を抽出
            url1_name = extract_site_name(current_url1, st.session_state['analysis_result'])

            scores_url1 = stabilize_scores(st.session_state['analysis_result'])

            # レーダーチャートと数値データを1行2列で配置
            chart_col1, chart_col2 = st.columns([1, 1])

            with chart_col1:
                st.markdown("**📈 レーダーチャート**")
                chart = create_radar_chart(scores_url1, None, "分析対象")
                st.plotly_chart(chart, use_container_width=True)

            with chart_col2:
                st.markdown("**📊 抽出された数値データ**")
                # 数値データ表示（一時的にコメントアウト）
                # numerical_data1 = extract_numerical_data(st.session_state['analysis_result'])
                # if numerical_data1:
                #     for key, value in numerical_data1.items():
                #         st.metric(label=key, value=f"{value:,}")
                # else:
                #     st.info("数値データが十分に抽出できませんでした")

                st.info("数値データ表示は一時的に無効化されています")

            # 得点表示
            st.markdown("---")
            st.subheader("📋 項目別得点")
            st.markdown(f"**分析対象（{url1_name}）得点**")
            for category, score in scores_url1.items():
                st.write(f"• {category}: {score}/10")

    except Exception as e:
        st.warning(f"チャート作成中にエラーが発生しました: {str(e)}")
        st.info("分析結果のテキスト表示は正常に機能しています。")

# 独立したダウンロードボタン（try-except文の外に配置）
if 'analysis_result' in st.session_state:
    st.markdown("---")
    st.subheader("💾 分析結果ダウンロード")

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.download_button(
            label="📄 分析結果をテキストファイルでダウンロード",
            data=st.session_state['analysis_result'],
            file_name="salon_comparison_analysis.txt",
            mime="text/plain",
            use_container_width=True,
            type="primary"
        )

    # CTAボタンとチャット機能を追加
    display_chat_cta_and_section()

# フッター
st.markdown("---")

# フッターにロゴを配置（中央揃え）
footer_col1, footer_col2, footer_col3 = st.columns([1, 2, 1])

with footer_col2:
    try:
        kuroco_logo = Image.open('kuroco-logo.png')
        # ロゴを中央揃えで表示
        st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
        st.image(kuroco_logo, width=200)
        st.markdown("</div>", unsafe_allow_html=True)
    except:
        st.markdown("<div style='text-align: center;'><strong>KUROCO</strong></div>", unsafe_allow_html=True)

st.markdown(
    "<div style='text-align: center; margin-top: 10px;'>Made with ❤️ using Streamlit and Gemini API</div>",
    unsafe_allow_html=True
)




