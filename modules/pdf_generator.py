"""
PDF生成モジュール
ReportLabを使用して日本語対応PDFレポートを生成
"""

import io
import os
import urllib.request
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
    KeepTogether,
)


# フォントキャッシュディレクトリ
FONT_CACHE_DIR = Path(tempfile.gettempdir()) / "hpb_fonts"
NOTO_SANS_JP_URL = "https://github.com/google/fonts/raw/main/ofl/notosansjp/NotoSansJP-Regular.ttf"

# 採点基準
SCORING_CRITERIA = {
    "pv": {
        "name": "集客力",
        "items": {
            "1-1": "キャッチコピーが独自性あり",
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
            "2-2": "強い緊急性訴求あり",
            "2-3": "全メニューに詳細説明",
            "2-4": "ビフォーアフター写真10組以上",
            "2-5": "口コミ返信率80%以上",
        }
    },
    "price": {
        "name": "価格競争力",
        "items": {
            "3-1": "競合より20%以上安い",
            "3-2": "初回割引50%以上",
            "3-3": "セットメニュー3つ以上",
            "3-4": "追加料金・オプション料金の明記",
            "3-5": "施術時間・内容が充実",
        }
    },
    "diff": {
        "name": "差別化",
        "items": {
            "4-1": "エリアで唯一/希少な専門性",
            "4-2": "ターゲット層が具体的",
            "4-3": "資格・受賞歴の権威性",
            "4-4": "独自メニュー・技術",
            "4-5": "メディア掲載・SNS1万人以上",
        }
    }
}


def download_noto_sans_jp() -> Optional[str]:
    """Noto Sans JPフォントをダウンロード"""
    try:
        FONT_CACHE_DIR.mkdir(parents=True, exist_ok=True)
        font_path = FONT_CACHE_DIR / "NotoSansJP-Regular.ttf"

        if font_path.exists():
            return str(font_path)

        urllib.request.urlretrieve(NOTO_SANS_JP_URL, font_path)
        return str(font_path)
    except Exception:
        return None


def register_japanese_font():
    """日本語フォントを登録"""
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

    return "Helvetica"


