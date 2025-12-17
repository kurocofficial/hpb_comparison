"""
チャート生成モジュール
Plotlyを使用してレーダーチャートとバーチャートを生成
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_radar_chart(
    my_salon_scores: dict,
    competitor_scores: list[dict] = None,
    title: str = "サロン評価比較"
) -> go.Figure:
    """
    レーダーチャートを生成

    Args:
        my_salon_scores: 自店舗のスコア {"name": str, "pv": int, "cv": int, "price": int, "diff": int}
        competitor_scores: 競合店舗のスコアリスト
        title: チャートタイトル

    Returns:
        go.Figure: Plotlyフィギュア
    """
    categories = ['PV獲得力', 'CV転換力', '価格競争力', '差別化']

    fig = go.Figure()

    # 自店舗
    fig.add_trace(go.Scatterpolar(
        r=[
            my_salon_scores['pv'],
            my_salon_scores['cv'],
            my_salon_scores['price'],
            my_salon_scores['diff'],
            my_salon_scores['pv']  # 閉じるために最初の値を追加
        ],
        theta=categories + [categories[0]],
        fill='toself',
        name=my_salon_scores.get('name', '自店舗'),
        line=dict(color='#FF6B6B', width=3),
        fillcolor='rgba(255, 107, 107, 0.3)'
    ))

    # 競合店舗
    colors = ['#4ECDC4', '#45B7D1', '#96CEB4']
    if competitor_scores:
        for i, comp in enumerate(competitor_scores):
            fig.add_trace(go.Scatterpolar(
                r=[
                    comp['pv'],
                    comp['cv'],
                    comp['price'],
                    comp['diff'],
                    comp['pv']
                ],
                theta=categories + [categories[0]],
                fill='toself',
                name=comp.get('name', f'競合{i+1}'),
                line=dict(color=colors[i % len(colors)], width=2),
                fillcolor=f'rgba({",".join(str(int(colors[i % len(colors)][j:j+2], 16)) for j in (1, 3, 5))}, 0.2)'
            ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5],
                tickvals=[1, 2, 3, 4, 5],
                tickfont=dict(size=12)
            ),
            angularaxis=dict(
                tickfont=dict(size=14)
            )
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.2,
            xanchor="center",
            x=0.5,
            font=dict(size=12)
        ),
        title=dict(
            text=title,
            font=dict(size=18),
            x=0.5
        ),
        margin=dict(l=40, r=40, t=60, b=80),
        height=400
    )

    return fig


def create_comparison_bar_chart(
    my_salon_scores: dict,
    competitor_scores: list[dict] = None,
    title: str = "項目別スコア比較"
) -> go.Figure:
    """
    横棒グラフで項目別比較を表示

    Args:
        my_salon_scores: 自店舗のスコア
        competitor_scores: 競合店舗のスコアリスト
        title: チャートタイトル

    Returns:
        go.Figure: Plotlyフィギュア
    """
    categories = ['PV獲得力', 'CV転換力', '価格競争力', '差別化']

    fig = go.Figure()

    # 自店舗
    fig.add_trace(go.Bar(
        name=my_salon_scores.get('name', '自店舗'),
        x=[
            my_salon_scores['pv'],
            my_salon_scores['cv'],
            my_salon_scores['price'],
            my_salon_scores['diff']
        ],
        y=categories,
        orientation='h',
        marker_color='#FF6B6B',
        text=[
            my_salon_scores['pv'],
            my_salon_scores['cv'],
            my_salon_scores['price'],
            my_salon_scores['diff']
        ],
        textposition='auto'
    ))

    # 競合店舗
    colors = ['#4ECDC4', '#45B7D1', '#96CEB4']
    if competitor_scores:
        for i, comp in enumerate(competitor_scores):
            fig.add_trace(go.Bar(
                name=comp.get('name', f'競合{i+1}'),
                x=[
                    comp['pv'],
                    comp['cv'],
                    comp['price'],
                    comp['diff']
                ],
                y=categories,
                orientation='h',
                marker_color=colors[i % len(colors)],
                text=[
                    comp['pv'],
                    comp['cv'],
                    comp['price'],
                    comp['diff']
                ],
                textposition='auto'
            ))

    fig.update_layout(
        barmode='group',
        title=dict(
            text=title,
            font=dict(size=18),
            x=0.5
        ),
        xaxis=dict(
            title='スコア',
            range=[0, 5.5],
            tickvals=[0, 1, 2, 3, 4, 5],
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            tickfont=dict(size=14)
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.3,
            xanchor="center",
            x=0.5,
            font=dict(size=12)
        ),
        margin=dict(l=100, r=40, t=60, b=80),
        height=350
    )

    return fig


def create_total_score_gauge(score: float, name: str = "総合スコア") -> go.Figure:
    """
    総合スコアのゲージチャートを生成

    Args:
        score: 総合スコア (0-5)
        name: 表示名

    Returns:
        go.Figure: Plotlyフィギュア
    """
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': name, 'font': {'size': 16}},
        number={'font': {'size': 40}, 'suffix': '/5'},
        gauge={
            'axis': {'range': [0, 5], 'tickwidth': 1, 'tickfont': {'size': 12}},
            'bar': {'color': "#FF6B6B"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 2], 'color': '#FFE5E5'},
                {'range': [2, 3.5], 'color': '#FFF3E5'},
                {'range': [3.5, 5], 'color': '#E5FFE5'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': score
            }
        }
    ))

    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=40, b=20)
    )

    return fig


def create_gender_pie_chart(gender_ratio: dict) -> go.Figure:
    """
    性別比率の円グラフを生成

    Args:
        gender_ratio: {"female": 73, "male": 26, "other": 0}

    Returns:
        go.Figure: Plotlyフィギュア
    """
    labels = ['女性', '男性', 'その他']
    values = [
        gender_ratio.get('female', 0),
        gender_ratio.get('male', 0),
        gender_ratio.get('other', 0)
    ]
    colors = ['#FF9999', '#66B2FF', '#C0C0C0']

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(colors=colors),
        textinfo='label+text',
        text=[f'{v}%' for v in values],
        textfont=dict(size=12),
        hovertemplate='%{label}: %{text}<extra></extra>'
    )])

    fig.update_layout(
        title=dict(
            text='性別比率',
            font=dict(size=16),
            x=0.5
        ),
        showlegend=False,
        margin=dict(l=20, r=20, t=50, b=20),
        height=250
    )

    return fig


def create_age_bar_chart(age_ratio: dict) -> go.Figure:
    """
    年代比率の横棒グラフを生成

    Args:
        age_ratio: {"under_10s": 5, "20s": 33, "30s": 28, "40s": 19, "50s_plus": 15}

    Returns:
        go.Figure: Plotlyフィギュア
    """
    labels = ['〜10代', '20代', '30代', '40代', '50代〜']
    values = [
        age_ratio.get('under_10s', 0),
        age_ratio.get('20s', 0),
        age_ratio.get('30s', 0),
        age_ratio.get('40s', 0),
        age_ratio.get('50s_plus', 0)
    ]
    colors = ['#FFB3BA', '#FFDFBA', '#FFFFBA', '#BAFFC9', '#BAE1FF']

    fig = go.Figure(data=[go.Bar(
        x=values,
        y=labels,
        orientation='h',
        marker=dict(color=colors),
        text=[f'{v}%' for v in values],
        textposition='outside',
        hovertemplate='%{y}: %{x}%<extra></extra>'
    )])

    fig.update_layout(
        title=dict(
            text='年代比率（女性）',
            font=dict(size=16),
            x=0.5
        ),
        xaxis=dict(
            title='割合（%）',
            range=[0, max(values) * 1.2 if values else 50],
            ticksuffix='%'
        ),
        yaxis=dict(
            autorange='reversed'
        ),
        margin=dict(l=60, r=40, t=50, b=40),
        height=250
    )

    return fig


def create_score_summary_cards(
    my_salon_scores: dict,
    competitor_scores: list[dict] = None
) -> go.Figure:
    """
    スコアサマリーテーブルを生成

    Args:
        my_salon_scores: 自店舗のスコア
        competitor_scores: 競合店舗のスコアリスト

    Returns:
        go.Figure: Plotlyフィギュア
    """
    headers = ['項目', my_salon_scores.get('name', '自店舗')]
    cells_data = [
        ['PV獲得力', 'CV転換力', '価格競争力', '差別化', '総合'],
        [
            f"{'★' * my_salon_scores['pv']}{'☆' * (5 - my_salon_scores['pv'])}",
            f"{'★' * my_salon_scores['cv']}{'☆' * (5 - my_salon_scores['cv'])}",
            f"{'★' * my_salon_scores['price']}{'☆' * (5 - my_salon_scores['price'])}",
            f"{'★' * my_salon_scores['diff']}{'☆' * (5 - my_salon_scores['diff'])}",
            f"{my_salon_scores.get('total', 0):.1f}"
        ]
    ]

    if competitor_scores:
        for comp in competitor_scores:
            headers.append(comp.get('name', '競合'))
            cells_data.append([
                f"{'★' * comp['pv']}{'☆' * (5 - comp['pv'])}",
                f"{'★' * comp['cv']}{'☆' * (5 - comp['cv'])}",
                f"{'★' * comp['price']}{'☆' * (5 - comp['price'])}",
                f"{'★' * comp['diff']}{'☆' * (5 - comp['diff'])}",
                f"{comp.get('total', 0):.1f}"
            ])

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=headers,
            fill_color='#FF6B6B',
            align='center',
            font=dict(color='white', size=14)
        ),
        cells=dict(
            values=cells_data,
            fill_color=[['white', '#f9f9f9'] * 3],
            align='center',
            font=dict(size=12),
            height=35
        )
    )])

    fig.update_layout(
        margin=dict(l=10, r=10, t=10, b=10),
        height=250
    )

    return fig
