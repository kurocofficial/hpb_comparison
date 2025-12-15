"""
PDF生成モジュール
ReportLabを使用して日本語対応PDFレポートを生成
"""

import io
import os
import urllib.request
import zipfile
import tempfile
from datetime import datetime
from typing import Optional
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak,
)


# フォントキャッシュディレクトリ
FONT_CACHE_DIR = Path(tempfile.gettempdir()) / "hpb_fonts"
NOTO_SANS_JP_URL = "https://github.com/google/fonts/raw/main/ofl/notosansjp/NotoSansJP-Regular.ttf"


def download_noto_sans_jp() -> Optional[str]:
    """Noto Sans JPフォントをダウンロード"""
    try:
        FONT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        font_path = FONT_CACHE_DIR / "NotoSansJP-Regular.ttf"

        if font_path.exists():
            return str(font_path)

        # フォントをダウンロード
        urllib.request.urlretrieve(NOTO_SANS_JP_URL, font_path)
        return str(font_path)
    except Exception:
        return None


def register_japanese_font():
    """日本語フォントを登録"""
    # まずローカルのフォントを確認
    font_paths = [
        # Windows
        "C:/Windows/Fonts/msgothic.ttc",
        "C:/Windows/Fonts/meiryo.ttc",
        "C:/Windows/Fonts/YuGothM.ttc",
        # プロジェクト内
        os.path.join(os.path.dirname(__file__), "..", "assets", "fonts", "NotoSansJP-Regular.ttf"),
        # Linux (Streamlit Cloud - fonts-noto-cjk package)
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJKjp-Regular.otf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf",
        # Mac
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]

    for font_path in font_paths:
        if os.path.exists(font_path):
            try:
                pdfmetrics.registerFont(TTFont("JapaneseFont", font_path))
                return "JapaneseFont"
            except Exception:
                continue

    # Linuxでfindコマンドを使ってNotoフォントを探す
    try:
        import subprocess
        result = subprocess.run(
            ["find", "/usr/share/fonts", "-name", "*NotoSans*CJK*.otf", "-o", "-name", "*NotoSans*CJK*.ttf"],
            capture_output=True, text=True, timeout=5
        )
        if result.stdout.strip():
            font_path = result.stdout.strip().split('\n')[0]
            pdfmetrics.registerFont(TTFont("JapaneseFont", font_path))
            return "JapaneseFont"
    except Exception:
        pass

    # ローカルにフォントがない場合はダウンロード
    downloaded_font = download_noto_sans_jp()
    if downloaded_font:
        try:
            pdfmetrics.registerFont(TTFont("JapaneseFont", downloaded_font))
            return "JapaneseFont"
        except Exception:
            pass

    # フォントが見つからない場合はデフォルトを使用（文字化けする可能性あり）
    return "Helvetica"


