"""
HPB Analyzer - Gemini API連携モジュール
ホットペッパービューティーのURL解析と比較分析を行う
"""

import os
import json
import re
from typing import Optional
from dataclasses import dataclass

import google.generativeai as genai
from prompts.analysis_prompts import (
    SALON_ANALYSIS_PROMPT,
    COMPARISON_PROMPT,
    CHAT_PROMPT,
)


@dataclass
class SalonScore:
    """サロン評価スコア"""
    name: str
    url: str
    pv_score: int  # PV獲得力 (1-5)
    cv_score: int  # CV転換力 (1-5)
    price_score: int  # 価格競争力 (1-5)
    diff_score: int  # 差別化 (1-5)
    total_score: float  # 総合スコア
    strengths: list[str]  # 強み
    weaknesses: list[str]  # 弱み
    improvements: list[str]  # 改善提案
    raw_analysis: str  # 生の分析結果


@dataclass
class ComparisonResult:
    """比較分析結果"""
    my_salon: SalonScore
    competitors: list[SalonScore]
    comparison_summary: str
    recommendations: list[str]


class HPBAnalyzer:
    """ホットペッパービューティー分析クラス"""

    def __init__(self, api_key: Optional[str] = None):
        """
        初期化

        Args:
            api_key: Gemini APIキー（省略時は環境変数から取得）
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")

    def analyze_salon(self, url: str, is_my_salon: bool = False) -> SalonScore:
        """
        単一サロンの分析

        Args:
            url: ホットペッパービューティーのサロンURL
            is_my_salon: 自店舗かどうか

        Returns:
            SalonScore: 分析結果
        """
        prompt = SALON_ANALYSIS_PROMPT.format(
            salon_type="自店舗" if is_my_salon else "競合店舗"
        )

        response = self.model.generate_content([
            prompt,
            {"url": url}
        ])

        return self._parse_salon_response(response.text, url)

    def compare_salons(
        self,
        my_salon_url: str,
        competitor_urls: list[str]
    ) -> ComparisonResult:
        """
        複数サロンの比較分析

        Args:
            my_salon_url: 自店舗URL
            competitor_urls: 競合店舗URLリスト

        Returns:
            ComparisonResult: 比較分析結果
        """
        # 自店舗分析
        my_salon = self.analyze_salon(my_salon_url, is_my_salon=True)

        # 競合分析
        competitors = []
        for url in competitor_urls:
            if url:
                competitor = self.analyze_salon(url, is_my_salon=False)
                competitors.append(competitor)

        # 比較サマリー生成
        comparison_summary, recommendations = self._generate_comparison(
            my_salon, competitors
        )

        return ComparisonResult(
            my_salon=my_salon,
            competitors=competitors,
            comparison_summary=comparison_summary,
            recommendations=recommendations
        )

    def chat(self, question: str, analysis_context: str) -> str:
        """
        分析結果についてのチャット応答

        Args:
            question: ユーザーの質問
            analysis_context: 分析結果のコンテキスト

        Returns:
            str: AI応答
        """
        prompt = CHAT_PROMPT.format(
            context=analysis_context,
            question=question
        )

        response = self.model.generate_content(prompt)
        return response.text

    def _parse_salon_response(self, response_text: str, url: str) -> SalonScore:
        """
        Gemini応答をパースしてSalonScoreを生成

        Args:
            response_text: Geminiからの応答テキスト
            url: サロンURL

        Returns:
            SalonScore: パース結果
        """
        # JSONブロックを抽出
        json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)

        if json_match:
            try:
                data = json.loads(json_match.group(1))
                return SalonScore(
                    name=data.get("name", "不明"),
                    url=url,
                    pv_score=int(data.get("pv_score", 3)),
                    cv_score=int(data.get("cv_score", 3)),
                    price_score=int(data.get("price_score", 3)),
                    diff_score=int(data.get("diff_score", 3)),
                    total_score=float(data.get("total_score", 3.0)),
                    strengths=data.get("strengths", []),
                    weaknesses=data.get("weaknesses", []),
                    improvements=data.get("improvements", []),
                    raw_analysis=response_text
                )
            except (json.JSONDecodeError, KeyError, ValueError):
                pass

        # パース失敗時はデフォルト値で返す
        return SalonScore(
            name="解析中のサロン",
            url=url,
            pv_score=3,
            cv_score=3,
            price_score=3,
            diff_score=3,
            total_score=3.0,
            strengths=["解析結果を取得中"],
            weaknesses=["解析結果を取得中"],
            improvements=["解析結果を取得中"],
            raw_analysis=response_text
        )

    def _generate_comparison(
        self,
        my_salon: SalonScore,
        competitors: list[SalonScore]
    ) -> tuple[str, list[str]]:
        """
        比較サマリーを生成

        Args:
            my_salon: 自店舗スコア
            competitors: 競合スコアリスト

        Returns:
            tuple: (比較サマリー, 推奨事項リスト)
        """
        # 比較用のコンテキスト作成
        context = f"""
自店舗: {my_salon.name}
- PV獲得力: {my_salon.pv_score}/5
- CV転換力: {my_salon.cv_score}/5
- 価格競争力: {my_salon.price_score}/5
- 差別化: {my_salon.diff_score}/5
- 総合: {my_salon.total_score}/5

"""
        for i, comp in enumerate(competitors, 1):
            context += f"""
競合{i}: {comp.name}
- PV獲得力: {comp.pv_score}/5
- CV転換力: {comp.cv_score}/5
- 価格競争力: {comp.price_score}/5
- 差別化: {comp.diff_score}/5
- 総合: {comp.total_score}/5

"""

        prompt = COMPARISON_PROMPT.format(scores_context=context)
        response = self.model.generate_content(prompt)

        # 応答をパース
        response_text = response.text

        # 推奨事項を抽出
        recommendations = []
        lines = response_text.split('\n')
        for line in lines:
            if line.strip().startswith(('1.', '2.', '3.', '-', '・')):
                clean_line = re.sub(r'^[\d\.\-・\s]+', '', line.strip())
                if clean_line:
                    recommendations.append(clean_line)

        if not recommendations:
            recommendations = ["詳細な分析結果をご確認ください"]

        return response_text, recommendations[:5]
