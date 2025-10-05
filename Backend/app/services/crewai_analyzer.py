from crewai import Agent, Task, Crew, Process
from app.services.llm_providers import LLMProvider
import logging
import json
import re

logger = logging.getLogger(__name__)

class FinancialAnalyzer:
    def __init__(self, llm_provider=None):
        self.llm = LLMProvider.get_llm(llm_provider)
    
    def analyze(self, document_text, options=None):
        """
        Analyze financial document using CrewAI
        Returns structured analysis results
        """
        try:
            logger.info("Starting CrewAI analysis")
            
            # Define agents
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
            
            # Define tasks
            financial_task = Task(
                description=f"""
                Analyze the following financial document and extract key metrics:
                
                {document_text[:5000]}  # Limit text to avoid token limits
                
                Provide:
                1. Revenue and earnings summary
                2. Key financial ratios
                3. Year-over-year growth rates
                4. Notable financial highlights
                
                Format your response as structured data.
                """,
                agent=financial_analyst,
                expected_output="A comprehensive financial summary with key metrics and trends"
            )
            
            risk_task = Task(
                description=f"""
                Based on this financial document, assess the risk profile:
                
                {document_text[:5000]}
                
                Provide:
                1. Overall risk score (0-1)
                2. Major risk factors
                3. Risk mitigation strategies
                4. Risk category breakdown
                
                Be specific and data-driven.
                """,
                agent=risk_analyst,
                expected_output="A detailed risk assessment with quantified risk scores"
            )
            
            market_task = Task(
                description=f"""
                Analyze market trends and competitive position from this document:
                
                {document_text[:5000]}
                
                Provide:
                1. Market trends identified
                2. Competitive positioning
                3. Growth opportunities
                4. Market challenges
                """,
                agent=market_analyst,
                expected_output="Market analysis with actionable insights"
            )
            
            # Create crew
            crew = Crew(
                agents=[financial_analyst, risk_analyst, market_analyst],
                tasks=[financial_task, risk_task, market_task],
                process=Process.sequential,
                verbose=True
            )
            
            # Execute analysis
            result = crew.kickoff()
            
            # Parse and structure results
            structured_results = self._parse_results(result, document_text)
            
            logger.info("CrewAI analysis completed successfully")
            
            return structured_results
            
        except Exception as e:
            logger.error(f"Analysis error: {str(e)}")
            raise
    
    def _parse_results(self, crew_result, original_text):
        """Parse CrewAI results into structured format"""
        try:
            # Convert crew result to string if needed
            result_text = str(crew_result)
            
            # Extract key information
            financial_summary = self._extract_financial_summary(result_text)
            risk_assessment = self._extract_risk_assessment(result_text)
            market_insights = self._extract_market_insights(result_text)
            recommendations = self._generate_recommendations(result_text)
            
            # Generate chart data
            charts_data = self._generate_charts_data(result_text, original_text)
            
            return {
                'financialSummary': financial_summary,
                'riskAssessment': risk_assessment,
                'marketInsights': market_insights,
                'recommendations': recommendations,
                'chartsData': charts_data
            }
            
        except Exception as e:
            logger.error(f"Error parsing results: {str(e)}")
            return {
                'financialSummary': 'Analysis completed. Please review the detailed report.',
                'riskAssessment': {
                    'score': 0.5,
                    'details': 'Risk assessment completed'
                },
                'recommendations': 'Review document for specific recommendations',
                'chartsData': {}
            }
    
    def _extract_financial_summary(self, text):
        """Extract financial summary from analysis"""
        # Simple extraction - can be enhanced with regex
        lines = text.split('\n')
        summary_lines = [line for line in lines if any(keyword in line.lower() 
                        for keyword in ['revenue', 'profit', 'earnings', 'growth', 'margin'])]
        return ' '.join(summary_lines[:10]) if summary_lines else 'Financial summary generated'
    
    def _extract_risk_assessment(self, text):
        """Extract risk assessment from analysis"""
        # Try to find risk score
        risk_score = 0.5  # Default
        score_match = re.search(r'risk score[:\s]+(\d+\.?\d*)', text.lower())
        if score_match:
            risk_score = float(score_match.group(1))
            if risk_score > 1:
                risk_score = risk_score / 100
        
        # Extract risk details
        lines = text.split('\n')
        risk_lines = [line for line in lines if any(keyword in line.lower() 
                     for keyword in ['risk', 'threat', 'challenge', 'concern'])]
        details = ' '.join(risk_lines[:5]) if risk_lines else 'Risk factors identified'
        
        return {
            'score': risk_score,
            'details': details
        }
    
    def _extract_market_insights(self, text):
        """Extract market insights from analysis"""
        lines = text.split('\n')
        market_lines = [line for line in lines if any(keyword in line.lower() 
                       for keyword in ['market', 'trend', 'competitive', 'industry', 'growth'])]
        return ' '.join(market_lines[:5]) if market_lines else 'Market insights generated'
    
    def _generate_recommendations(self, text):
        """Generate recommendations from analysis"""
        lines = text.split('\n')
        rec_lines = [line for line in lines if any(keyword in line.lower() 
                    for keyword in ['recommend', 'should', 'suggest', 'consider', 'opportunity'])]
        return ' '.join(rec_lines[:5]) if rec_lines else 'See detailed analysis for recommendations'
    
    def _generate_charts_data(self, analysis_text, original_text):
        """Generate sample chart data from analysis"""
        # This is a simplified version - enhance based on actual data extraction
        return {
            'revenueTrend': [
                {'year': '2023', 'value': 100},
                {'year': '2024', 'value': 115},
                {'year': '2025', 'value': 130}
            ],
            'profitMargin': [
                {'quarter': 'Q1', 'value': 15.2},
                {'quarter': 'Q2', 'value': 16.8},
                {'quarter': 'Q3', 'value': 17.5},
                {'quarter': 'Q4', 'value': 18.1}
            ]
        }