"""
HPB分析ツール - メインアプリケーション
ホットペッパービューティーのサロンページを分析・比較するStreamlitアプリ
"""

import os
import sys
import csv
import random
from pathlib import Path

import streamlit as st

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from modules.analyzer import HPBAnalyzer, ComparisonResult
from modules.chart import (
    create_radar_chart,
    create_comparison_bar_chart,
    create_total_score_gauge,
    create_gender_pie_chart,
    create_age_bar_chart,
)
from modules.pdf_generator import generate_pdf_report

# YouTube動画の設定
YOUTUBE_CSV_PATH = Path(__file__).parent / "videos" / "美容サロン経営カレッジ.csv"


def load_youtube_videos() -> list[dict]:
    """CSVからYouTube動画リストを読み込む"""
    videos = []
    try:
        with open(YOUTUBE_CSV_PATH, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('リンク'):
                    videos.append({
                        'title': row.get('タイトル', ''),
                        'url': row['リンク']
                    })
    except Exception:
        pass
    return videos


def extract_youtube_id(url: str) -> str | None:
    """YouTubeのURLから動画IDを抽出"""
    import re
    # youtu.be/VIDEO_ID 形式
    match = re.search(r'youtu\.be/([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    # youtube.com/watch?v=VIDEO_ID 形式
    match = re.search(r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)', url)
    if match:
        return match.group(1)
    return None


# ページ設定
st.set_page_config(
    page_title="HPB分析ツール",
    page_icon="💇",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# モバイル対応CSS
st.markdown("""
<style>
    /* モバイル最適化 */
    .stApp {
        max-width: 100%;
    }

    /* 入力フィールドを大きく */
    .stTextInput > div > div > input {
        font-size: 16px !important;
        padding: 12px !important;
    }

    /* ボタンを大きく・タップしやすく */
    .stButton > button {
        width: 100%;
        min-height: 48px;
        font-size: 16px;
        font-weight: bold;
        border-radius: 8px;
    }

    /* プライマリボタン */
    .stButton > button[kind="primary"] {
        background-color: #FF6B6B;
        color: white;
    }

    /* タブを大きく */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        font-size: 14px;
        padding: 12px 16px;
    }

    /* カード風スタイル */
    .score-card {
        background: white;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 16px;
    }

    /* スコア表示 */
    .score-value {
        font-size: 32px;
        font-weight: bold;
        color: #FF6B6B;
    }

    /* セクションヘッダー */
    .section-header {
        font-size: 18px;
        font-weight: bold;
        color: #333;
        margin-top: 24px;
        margin-bottom: 12px;
        padding-bottom: 8px;
        border-bottom: 2px solid #FF6B6B;
    }

    /* 改善提案カード */
    .improvement-card {
        background: #FFF5F5;
        border-left: 4px solid #FF6B6B;
        padding: 12px;
        margin-bottom: 8px;
        border-radius: 0 8px 8px 0;
    }

    /* チャット入力 */
    .stChatInput {
        font-size: 16px !important;
    }

    /* ダウンロードボタン共通 */
    .stDownloadButton > button {
        width: 100%;
        min-height: 48px;
        font-size: 16px;
        font-weight: bold;
        border-radius: 8px;
    }

    /* PDFダウンロードボタン（プライマリ） */
    .stDownloadButton > button[kind="primary"] {
        background-color: #FF6B6B !important;
        color: white !important;
        border: none !important;
    }

    /* テキストダウンロードボタン（セカンダリ：グレー背景白文字） */
    .stDownloadButton > button[kind="secondary"] {
        background-color: #6c757d !important;
        color: white !important;
        border: none !important;
    }

    .stDownloadButton > button[kind="secondary"]:hover {
        background-color: #5a6268 !important;
    }

    /* スマホ横スクロール防止 */
    @media (max-width: 768px) {
        .main .block-container {
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .stPlotlyChart {
            overflow-x: auto;
        }
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """セッション状態を初期化"""
    if 'analysis_result' not in st.session_state:
        st.session_state.analysis_result = None
    if 'analysis_context' not in st.session_state:
        st.session_state.analysis_context = ""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'last_video' not in st.session_state:
        st.session_state.last_video = None


def get_api_key() -> str:
    """APIキーを取得"""
    # Streamlit Cloudのsecrets
    if hasattr(st, 'secrets') and 'GEMINI_API_KEY' in st.secrets:
        return st.secrets['GEMINI_API_KEY']
    # 環境変数
    return os.getenv('GEMINI_API_KEY', '')


def render_url_input_page():
    """URL入力ページをレンダリング"""
    st.markdown("### 💇 HPB分析ツール")
    st.markdown("ホットペッパービューティーのサロンページを分析・比較します")

    st.markdown("---")

    # 自店舗URL
    st.markdown("**📍 自店舗のURL**")
    my_url = st.text_input(
        "自店舗URL",
        placeholder="https://beauty.hotpepper.jp/slnH...",
        label_visibility="collapsed",
        key="my_salon_url"
    )

    st.markdown("")

    # 競合URL
    st.markdown("**🏪 競合店舗のURL（任意）**")

    competitor1 = st.text_input(
        "競合1",
        placeholder="競合店舗1のURL",
        label_visibility="collapsed",
        key="competitor1_url"
    )

    competitor2 = st.text_input(
        "競合2",
        placeholder="競合店舗2のURL",
        label_visibility="collapsed",
        key="competitor2_url"
    )

    st.markdown("---")

    # 分析ボタン
    analyze_clicked = st.button(
        "🔍 分析を開始",
        type="primary",
        use_container_width=True,
        disabled=not my_url
    )

    if analyze_clicked and my_url:
        run_analysis(my_url, [competitor1, competitor2])


def run_analysis(my_url: str, competitor_urls: list[str]):
    """分析を実行"""
    api_key = get_api_key()
    if not api_key:
        st.error("APIキーが設定されていません。環境変数またはsecretsにGEMINI_API_KEYを設定してください。")
        return

    # 有効な競合URLのみ抽出
    valid_competitors = [url for url in competitor_urls if url and url.strip()]

    # YouTube動画を読み込み
    videos = load_youtube_videos()
    selected_video = None  # 選択した動画を保持

    try:
        # 分析中メッセージとプログレスバー
        st.info("🔍 分析中... しばらくお待ちください（2-3分程度かかります）")
        progress = st.progress(0)
        status = st.empty()

        # 待機中にYouTube動画を表示
        if videos:
            st.markdown("---")
            st.markdown("**📺 お待ちの間、サロン経営のヒントをどうぞ**")

            # HPB関連動画を優先、なければランダム選択
            hpb_videos = [v for v in videos if 'ホットペッパー' in v['title'] or 'HPB' in v['title'].upper()]
            if hpb_videos:
                selected_video = random.choice(hpb_videos)
            else:
                selected_video = random.choice(videos)
            video_id = extract_youtube_id(selected_video['url'])

            if video_id:
                st.markdown(f"**{selected_video['title']}**")
                # YouTube埋め込みプレーヤー（自動再生・ミュート開始）
                youtube_embed = f'''
                <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; border-radius: 12px;">
                    <iframe
                        src="https://www.youtube.com/embed/{video_id}?autoplay=1&mute=1&rel=0"
                        style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; border-radius: 12px;"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowfullscreen>
                    </iframe>
                </div>
                <p style="font-size: 12px; color: #666; margin-top: 8px;">※ 音声はミュート状態で開始します。動画内のスピーカーボタンで音声ONにできます</p>
                '''
                st.markdown(youtube_embed, unsafe_allow_html=True)
                st.markdown("")

        status.text("🔄 APIに接続中...")
        progress.progress(10)

        analyzer = HPBAnalyzer(api_key)

        status.text("📊 自店舗を分析中...")
        progress.progress(30)

        result = analyzer.compare_salons(my_url, valid_competitors)

        progress.progress(100)
        status.text("✅ 分析完了!")

        # 結果を保存
        st.session_state.analysis_result = result
        st.session_state.analysis_context = _build_context(result)
        st.session_state.last_video = selected_video  # 動画情報も保存

        st.rerun()

    except Exception as e:
        st.error(f"分析中にエラーが発生しました: {str(e)}")


def _build_context(result: ComparisonResult) -> str:
    """チャット用コンテキストを構築"""
    context = f"""
自店舗: {result.my_salon.name}
- 集客力: {result.my_salon.pv_score}/5
- 予約力: {result.my_salon.cv_score}/5
- 価格競争力: {result.my_salon.price_score}/5
- 差別化: {result.my_salon.diff_score}/5
- 総合スコア: {result.my_salon.total_score}/5

強み: {', '.join(result.my_salon.strengths)}
弱み: {', '.join(result.my_salon.weaknesses)}

"""

    for i, comp in enumerate(result.competitors, 1):
        context += f"""
競合{i}: {comp.name}
- 集客力: {comp.pv_score}/5
- 予約力: {comp.cv_score}/5
- 価格競争力: {comp.price_score}/5
- 差別化: {comp.diff_score}/5
- 総合スコア: {comp.total_score}/5

"""

    context += f"\n比較分析:\n{result.comparison_summary}"
    return context


def render_result_page():
    """分析結果ページをレンダリング"""
    result: ComparisonResult = st.session_state.analysis_result

    # ヘッダー
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### 📊 分析結果")
    with col2:
        if st.button("🔄 新規分析"):
            st.session_state.analysis_result = None
            st.session_state.chat_history = []
            st.session_state.last_video = None
            st.rerun()

    # タブ
    tab1, tab2, tab3, tab4 = st.tabs(["📈 スコア", "💬 AI相談", "📄 レポート", "📺 YouTube"])

    with tab1:
        render_score_tab(result)

    with tab2:
        render_chat_tab(result)

    with tab3:
        render_report_tab(result)

    with tab4:
        render_youtube_tab()


def render_score_tab(result: ComparisonResult):
    """スコアタブをレンダリング"""
    my_salon = result.my_salon

    # チェック項目の定義（厳しめ基準）
    SCORING_CRITERIA = {
        "pv": {
            "name": "集客力",
            "items": {
                "1-1": "キャッチコピーが独自性あり（○○専門など）",
                "1-2": "メイン写真がプロ撮影レベル",
                "1-3": "ギャラリー写真30枚以上",
                "1-4": "口コミ3,000件以上",
                "1-5": "口コミ評価4.9以上",
            }
        },
        "cv": {
            "name": "予約力",
            "items": {
                "2-1": "クーポン10種類以上・割引率40%以上",
                "2-2": "強い緊急性訴求（本日空き・残り○枠等）",
                "2-3": "全メニューに詳細説明あり",
                "2-4": "ビフォーアフター写真10組以上",
                "2-5": "口コミ返信率80%以上・丁寧な対応",
            }
        },
        "price": {
            "name": "価格競争力",
            "items": {
                "3-1": "競合より20%以上安い",
                "3-2": "初回割引50%以上または高額特典",
                "3-3": "セットメニュー3つ以上・30%以上お得",
                "3-4": "追加料金・オプション料金の明記（価格透明性）",
                "3-5": "施術時間・内容が競合より充実",
            }
        },
        "diff": {
            "name": "差別化",
            "items": {
                "4-1": "エリアで唯一/希少な専門性",
                "4-2": "ターゲット層が具体的で最適化",
                "4-3": "資格・受賞歴・有名店出身の権威性",
                "4-4": "独自メニュー・オリジナル技術・特別設備",
                "4-5": "メディア掲載・SNS1万人以上の外部評価",
            }
        }
    }

    # 総合スコア
    st.markdown('<div class="section-header">総合スコア</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        gauge = create_total_score_gauge(my_salon.total_score, my_salon.name)
        st.plotly_chart(gauge, use_container_width=True)
    with col2:
        st.metric("集客力", f"{'★' * my_salon.pv_score}{'☆' * (5 - my_salon.pv_score)}")
        st.metric("予約力", f"{'★' * my_salon.cv_score}{'☆' * (5 - my_salon.cv_score)}")
        st.metric("価格競争力", f"{'★' * my_salon.price_score}{'☆' * (5 - my_salon.price_score)}")
        st.metric("差別化", f"{'★' * my_salon.diff_score}{'☆' * (5 - my_salon.diff_score)}")

    # 採点詳細
    st.markdown('<div class="section-header">採点詳細</div>', unsafe_allow_html=True)

    score_details = {
        "pv": (my_salon.pv_score, my_salon.pv_details or []),
        "cv": (my_salon.cv_score, my_salon.cv_details or []),
        "price": (my_salon.price_score, my_salon.price_details or []),
        "diff": (my_salon.diff_score, my_salon.diff_details or []),
    }

    for key, (score, details) in score_details.items():
        criteria = SCORING_CRITERIA[key]
        with st.expander(f"{criteria['name']}: {score}/5点"):
            for item_id, item_label in criteria["items"].items():
                if item_id in details:
                    st.markdown(f"✅ {item_label}")
                else:
                    st.markdown(f"❌ {item_label}")

    # 予約比率（男女比・年齢層）
    if my_salon.gender_ratio or my_salon.age_ratio:
        st.markdown('<div class="section-header">予約比率</div>', unsafe_allow_html=True)
        st.markdown("*直近3カ月のネット予約データに基づく*")

        col1, col2 = st.columns(2)

        with col1:
            if my_salon.gender_ratio:
                gender_chart = create_gender_pie_chart(my_salon.gender_ratio)
                st.plotly_chart(gender_chart, use_container_width=True)
            else:
                st.info("性別比率データなし")

        with col2:
            if my_salon.age_ratio:
                age_chart = create_age_bar_chart(my_salon.age_ratio)
                st.plotly_chart(age_chart, use_container_width=True)
            else:
                st.info("年代比率データなし")

    # 比較チャート
    if result.competitors:
        st.markdown('<div class="section-header">競合比較</div>', unsafe_allow_html=True)

        my_scores = {
            'name': my_salon.name,
            'pv': my_salon.pv_score,
            'cv': my_salon.cv_score,
            'price': my_salon.price_score,
            'diff': my_salon.diff_score,
            'total': my_salon.total_score
        }

        comp_scores = [{
            'name': c.name,
            'pv': c.pv_score,
            'cv': c.cv_score,
            'price': c.price_score,
            'diff': c.diff_score,
            'total': c.total_score
        } for c in result.competitors]

        # レーダーチャート
        radar = create_radar_chart(my_scores, comp_scores)
        st.plotly_chart(radar, use_container_width=True)

        # バーチャート
        bar = create_comparison_bar_chart(my_scores, comp_scores)
        st.plotly_chart(bar, use_container_width=True)

    # 強み・弱み
    st.markdown('<div class="section-header">分析詳細</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**💪 強み**")
        for s in my_salon.strengths[:3]:
            st.success(s)

    with col2:
        st.markdown("**⚠️ 改善点**")
        for w in my_salon.weaknesses[:3]:
            st.warning(w)

    # 改善提案
    st.markdown('<div class="section-header">改善提案</div>', unsafe_allow_html=True)
    for i, imp in enumerate(my_salon.improvements[:5], 1):
        st.markdown(f"""
        <div class="improvement-card">
            <strong>{i}.</strong> {imp}
        </div>
        """, unsafe_allow_html=True)


def render_chat_tab(result: ComparisonResult):
    """AIチャットタブをレンダリング"""
    st.markdown('<div class="section-header">AI相談</div>', unsafe_allow_html=True)
    st.markdown("分析結果について質問できます")

    # チャット履歴表示
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    # 入力
    if question := st.chat_input("質問を入力してください"):
        # ユーザーメッセージを追加
        st.session_state.chat_history.append({
            "role": "user",
            "content": question
        })

        with st.chat_message("user"):
            st.write(question)

        # AI応答
        with st.chat_message("assistant"):
            with st.spinner("回答を生成中..."):
                try:
                    api_key = get_api_key()
                    analyzer = HPBAnalyzer(api_key)
                    response = analyzer.chat(
                        question,
                        st.session_state.analysis_context
                    )
                    st.write(response)

                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": response
                    })
                except Exception as e:
                    st.error(f"エラー: {str(e)}")


def render_report_tab(result: ComparisonResult):
    """レポート出力タブをレンダリング"""
    st.markdown('<div class="section-header">レポート出力</div>', unsafe_allow_html=True)

    # PDFレポートセクション
    st.markdown("**📑 PDFレポート**")
    st.markdown("グラフ付きの見やすいPDF形式でダウンロードできます")

    my = result.my_salon
    my_salon_data = {
        'name': my.name,
        'url': my.url,
        'pv': my.pv_score,
        'cv': my.cv_score,
        'price': my.price_score,
        'diff': my.diff_score,
        'total': my.total_score,
        'strengths': my.strengths,
        'weaknesses': my.weaknesses,
        'improvements': my.improvements,
        'pv_details': my.pv_details or [],
        'cv_details': my.cv_details or [],
        'price_details': my.price_details or [],
        'diff_details': my.diff_details or [],
    }

    competitor_data = [{
        'name': c.name,
        'pv': c.pv_score,
        'cv': c.cv_score,
        'price': c.price_score,
        'diff': c.diff_score,
        'total': c.total_score,
    } for c in result.competitors]

    try:
        # グラフを画像化
        my_scores = {
            'name': my.name,
            'pv': my.pv_score,
            'cv': my.cv_score,
            'price': my.price_score,
            'diff': my.diff_score,
            'total': my.total_score
        }
        comp_scores = competitor_data

        radar_image = None
        bar_image = None

        try:
            radar_fig = create_radar_chart(my_scores, comp_scores)
            radar_image = radar_fig.to_image(format="png", width=800, height=500)
        except Exception:
            pass

        try:
            bar_fig = create_comparison_bar_chart(my_scores, comp_scores)
            bar_image = bar_fig.to_image(format="png", width=800, height=400)
        except Exception:
            pass

        pdf_bytes = generate_pdf_report(
            my_salon_data=my_salon_data,
            competitor_data=competitor_data,
            comparison_summary=result.comparison_summary,
            recommendations=my.improvements[:5],
            radar_chart_image=radar_image,
            bar_chart_image=bar_image,
            gender_ratio=my.gender_ratio,
            age_ratio=my.age_ratio,
        )

        st.download_button(
            label="PDFをダウンロード",
            data=pdf_bytes,
            file_name="hpb_analysis_report.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
            key="pdf_download"
        )
    except Exception as e:
        st.warning(f"PDF生成に失敗しました: {str(e)}")

    st.markdown("")
    st.markdown("---")
    st.markdown("")

    # テキストレポートセクション
    st.markdown("**📄 テキストレポート**")
    st.markdown("シンプルなテキスト形式でダウンロードできます")

    # テキストレポート生成
    def generate_text_report() -> str:
        my = result.my_salon
        lines = []
        lines.append("=" * 50)
        lines.append("HPB分析レポート")
        lines.append("=" * 50)
        lines.append("")
        lines.append(f"■ サロン名: {my.name}")
        lines.append(f"■ URL: {my.url}")
        lines.append("")
        lines.append("-" * 50)
        lines.append("【スコア】")
        lines.append("-" * 50)
        lines.append(f"  集客力:     {'★' * my.pv_score}{'☆' * (5 - my.pv_score)} ({my.pv_score}/5)")
        lines.append(f"  予約力:     {'★' * my.cv_score}{'☆' * (5 - my.cv_score)} ({my.cv_score}/5)")
        lines.append(f"  価格競争力: {'★' * my.price_score}{'☆' * (5 - my.price_score)} ({my.price_score}/5)")
        lines.append(f"  差別化:     {'★' * my.diff_score}{'☆' * (5 - my.diff_score)} ({my.diff_score}/5)")
        lines.append(f"  ─────────────────────")
        lines.append(f"  総合スコア: {my.total_score}/5")
        lines.append("")

        # 採点詳細
        lines.append("-" * 50)
        lines.append("【採点詳細】")
        lines.append("-" * 50)

        criteria = {
            "集客力": {
                "details": my.pv_details or [],
                "items": {
                    "1-1": "キャッチコピーが独自性あり",
                    "1-2": "メイン写真がプロ撮影レベル",
                    "1-3": "ギャラリー写真30枚以上",
                    "1-4": "口コミ3,000件以上",
                    "1-5": "口コミ評価4.9以上",
                }
            },
            "予約力": {
                "details": my.cv_details or [],
                "items": {
                    "2-1": "クーポン10種類以上・割引率40%以上",
                    "2-2": "強い緊急性訴求",
                    "2-3": "全メニューに詳細説明",
                    "2-4": "ビフォーアフター写真10組以上",
                    "2-5": "口コミ返信率80%以上",
                }
            },
            "価格競争力": {
                "details": my.price_details or [],
                "items": {
                    "3-1": "競合より20%以上安い",
                    "3-2": "初回割引50%以上",
                    "3-3": "セットメニュー3つ以上",
                    "3-4": "追加料金・オプション料金の明記",
                    "3-5": "施術時間・内容が充実",
                }
            },
            "差別化": {
                "details": my.diff_details or [],
                "items": {
                    "4-1": "エリアで唯一/希少な専門性",
                    "4-2": "ターゲット層が具体的",
                    "4-3": "資格・受賞歴の権威性",
                    "4-4": "独自メニュー・技術",
                    "4-5": "メディア掲載・SNS1万人以上",
                }
            },
        }

        for cat_name, cat_data in criteria.items():
            lines.append(f"\n  《{cat_name}》")
            for item_id, item_label in cat_data["items"].items():
                mark = "✓" if item_id in cat_data["details"] else "✗"
                lines.append(f"    [{mark}] {item_label}")

        # 予約比率
        if my.gender_ratio or my.age_ratio:
            lines.append("")
            lines.append("-" * 50)
            lines.append("【予約比率】")
            lines.append("-" * 50)
            lines.append("  ※直近3カ月のネット予約データに基づく")

            if my.gender_ratio:
                lines.append("")
                lines.append("  《性別比率》")
                lines.append(f"    女性: {my.gender_ratio.get('female', 0)}%")
                lines.append(f"    男性: {my.gender_ratio.get('male', 0)}%")
                lines.append(f"    その他: {my.gender_ratio.get('other', 0)}%")

            if my.age_ratio:
                lines.append("")
                lines.append("  《年代比率（女性）》")
                lines.append(f"    〜10代: {my.age_ratio.get('under_10s', 0)}%")
                lines.append(f"    20代: {my.age_ratio.get('20s', 0)}%")
                lines.append(f"    30代: {my.age_ratio.get('30s', 0)}%")
                lines.append(f"    40代: {my.age_ratio.get('40s', 0)}%")
                lines.append(f"    50代〜: {my.age_ratio.get('50s_plus', 0)}%")

        lines.append("")
        lines.append("-" * 50)
        lines.append("【強み】")
        lines.append("-" * 50)
        for i, s in enumerate(my.strengths[:5], 1):
            lines.append(f"  {i}. {s}")

        lines.append("")
        lines.append("-" * 50)
        lines.append("【改善点】")
        lines.append("-" * 50)
        for i, w in enumerate(my.weaknesses[:5], 1):
            lines.append(f"  {i}. {w}")

        lines.append("")
        lines.append("-" * 50)
        lines.append("【改善提案】")
        lines.append("-" * 50)
        for i, imp in enumerate(my.improvements[:5], 1):
            lines.append(f"  {i}. {imp}")

        # 競合比較
        if result.competitors:
            lines.append("")
            lines.append("=" * 50)
            lines.append("【競合比較】")
            lines.append("=" * 50)
            for i, comp in enumerate(result.competitors, 1):
                lines.append(f"\n  ▼ 競合{i}: {comp.name}")
                lines.append(f"    集客力: {comp.pv_score}/5 | 予約力: {comp.cv_score}/5")
                lines.append(f"    価格競争力: {comp.price_score}/5 | 差別化: {comp.diff_score}/5")
                lines.append(f"    総合: {comp.total_score}/5")

        lines.append("")
        lines.append("-" * 50)
        lines.append("【比較分析サマリー】")
        lines.append("-" * 50)
        lines.append(result.comparison_summary)

        lines.append("")
        lines.append("=" * 50)
        lines.append("Generated by HPB分析ツール")
        lines.append("=" * 50)

        return "\n".join(lines)

    report_text = generate_text_report()

    st.download_button(
        label="テキストをダウンロード",
        data=report_text.encode('utf-8'),
        file_name="hpb_analysis_report.txt",
        mime="text/plain",
        use_container_width=True,
        key="text_download",
        type="secondary"
    )

    # 比較サマリー表示
    st.markdown("---")
    st.markdown("**比較分析サマリー**")
    st.markdown(result.comparison_summary)


def render_youtube_tab():
    """YouTubeタブをレンダリング"""
    st.markdown('<div class="section-header">美容サロン経営カレッジ</div>', unsafe_allow_html=True)

    # チャンネル情報
    st.markdown("""
    **サロン経営に役立つ動画チャンネル**

    ホットペッパービューティーの活用法や集客のコツなど、
    サロン経営に役立つ情報を発信しています。
    """)

    # 分析中に視聴していた動画をハイライト
    if st.session_state.last_video:
        st.markdown("---")
        st.markdown("**▶ 先ほど視聴していた動画**")
        video = st.session_state.last_video
        video_id = extract_youtube_id(video['url'])
        if video_id:
            st.markdown(f"**{video['title']}**")
            youtube_embed = f'''
            <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; border-radius: 12px;">
                <iframe
                    src="https://www.youtube.com/embed/{video_id}?rel=0"
                    style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; border-radius: 12px;"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowfullscreen>
                </iframe>
            </div>
            '''
            st.markdown(youtube_embed, unsafe_allow_html=True)

    # 全動画リスト
    st.markdown("---")
    st.markdown("**📋 動画一覧**")

    videos = load_youtube_videos()
    if videos:
        for i, video in enumerate(videos, 1):
            with st.expander(f"{i}. {video['title']}"):
                video_id = extract_youtube_id(video['url'])
                if video_id:
                    youtube_embed = f'''
                    <div style="position: relative; padding-bottom: 56.25%; height: 0; overflow: hidden; max-width: 100%; border-radius: 12px;">
                        <iframe
                            src="https://www.youtube.com/embed/{video_id}?rel=0"
                            style="position: absolute; top: 0; left: 0; width: 100%; height: 100%; border: none; border-radius: 12px;"
                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                            allowfullscreen>
                        </iframe>
                    </div>
                    '''
                    st.markdown(youtube_embed, unsafe_allow_html=True)
                st.markdown(f"[YouTubeで見る]({video['url']})")
    else:
        st.info("動画が見つかりませんでした")

    # チャンネルリンク
    st.markdown("---")
    st.markdown("**🔗 チャンネル登録はこちら**")
    st.markdown("[美容サロン経営カレッジ - YouTubeチャンネル](https://www.youtube.com/@biyou-salon)")


def main():
    """メイン関数"""
    init_session_state()

    if st.session_state.analysis_result is None:
        render_url_input_page()
    else:
        render_result_page()


if __name__ == "__main__":
    main()