def generate_pdf_report(
    my_salon_data: dict,
    competitor_data: list[dict],
    comparison_summary: str,
    recommendations: list[str],
    radar_chart_image: Optional[bytes] = None,
    bar_chart_image: Optional[bytes] = None,
) -> bytes:
    """
    PDFレポートを生成

    Args:
        my_salon_data: 自店舗データ
        competitor_data: 競合店舗データリスト
        comparison_summary: 比較サマリー
        recommendations: 改善提案リスト
        radar_chart_image: レーダーチャート画像（PNG bytes）
        bar_chart_image: バーチャート画像（PNG bytes）

    Returns:
        bytes: PDFデータ
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=15*mm,
        leftMargin=15*mm,
        topMargin=15*mm,
        bottomMargin=15*mm
    )

    # 日本語フォント登録
    font_name = register_japanese_font()

    # スタイル設定
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='JapaneseTitle',
        fontName=font_name,
        fontSize=20,
        leading=24,
        alignment=1,  # CENTER
        spaceAfter=10*mm
    ))
    styles.add(ParagraphStyle(
        name='JapaneseHeading',
        fontName=font_name,
        fontSize=14,
        leading=18,
        spaceBefore=8*mm,
        spaceAfter=4*mm,
        textColor=colors.HexColor('#FF6B6B')
    ))
    styles.add(ParagraphStyle(
        name='JapaneseBody',
        fontName=font_name,
        fontSize=10,
        leading=16,
        spaceAfter=3*mm
    ))
    styles.add(ParagraphStyle(
        name='JapaneseSmall',
        fontName=font_name,
        fontSize=8,
        leading=12
    ))

    # コンテンツ作成
    story = []

    # タイトル
    story.append(Paragraph(
        "ホットペッパービューティー分析レポート",
        styles['JapaneseTitle']
    ))

    # 作成日時
    story.append(Paragraph(
        f"作成日: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}",
        styles['JapaneseSmall']
    ))
    story.append(Spacer(1, 5*mm))

    # 自店舗情報
    story.append(Paragraph("自店舗情報", styles['JapaneseHeading']))
    story.append(Paragraph(
        f"店舗名: {my_salon_data.get('name', '不明')}",
        styles['JapaneseBody']
    ))

    # スコアテーブル（星をスコア数字に変更して文字化け回避）
    score_data = [
        ['評価項目', '自店舗'] + [f"競合{i+1}" for i in range(len(competitor_data))],
        ['集客力', f"{my_salon_data.get('pv', 0)}/5"] +
        [f"{c.get('pv', 0)}/5" for c in competitor_data],
        ['予約力', f"{my_salon_data.get('cv', 0)}/5"] +
        [f"{c.get('cv', 0)}/5" for c in competitor_data],
        ['価格競争力', f"{my_salon_data.get('price', 0)}/5"] +
        [f"{c.get('price', 0)}/5" for c in competitor_data],
        ['差別化', f"{my_salon_data.get('diff', 0)}/5"] +
        [f"{c.get('diff', 0)}/5" for c in competitor_data],
        ['総合スコア', f"{my_salon_data.get('total', 0):.1f}/5"] +
        [f"{c.get('total', 0):.1f}/5" for c in competitor_data],
    ]

    col_widths = [80] + [90] * (1 + len(competitor_data))
    score_table = Table(score_data, colWidths=col_widths)
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B6B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 8*mm))

    # チャート画像
    if radar_chart_image:
        story.append(Paragraph("評価チャート", styles['JapaneseHeading']))
        img = Image(io.BytesIO(radar_chart_image), width=160*mm, height=100*mm)
        story.append(img)
        story.append(Spacer(1, 5*mm))

    if bar_chart_image:
        img = Image(io.BytesIO(bar_chart_image), width=160*mm, height=90*mm)
        story.append(img)
        story.append(Spacer(1, 8*mm))

    # 比較サマリー
    story.append(Paragraph("比較分析", styles['JapaneseHeading']))

    # サマリーを段落ごとに分割
    summary_lines = comparison_summary.split('\n')
    for line in summary_lines:
        if line.strip():
            # マークダウンの見出しを処理
            if line.startswith('###'):
                story.append(Paragraph(
                    line.replace('###', '').strip(),
                    styles['JapaneseHeading']
                ))
            elif line.startswith('#'):
                continue  # 大見出しはスキップ
            else:
                # 特殊文字を置換して文字化け回避
                clean_line = line.replace('★', '[*]').replace('☆', '[ ]')
                story.append(Paragraph(clean_line, styles['JapaneseBody']))

    # 改善提案
    story.append(PageBreak())
    story.append(Paragraph("改善提案", styles['JapaneseHeading']))

    for i, rec in enumerate(recommendations, 1):
        story.append(Paragraph(
            f"{i}. {rec}",
            styles['JapaneseBody']
        ))

    # 自店舗の強み・弱み
    if my_salon_data.get('strengths'):
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph("自店舗の強み", styles['JapaneseHeading']))
        for s in my_salon_data['strengths']:
            story.append(Paragraph(f"- {s}", styles['JapaneseBody']))

    if my_salon_data.get('weaknesses'):
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph("改善が必要な点", styles['JapaneseHeading']))
        for w in my_salon_data['weaknesses']:
            story.append(Paragraph(f"- {w}", styles['JapaneseBody']))

    # フッター
    story.append(Spacer(1, 10*mm))
    story.append(Paragraph(
        "このレポートはAIによる自動分析です。参考情報としてご活用ください。",
        styles['JapaneseSmall']
    ))

    # PDF生成
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def _score_stars(score: int) -> str:
    """スコアを星で表現"""
    return "★" * score + "☆" * (5 - score)