def generate_pdf_report(
    my_salon_data: dict,
    competitor_data: list[dict],
    comparison_summary: str,
    recommendations: list[str],
    radar_chart_image: Optional[bytes] = None,
    bar_chart_image: Optional[bytes] = None,
    gender_ratio: Optional[dict] = None,
    age_ratio: Optional[dict] = None,
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
        gender_ratio: 性別比率データ {"female": 73, "male": 26, "other": 0}
        age_ratio: 年代比率データ {"under_10s": 5, "20s": 33, ...}

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
        fontSize=22,
        leading=28,
        alignment=1,
        spaceAfter=8*mm,
        textColor=colors.HexColor('#333333')
    ))
    styles.add(ParagraphStyle(
        name='JapaneseSubtitle',
        fontName=font_name,
        fontSize=12,
        leading=16,
        alignment=1,
        spaceAfter=5*mm,
        textColor=colors.HexColor('#666666')
    ))
    styles.add(ParagraphStyle(
        name='JapaneseHeading',
        fontName=font_name,
        fontSize=14,
        leading=18,
        spaceBefore=6*mm,
        spaceAfter=4*mm,
        textColor=colors.HexColor('#FF6B6B')
    ))
    styles.add(ParagraphStyle(
        name='JapaneseHeading2',
        fontName=font_name,
        fontSize=12,
        leading=16,
        spaceBefore=4*mm,
        spaceAfter=2*mm,
        textColor=colors.HexColor('#333333')
    ))
    styles.add(ParagraphStyle(
        name='JapaneseBody',
        fontName=font_name,
        fontSize=10,
        leading=16,
        spaceAfter=2*mm
    ))
    styles.add(ParagraphStyle(
        name='JapaneseSmall',
        fontName=font_name,
        fontSize=8,
        leading=12,
        textColor=colors.HexColor('#666666')
    ))
    styles.add(ParagraphStyle(
        name='CheckItem',
        fontName=font_name,
        fontSize=9,
        leading=14,
        leftIndent=10
    ))

    story = []

    # ===== 表紙セクション =====
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph(
        "HPB分析レポート",
        styles['JapaneseTitle']
    ))
    story.append(Paragraph(
        "ホットペッパービューティー サロン競合分析",
        styles['JapaneseSubtitle']
    ))
    story.append(Spacer(1, 10*mm))

    # サロン情報
    story.append(Paragraph(
        f"対象サロン: {my_salon_data.get('name', '不明')}",
        styles['JapaneseBody']
    ))
    story.append(Paragraph(
        f"作成日時: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}",
        styles['JapaneseSmall']
    ))
    story.append(Spacer(1, 10*mm))

    # ===== 総合スコアセクション =====
    story.append(Paragraph("総合評価", styles['JapaneseHeading']))

    # 大きなスコア表示
    total_score = my_salon_data.get('total', 0)
    score_color = '#4CAF50' if total_score >= 4 else '#FF9800' if total_score >= 3 else '#F44336'

    score_table_data = [
        [Paragraph(f"<font size='28' color='{score_color}'><b>{total_score:.1f}</b></font><font size='14'>/5</font>", styles['JapaneseBody'])]
    ]
    score_display = Table(score_table_data, colWidths=[80*mm])
    score_display.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOX', (0, 0), (-1, -1), 2, colors.HexColor(score_color)),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f9f9f9')),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(score_display)
    story.append(Spacer(1, 5*mm))

    # 4項目スコアテーブル
    score_data = [
        ['評価項目', 'スコア', '評価'],
        ['集客力', f"{my_salon_data.get('pv', 0)}/5", _get_rating_text(my_salon_data.get('pv', 0))],
        ['予約力', f"{my_salon_data.get('cv', 0)}/5", _get_rating_text(my_salon_data.get('cv', 0))],
        ['価格競争力', f"{my_salon_data.get('price', 0)}/5", _get_rating_text(my_salon_data.get('price', 0))],
        ['差別化', f"{my_salon_data.get('diff', 0)}/5", _get_rating_text(my_salon_data.get('diff', 0))],
    ]

    score_table = Table(score_data, colWidths=[60*mm, 40*mm, 60*mm])
    score_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B6B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 8*mm))

    # ===== グラフセクション =====
    if radar_chart_image or bar_chart_image:
        story.append(Paragraph("評価チャート", styles['JapaneseHeading']))

        if radar_chart_image:
            try:
                img = Image(io.BytesIO(radar_chart_image), width=160*mm, height=100*mm)
                story.append(img)
                story.append(Spacer(1, 5*mm))
            except Exception:
                pass

        if bar_chart_image:
            try:
                img = Image(io.BytesIO(bar_chart_image), width=160*mm, height=80*mm)
                story.append(img)
                story.append(Spacer(1, 5*mm))
            except Exception:
                pass

    # ===== 採点詳細セクション =====
    story.append(PageBreak())
    story.append(Paragraph("採点詳細", styles['JapaneseHeading']))
    story.append(Paragraph(
        "各項目の評価基準と判定結果です。チェックが多いほど高評価となります。",
        styles['JapaneseSmall']
    ))
    story.append(Spacer(1, 3*mm))

    score_details = {
        "pv": my_salon_data.get('pv_details', []),
        "cv": my_salon_data.get('cv_details', []),
        "price": my_salon_data.get('price_details', []),
        "diff": my_salon_data.get('diff_details', []),
    }

    for key, criteria in SCORING_CRITERIA.items():
        details = score_details.get(key, [])
        score = my_salon_data.get(key, 0)

        # カテゴリヘッダー
        story.append(Paragraph(
            f"{criteria['name']} ({score}/5点)",
            styles['JapaneseHeading2']
        ))

        # チェック項目テーブル
        check_data = []
        for item_id, item_label in criteria["items"].items():
            is_checked = item_id in details
            mark = "○" if is_checked else "×"
            mark_color = '#4CAF50' if is_checked else '#999999'
            check_data.append([
                Paragraph(f"<font color='{mark_color}'><b>{mark}</b></font>", styles['CheckItem']),
                Paragraph(item_label, styles['CheckItem'])
            ])

        check_table = Table(check_data, colWidths=[15*mm, 150*mm])
        check_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        story.append(check_table)
        story.append(Spacer(1, 3*mm))

    # ===== 予約比率セクション =====
    if gender_ratio or age_ratio:
        story.append(Spacer(1, 5*mm))
        story.append(Paragraph("予約比率", styles['JapaneseHeading']))
        story.append(Paragraph(
            "直近3カ月のネット予約データに基づく顧客層の分析です。",
            styles['JapaneseSmall']
        ))
        story.append(Spacer(1, 3*mm))

        ratio_data = []

        if gender_ratio:
            story.append(Paragraph("性別比率", styles['JapaneseHeading2']))
            gender_table_data = [
                ['女性', '男性', 'その他'],
                [
                    f"{gender_ratio.get('female', 0)}%",
                    f"{gender_ratio.get('male', 0)}%",
                    f"{gender_ratio.get('other', 0)}%"
                ]
            ]
            gender_table = Table(gender_table_data, colWidths=[50*mm, 50*mm, 50*mm])
            gender_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF9999')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(gender_table)
            story.append(Spacer(1, 5*mm))

        if age_ratio:
            story.append(Paragraph("年代比率（女性）", styles['JapaneseHeading2']))
            age_table_data = [
                ['〜10代', '20代', '30代', '40代', '50代〜'],
                [
                    f"{age_ratio.get('under_10s', 0)}%",
                    f"{age_ratio.get('20s', 0)}%",
                    f"{age_ratio.get('30s', 0)}%",
                    f"{age_ratio.get('40s', 0)}%",
                    f"{age_ratio.get('50s_plus', 0)}%"
                ]
            ]
            age_table = Table(age_table_data, colWidths=[32*mm, 32*mm, 32*mm, 32*mm, 32*mm])
            age_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FFB3BA')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            story.append(age_table)
            story.append(Spacer(1, 5*mm))

    # ===== 競合比較セクション =====
    if competitor_data:
        story.append(PageBreak())
        story.append(Paragraph("競合比較", styles['JapaneseHeading']))

        # 比較テーブル
        comp_header = ['評価項目', my_salon_data.get('name', '自店舗')[:10]]
        for i, c in enumerate(competitor_data):
            comp_header.append(c.get('name', f'競合{i+1}')[:10])

        comp_data = [comp_header]

        for key, label in [('pv', '集客力'), ('cv', '予約力'), ('price', '価格競争力'), ('diff', '差別化'), ('total', '総合')]:
            row = [label]
            my_val = my_salon_data.get(key, 0)
            if key == 'total':
                row.append(f"{my_val:.1f}")
            else:
                row.append(str(my_val))

            for c in competitor_data:
                c_val = c.get(key, 0)
                if key == 'total':
                    row.append(f"{c_val:.1f}")
                else:
                    row.append(str(c_val))
            comp_data.append(row)

        col_widths = [40*mm] + [35*mm] * (1 + len(competitor_data))
        comp_table = Table(comp_data, colWidths=col_widths)
        comp_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B6B')),
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(comp_table)
        story.append(Spacer(1, 8*mm))

    # ===== 強み・弱みセクション =====
    story.append(Paragraph("強み・弱み分析", styles['JapaneseHeading']))

    col_data = []
    strengths = my_salon_data.get('strengths', [])[:5]
    weaknesses = my_salon_data.get('weaknesses', [])[:5]

    max_len = max(len(strengths), len(weaknesses))

    strength_header = Paragraph("<b>強み</b>", styles['JapaneseBody'])
    weakness_header = Paragraph("<b>改善点</b>", styles['JapaneseBody'])
    col_data.append([strength_header, weakness_header])

    for i in range(max_len):
        s = strengths[i] if i < len(strengths) else ""
        w = weaknesses[i] if i < len(weaknesses) else ""
        col_data.append([
            Paragraph(f"+ {s}" if s else "", styles['JapaneseSmall']),
            Paragraph(f"- {w}" if w else "", styles['JapaneseSmall'])
        ])

    sw_table = Table(col_data, colWidths=[85*mm, 85*mm])
    sw_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, 0), colors.HexColor('#E8F5E9')),
        ('BACKGROUND', (1, 0), (1, 0), colors.HexColor('#FFEBEE')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.grey),
        ('LINEBELOW', (0, 0), (-1, 0), 1, colors.grey),
    ]))
    story.append(sw_table)
    story.append(Spacer(1, 8*mm))

    # ===== 改善提案セクション =====
    story.append(Paragraph("改善提案", styles['JapaneseHeading']))
    story.append(Paragraph(
        "優先度の高い順に改善施策を提案します。",
        styles['JapaneseSmall']
    ))
    story.append(Spacer(1, 3*mm))

    improvements = my_salon_data.get('improvements', recommendations)[:5]
    for i, imp in enumerate(improvements, 1):
        priority_color = '#F44336' if i == 1 else '#FF9800' if i == 2 else '#4CAF50'
        story.append(Paragraph(
            f"<font color='{priority_color}'><b>{i}.</b></font> {imp}",
            styles['JapaneseBody']
        ))

    # ===== 比較分析サマリー =====
    if comparison_summary:
        story.append(PageBreak())
        story.append(Paragraph("比較分析サマリー", styles['JapaneseHeading']))

        summary_lines = comparison_summary.split('\n')
        for line in summary_lines:
            if line.strip():
                if line.startswith('###'):
                    story.append(Paragraph(
                        line.replace('###', '').strip(),
                        styles['JapaneseHeading2']
                    ))
                elif line.startswith('#'):
                    continue
                else:
                    clean_line = line.replace('★', '[*]').replace('☆', '[ ]')
                    story.append(Paragraph(clean_line, styles['JapaneseBody']))

    # ===== フッター =====
    story.append(Spacer(1, 15*mm))
    story.append(Paragraph(
        "---",
        styles['JapaneseSmall']
    ))
    story.append(Paragraph(
        "このレポートはAIによる自動分析です。参考情報としてご活用ください。",
        styles['JapaneseSmall']
    ))
    story.append(Paragraph(
        "Generated by HPB分析ツール",
        styles['JapaneseSmall']
    ))

    # PDF生成
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def _get_rating_text(score: int) -> str:
    """スコアから評価テキストを取得"""
    if score >= 5:
        return "非常に優れている"
    elif score >= 4:
        return "優れている"
    elif score >= 3:
        return "平均的"
    elif score >= 2:
        return "改善が必要"
    else:
        return "要重点改善"


def _score_stars(score: int) -> str:
    """スコアを星で表現"""
    return "★" * score + "☆" * (5 - score)
