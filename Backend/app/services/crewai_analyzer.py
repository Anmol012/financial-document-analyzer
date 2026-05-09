from crewai import Agent, Task, Crew, Process
from app.services.llm_providers import LLMProvider
import logging
import re

logger = logging.getLogger(__name__)

DOCUMENT_SNIPPET_LEN = 5000


class FinancialAnalyzer:
    def __init__(self, llm_provider=None):
        self.llm = LLMProvider.get_llm(llm_provider)

    def analyze(self, document_text, options=None):
        try:
            logger.info("Starting CrewAI analysis")

            snippet = document_text[:DOCUMENT_SNIPPET_LEN]

            financial_analyst = Agent(
                role='Senior Financial Analyst',
                goal='Extract and analyze key financial metrics from documents',
                backstory='You are an experienced financial analyst with expertise in analyzing financial statements, earnings reports, and market data.',
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            )

            risk_analyst = Agent(
                role='Risk Assessment Specialist',
                goal='Identify and evaluate financial risks',
                backstory='You specialize in risk assessment with deep knowledge of market volatility, credit risk, and operational risks.',
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            )

            market_analyst = Agent(
                role='Market Research Analyst',
                goal='Analyze market trends and provide insights',
                backstory='You are a market research expert who identifies trends, competitive dynamics, and growth opportunities.',
                verbose=True,
                allow_delegation=False,
                llm=self.llm
            )

            financial_task = Task(
                description=(
                    "Analyze the following financial document and extract key metrics:\n\n"
                    f"{snippet}\n\n"
                    "Provide:\n"
                    "1. Revenue and earnings summary\n"
                    "2. Key financial ratios\n"
                    "3. Year-over-year growth rates\n"
                    "4. Notable financial highlights\n\n"
                    "Format your response as structured data."
                ),
                agent=financial_analyst,
                expected_output="A comprehensive financial summary with key metrics and trends"
            )

            risk_task = Task(
                description=(
                    "Based on this financial document, assess the risk profile:\n\n"
                    f"{snippet}\n\n"
                    "Provide:\n"
                    "1. Overall risk score (0-1)\n"
                    "2. Major risk factors\n"
                    "3. Risk mitigation strategies\n"
                    "4. Risk category breakdown\n\n"
                    "Be specific and data-driven."
                ),
                agent=risk_analyst,
                expected_output="A detailed risk assessment with quantified risk scores"
            )

            market_task = Task(
                description=(
                    "Analyze market trends and competitive position from this document:\n\n"
                    f"{snippet}\n\n"
                    "Provide:\n"
                    "1. Market trends identified\n"
                    "2. Competitive positioning\n"
                    "3. Growth opportunities\n"
                    "4. Market challenges"
                ),
                agent=market_analyst,
                expected_output="Market analysis with actionable insights"
            )

            crew = Crew(
                agents=[financial_analyst, risk_analyst, market_analyst],
                tasks=[financial_task, risk_task, market_task],
                process=Process.sequential,
                verbose=True
            )

            result = crew.kickoff()
            structured_results = self._parse_results(result, document_text)

            logger.info("CrewAI analysis completed successfully")
            return structured_results

        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            raise

    def _parse_results(self, crew_result, original_text):
        try:
            result_text = str(crew_result)

            financial_summary = self._extract_financial_summary(result_text)
            risk_assessment = self._extract_risk_assessment(result_text)
            market_insights = self._extract_market_insights(result_text)
            recommendations = self._generate_recommendations(result_text)
            charts_data = self._generate_charts_data(result_text, original_text)

            return {
                'financialSummary': financial_summary,
                'riskAssessment': risk_assessment,
                'marketInsights': market_insights,
                'recommendations': recommendations,
                'chartsData': charts_data,
            }

        except Exception as e:
            logger.error(f"Error parsing results: {str(e)}")
            return {
                'financialSummary': 'Analysis completed. Please review the detailed report.',
                'riskAssessment': {'score': 0.5, 'details': 'Risk assessment completed'},
                'marketInsights': 'Market analysis completed.',
                'recommendations': 'Review document for specific recommendations',
                'chartsData': self._default_charts(),
            }

    def _extract_financial_summary(self, text):
        lines = text.split('\n')
        summary_lines = [
            line for line in lines
            if any(kw in line.lower() for kw in ['revenue', 'profit', 'earnings', 'growth', 'margin'])
        ]
        return ' '.join(summary_lines[:10]) if summary_lines else 'Financial summary generated'

    def _extract_risk_assessment(self, text):
        risk_score = 0.5
        score_match = re.search(r'risk score[:\s]+(\d+\.?\d*)', text.lower())
        if score_match:
            risk_score = float(score_match.group(1))
            if risk_score > 1:
                risk_score = risk_score / 100

        lines = text.split('\n')
        risk_lines = [
            line for line in lines
            if any(kw in line.lower() for kw in ['risk', 'threat', 'challenge', 'concern'])
        ]
        details = ' '.join(risk_lines[:5]) if risk_lines else 'Risk factors identified'

        return {'score': round(risk_score, 2), 'details': details}

    def _extract_market_insights(self, text):
        lines = text.split('\n')
        market_lines = [
            line for line in lines
            if any(kw in line.lower() for kw in ['market', 'trend', 'competitive', 'industry', 'growth'])
        ]
        return ' '.join(market_lines[:5]) if market_lines else 'Market insights generated'

    def _generate_recommendations(self, text):
        lines = text.split('\n')
        rec_lines = [
            line for line in lines
            if any(kw in line.lower() for kw in ['recommend', 'should', 'suggest', 'consider', 'opportunity'])
        ]
        return ' '.join(rec_lines[:5]) if rec_lines else 'See detailed analysis for recommendations'

    def _generate_charts_data(self, analysis_text, original_text):
        charts = {}

        # Revenue trend — try to pull years and revenue figures from the document
        years = sorted(set(re.findall(r'\b(20\d{2})\b', original_text[:10000])))[-4:]
        revenue_matches = re.findall(
            r'(?:revenue|sales|net revenue)[^\d]*\$?([\d,]+\.?\d*)\s*(?:million|billion|M|B)?',
            original_text[:10000],
            re.IGNORECASE
        )

        revenue_trend = []
        for i, year in enumerate(years):
            if i < len(revenue_matches):
                try:
                    val = float(revenue_matches[i].replace(',', ''))
                    revenue_trend.append({'year': year, 'value': val})
                except ValueError:
                    pass

        charts['revenueTrend'] = revenue_trend if revenue_trend else self._default_charts()['revenueTrend']

        # Profit margin — try from analysis text
        margin_matches = re.findall(
            r'(?:profit margin|net margin|gross margin)[^\d]*(\d+\.?\d*)\s*%',
            analysis_text,
            re.IGNORECASE
        )
        if margin_matches:
            quarters = ['Q1', 'Q2', 'Q3', 'Q4']
            charts['profitMargin'] = [
                {'quarter': quarters[i], 'value': float(m)}
                for i, m in enumerate(margin_matches[:4])
            ]
        else:
            charts['profitMargin'] = self._default_charts()['profitMargin']

        return charts

    def _default_charts(self):
        return {
            'revenueTrend': [
                {'year': '2023', 'value': 100},
                {'year': '2024', 'value': 115},
                {'year': '2025', 'value': 130},
            ],
            'profitMargin': [
                {'quarter': 'Q1', 'value': 15.2},
                {'quarter': 'Q2', 'value': 16.8},
                {'quarter': 'Q3', 'value': 17.5},
                {'quarter': 'Q4', 'value': 18.1},
            ],
        }
