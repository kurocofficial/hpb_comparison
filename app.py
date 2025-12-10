"""
HPB分析ツール - メインアプリケーション
ホットペッパービューティーのサロンページを分析・比較するStreamlitアプリ
"""

import os
import sys
from pathlib import Path

import streamlit as st

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from modules.analyzer import HPBAnalyzer, ComparisonResult
from modules.chart import (
    create_radar_chart,
    create_comparison_bar_chart,
    create_total_score_gauge,
)
from modules.pdf_generator import generate_pdf_report

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

    try:
        with st.spinner("分析中... しばらくお待ちください（2-3分程度かかります）"):
            progress = st.progress(0)
            status = st.empty()

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

        st.rerun()

    except Exception as e:
        st.error(f"分析中にエラーが発生しました: {str(e)}")


def _build_context(result: ComparisonResult) -> str:
    """チャット用コンテキストを構築"""
    context = f"""
自店舗: {result.my_salon.name}
- PV獲得力: {result.my_salon.pv_score}/5
- CV転換力: {result.my_salon.cv_score}/5
- 価格競争力: {result.my_salon.price_score}/5
- 差別化: {result.my_salon.diff_score}/5
- 総合スコア: {result.my_salon.total_score}/5

強み: {', '.join(result.my_salon.strengths)}
弱み: {', '.join(result.my_salon.weaknesses)}

"""

    for i, comp in enumerate(result.competitors, 1):
        context += f"""
競合{i}: {comp.name}
- PV獲得力: {comp.pv_score}/5
- CV転換力: {comp.cv_score}/5
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
            st.rerun()

    # タブ
    tab1, tab2, tab3 = st.tabs(["📈 スコア", "💬 AI相談", "📥 レポート"])

    with tab1:
        render_score_tab(result)

    with tab2:
        render_chat_tab(result)

    with tab3:
        render_report_tab(result)


def render_score_tab(result: ComparisonResult):
    """スコアタブをレンダリング"""
    my_salon = result.my_salon

    # 総合スコア
    st.markdown('<div class="section-header">総合スコア</div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])
    with col1:
        gauge = create_total_score_gauge(my_salon.total_score, my_salon.name)
        st.plotly_chart(gauge, use_container_width=True)
    with col2:
        st.metric("PV獲得力", f"{'★' * my_salon.pv_score}{'☆' * (5 - my_salon.pv_score)}")
        st.metric("CV転換力", f"{'★' * my_salon.cv_score}{'☆' * (5 - my_salon.cv_score)}")
        st.metric("価格競争力", f"{'★' * my_salon.price_score}{'☆' * (5 - my_salon.price_score)}")
        st.metric("差別化", f"{'★' * my_salon.diff_score}{'☆' * (5 - my_salon.diff_score)}")

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
    st.markdown('<div class="section-header">PDFレポート出力</div>', unsafe_allow_html=True)

    st.markdown("分析結果をPDFレポートとしてダウンロードできます")

    if st.button("📥 PDFを生成", type="primary", use_container_width=True):
        with st.spinner("PDF生成中..."):
            try:
                # チャート画像を生成
                my_scores = {
                    'name': result.my_salon.name,
                    'pv': result.my_salon.pv_score,
                    'cv': result.my_salon.cv_score,
                    'price': result.my_salon.price_score,
                    'diff': result.my_salon.diff_score,
                    'total': result.my_salon.total_score
                }

                comp_scores = [{
                    'name': c.name,
                    'pv': c.pv_score,
                    'cv': c.cv_score,
                    'price': c.price_score,
                    'diff': c.diff_score,
                    'total': c.total_score
                } for c in result.competitors]

                radar = create_radar_chart(my_scores, comp_scores)
                bar = create_comparison_bar_chart(my_scores, comp_scores)

                radar_img = radar.to_image(format="png", width=800, height=500)
                bar_img = bar.to_image(format="png", width=800, height=450)

                # サロンデータを辞書に変換
                my_data = {
                    'name': result.my_salon.name,
                    'pv': result.my_salon.pv_score,
                    'cv': result.my_salon.cv_score,
                    'price': result.my_salon.price_score,
                    'diff': result.my_salon.diff_score,
                    'total': result.my_salon.total_score,
                    'strengths': result.my_salon.strengths,
                    'weaknesses': result.my_salon.weaknesses,
                }

                comp_data = [{
                    'name': c.name,
                    'pv': c.pv_score,
                    'cv': c.cv_score,
                    'price': c.price_score,
                    'diff': c.diff_score,
                    'total': c.total_score,
                } for c in result.competitors]

                # PDF生成
                pdf_bytes = generate_pdf_report(
                    my_data,
                    comp_data,
                    result.comparison_summary,
                    result.recommendations,
                    radar_img,
                    bar_img
                )

                st.download_button(
                    label="📄 PDFをダウンロード",
                    data=pdf_bytes,
                    file_name="hpb_analysis_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )

                st.success("PDF生成完了！上のボタンからダウンロードできます")

            except Exception as e:
                st.error(f"PDF生成エラー: {str(e)}")

    # 比較サマリー表示
    st.markdown("---")
    st.markdown("**比較分析サマリー**")
    st.markdown(result.comparison_summary)


def main():
    """メイン関数"""
    init_session_state()

    if st.session_state.analysis_result is None:
        render_url_input_page()
    else:
        render_result_page()


if __name__ == "__main__":
    main()
