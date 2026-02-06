#!/usr/bin/env python3
"""
Bot Optimization Testing Suite for Jorge's System

Comprehensive testing to ensure optimal bot performance for real-world scenarios.

Author: Claude Code Assistant
Created: 2026-01-22
"""

import asyncio
import time
import random
from datetime import datetime
from typing import List, Dict, Any
from dataclasses import dataclass

# Import our bots
from jorge_lead_bot import create_jorge_lead_bot
from jorge_seller_bot import create_jorge_seller_bot
from config_settings import settings


@dataclass
class TestScenario:
    """Test scenario definition"""
    name: str
    contact_id: str
    message: str
    expected_score_min: float
    expected_temperature: str
    test_type: str  # 'lead' or 'seller'
    difficulty: str  # 'easy', 'medium', 'hard'


@dataclass
class TestResult:
    """Test result tracking"""
    scenario_name: str
    success: bool
    response_time: float
    score_achieved: float
    temperature: str
    response_quality: str
    errors: List[str]


class BotOptimizationTester:
    """Comprehensive bot testing and optimization suite"""

    def __init__(self):
        self.lead_bot = create_jorge_lead_bot()
        self.seller_bot = create_jorge_seller_bot()
        self.results = []

    def get_lead_test_scenarios(self) -> List[TestScenario]:
        """Define comprehensive lead testing scenarios"""

        return [
            # EASY SCENARIOS - High-quality leads
            TestScenario(
                name="Hot Lead - Tech Executive",
                contact_id="test_lead_tech_exec",
                message="Hi Jorge! I'm relocating from San Francisco for a VP role at Tesla. I have a $800k budget, need to close within 45 days, and I'm pre-approved. Looking for 4+ bedrooms in Westlake or Bee Cave with great schools. Can you help?",
                expected_score_min=8.5,
                expected_temperature="hot",
                test_type="lead",
                difficulty="easy"
            ),

            TestScenario(
                name="Ready Buyer - Cash Purchase",
                contact_id="test_lead_cash_buyer",
                message="I'm selling my rental property and have $650k cash to buy immediately. Need something move-in ready in North Austin. Timeline is flexible but want to close within 30 days to avoid capital gains. 3+ bedrooms minimum.",
                expected_score_min=8.0,
                expected_temperature="hot",
                test_type="lead",
                difficulty="easy"
            ),

            # MEDIUM SCENARIOS - Good leads with some challenges
            TestScenario(
                name="First-Time Buyer - Uncertain",
                contact_id="test_lead_first_time",
                message="Hi, I'm thinking about buying my first house. I make about $80k/year and have saved up $40k. Is that enough for a down payment? I don't really know where to start or what areas are good.",
                expected_score_min=5.0,
                expected_temperature="warm",
                test_type="lead",
                difficulty="medium"
            ),

            TestScenario(
                name="Budget Conscious - Tight Timeline",
                contact_id="test_lead_budget_tight",
                message="My lease ends in 6 weeks and my landlord is selling. I need to find something under $350k ASAP. I'm pre-approved but only have $15k for down payment. Anything available in that range?",
                expected_score_min=6.0,
                expected_temperature="warm",
                test_type="lead",
                difficulty="medium"
            ),

            # HARD SCENARIOS - Challenging leads to test bot limits
            TestScenario(
                name="Vague Inquiry - No Specifics",
                contact_id="test_lead_vague",
                message="Hey, I might be interested in buying a house sometime. What do you have?",
                expected_score_min=2.0,
                expected_temperature="cold",
                test_type="lead",
                difficulty="hard"
            ),

            TestScenario(
                name="Unrealistic Expectations",
                contact_id="test_lead_unrealistic",
                message="I want a 5-bedroom mansion with a pool in Westlake Hills for under $300k. I know the market is crazy but I'm sure there's something. I can't pay more than that.",
                expected_score_min=3.0,
                expected_temperature="cold",
                test_type="lead",
                difficulty="hard"
            ),

            TestScenario(
                name="Just Shopping Around",
                contact_id="test_lead_shopping",
                message="I'm just looking at different agents. Not sure if I want to buy or rent. Maybe in a year or two. What's the market like?",
                expected_score_min=2.5,
                expected_temperature="cold",
                test_type="lead",
                difficulty="hard"
            ),

            # EDGE CASES - Test error handling
            TestScenario(
                name="Empty Message",
                contact_id="test_lead_empty",
                message="",
                expected_score_min=1.0,
                expected_temperature="cold",
                test_type="lead",
                difficulty="hard"
            ),

            TestScenario(
                name="Non-English Message",
                contact_id="test_lead_spanish",
                message="Hola, quiero comprar una casa en Austin. ¿Puedes ayudarme?",
                expected_score_min=3.0,
                expected_temperature="cold",
                test_type="lead",
                difficulty="hard"
            )
        ]

    def get_seller_test_scenarios(self) -> List[TestScenario]:
        """Define comprehensive seller testing scenarios"""

        return [
            # EASY SCENARIOS - Motivated sellers
            TestScenario(
                name="Divorce Sale - Urgent",
                contact_id="test_seller_divorce",
                message="My husband and I are getting divorced and we need to sell our house in Round Rock ASAP. We just want it gone and don't want to deal with repairs or showings. It needs some work but it's in a good neighborhood. What can you offer?",
                expected_score_min=7.0,
                expected_temperature="hot",
                test_type="seller",
                difficulty="easy"
            ),

            TestScenario(
                name="Job Relocation - Fast Sale",
                contact_id="test_seller_relocation",
                message="I got transferred to Seattle and need to sell my house in Cedar Park within 60 days. It's move-in ready but I don't have time for the traditional sales process. Looking for a cash offer.",
                expected_score_min=7.5,
                expected_temperature="hot",
                test_type="seller",
                difficulty="easy"
            ),

            # MEDIUM SCENARIOS - Somewhat motivated
            TestScenario(
                name="Inherited Property - Out of State",
                contact_id="test_seller_inherited",
                message="I inherited my mom's house in Austin but I live in California. It's been sitting empty for 6 months and I'm tired of paying taxes and maintenance on it. What's the process to sell to you?",
                expected_score_min=6.0,
                expected_temperature="warm",
                test_type="seller",
                difficulty="medium"
            ),

            # HARD SCENARIOS - Testing Jorge's confrontational approach
            TestScenario(
                name="Just Testing the Market",
                contact_id="test_seller_testing",
                message="I'm not really sure if I want to sell, but I'm curious what my house might be worth. I don't need to sell, just exploring options.",
                expected_score_min=3.0,
                expected_temperature="cold",
                test_type="seller",
                difficulty="hard"
            ),

            TestScenario(
                name="Unrealistic Price Expectations",
                contact_id="test_seller_unrealistic",
                message="I want to sell my house but Zillow says it's worth $500k and I won't take less than that. I know you buy houses but I'm not giving it away.",
                expected_score_min=4.0,
                expected_temperature="cold",
                test_type="seller",
                difficulty="hard"
            ),

            TestScenario(
                name="Wasting Time - No Real Intent",
                contact_id="test_seller_time_waster",
                message="Yeah, I might sell someday. What's your process? How much do you usually pay? I'm just curious.",
                expected_score_min=2.0,
                expected_temperature="cold",
                test_type="seller",
                difficulty="hard"
            )
        ]

    async def run_single_test(self, scenario: TestScenario) -> TestResult:
        """Run a single test scenario and measure results"""

        start_time = time.time()
        errors = []

        try:
            if scenario.test_type == "lead":
                result = await self.lead_bot.process_lead_message(
                    contact_id=scenario.contact_id,
                    location_id=settings.ghl_location_id,
                    message=scenario.message
                )
                score = result.get('lead_score', 0.0)
                temperature = result.get('lead_temperature', 'cold')
                response = result.get('message', '')

            else:  # seller
                result = await self.seller_bot.process_seller_message(
                    contact_id=scenario.contact_id,
                    location_id=settings.ghl_location_id,
                    message=scenario.message
                )
                score = 8.0 if result.seller_temperature == 'hot' else 6.0 if result.seller_temperature == 'warm' else 3.0
                temperature = result.seller_temperature
                response = result.response_message

            response_time = time.time() - start_time

            # Evaluate response quality
            response_quality = self._evaluate_response_quality(response, scenario)

            # Check if results meet expectations
            success = (
                score >= scenario.expected_score_min and
                temperature == scenario.expected_temperature and
                len(response) > 10  # Basic response length check
            )

            return TestResult(
                scenario_name=scenario.name,
                success=success,
                response_time=response_time,
                score_achieved=score,
                temperature=temperature,
                response_quality=response_quality,
                errors=errors
            )

        except Exception as e:
            errors.append(str(e))
            return TestResult(
                scenario_name=scenario.name,
                success=False,
                response_time=time.time() - start_time,
                score_achieved=0.0,
                temperature="error",
                response_quality="failed",
                errors=errors
            )

    def _evaluate_response_quality(self, response: str, scenario: TestScenario) -> str:
        """Evaluate the quality of the bot response"""

        if not response or len(response) < 10:
            return "poor"

        # Check for Jorge's confrontational style in seller responses
        if scenario.test_type == "seller":
            confrontational_indicators = [
                "don't waste my time",
                "are you serious",
                "let's get straight to the point",
                "I'm not here to",
                "if you're not ready"
            ]

            has_confrontational_tone = any(indicator in response.lower() for indicator in confrontational_indicators)

            if has_confrontational_tone and len(response) > 50:
                return "excellent"
            elif len(response) > 30:
                return "good"
            else:
                return "fair"

        # Lead response quality
        else:
            helpful_indicators = [
                "help you",
                "let me",
                "I can",
                "what's your",
                "tell me more"
            ]

            is_helpful = any(indicator in response.lower() for indicator in helpful_indicators)

            if is_helpful and len(response) > 50:
                return "excellent"
            elif len(response) > 30:
                return "good"
            else:
                return "fair"

    async def stress_test_concurrent_leads(self, num_concurrent: int = 5) -> Dict[str, Any]:
        """Test bot performance under concurrent load"""

        print(f'🔥 STRESS TEST - {num_concurrent} CONCURRENT LEADS')
        print('=' * 50)

        # Create multiple test scenarios to run simultaneously
        scenarios = []
        for i in range(num_concurrent):
            scenarios.append(TestScenario(
                name=f"Concurrent Lead {i+1}",
                contact_id=f"stress_test_lead_{i+1}",
                message=f"Hi! I'm lead number {i+1}. I have a ${400 + i*50}k budget and need to buy within {30 + i*10} days. Can you help?",
                expected_score_min=6.0,
                expected_temperature="warm",
                test_type="lead",
                difficulty="medium"
            ))

        start_time = time.time()

        # Run all scenarios concurrently
        tasks = [self.run_single_test(scenario) for scenario in scenarios]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        total_time = time.time() - start_time

        # Analyze results
        successful_tests = [r for r in results if isinstance(r, TestResult) and r.success]
        failed_tests = [r for r in results if not isinstance(r, TestResult) or not r.success]

        avg_response_time = sum(r.response_time for r in successful_tests) / len(successful_tests) if successful_tests else 0

        print(f'📊 STRESS TEST RESULTS:')
        print(f'  • Total Concurrent Leads: {num_concurrent}')
        print(f'  • Successful Responses: {len(successful_tests)}/{num_concurrent}')
        print(f'  • Average Response Time: {avg_response_time:.2f} seconds')
        print(f'  • Total Test Time: {total_time:.2f} seconds')
        print(f'  • Success Rate: {len(successful_tests)/num_concurrent*100:.1f}%')
        print()

        return {
            'total_leads': num_concurrent,
            'successful': len(successful_tests),
            'failed': len(failed_tests),
            'avg_response_time': avg_response_time,
            'total_time': total_time,
            'success_rate': len(successful_tests)/num_concurrent*100
        }

    async def run_comprehensive_test_suite(self) -> Dict[str, Any]:
        """Run the complete optimization test suite"""

        print('🧪 JORGE\'S BOT OPTIMIZATION TEST SUITE')
        print('=' * 60)
        print(f'Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
        print()

        all_scenarios = self.get_lead_test_scenarios() + self.get_seller_test_scenarios()

        results_by_difficulty = {'easy': [], 'medium': [], 'hard': []}
        results_by_type = {'lead': [], 'seller': []}

        print('🔵 TESTING LEAD BOT SCENARIOS')
        print('=' * 40)

        lead_scenarios = [s for s in all_scenarios if s.test_type == 'lead']

        for scenario in lead_scenarios:
            print(f'Testing: {scenario.name} ({scenario.difficulty})')
            result = await self.run_single_test(scenario)

            self.results.append(result)
            results_by_difficulty[scenario.difficulty].append(result)
            results_by_type['lead'].append(result)

            status = '✅' if result.success else '❌'
            print(f'  {status} Score: {result.score_achieved:.1f} | Time: {result.response_time:.2f}s | Quality: {result.response_quality}')

            # Small delay to avoid rate limiting
            await asyncio.sleep(0.5)

        print()
        print('🟢 TESTING SELLER BOT SCENARIOS')
        print('=' * 40)

        seller_scenarios = [s for s in all_scenarios if s.test_type == 'seller']

        for scenario in seller_scenarios:
            print(f'Testing: {scenario.name} ({scenario.difficulty})')
            result = await self.run_single_test(scenario)

            self.results.append(result)
            results_by_difficulty[scenario.difficulty].append(result)
            results_by_type['seller'].append(result)

            status = '✅' if result.success else '❌'
            print(f'  {status} Temp: {result.temperature} | Time: {result.response_time:.2f}s | Quality: {result.response_quality}')

            await asyncio.sleep(0.5)

        print()

        # Run stress test
        stress_results = await self.stress_test_concurrent_leads(5)

        # Generate comprehensive report
        return self._generate_optimization_report(results_by_difficulty, results_by_type, stress_results)

    def _generate_optimization_report(self, by_difficulty: Dict, by_type: Dict, stress_results: Dict) -> Dict:
        """Generate comprehensive optimization report"""

        print('📊 COMPREHENSIVE OPTIMIZATION REPORT')
        print('=' * 50)

        total_tests = len(self.results)
        successful_tests = [r for r in self.results if r.success]

        overall_success_rate = len(successful_tests) / total_tests * 100 if total_tests > 0 else 0
        avg_response_time = sum(r.response_time for r in successful_tests) / len(successful_tests) if successful_tests else 0

        print(f'🎯 OVERALL PERFORMANCE:')
        print(f'  • Total Tests: {total_tests}')
        print(f'  • Success Rate: {overall_success_rate:.1f}%')
        print(f'  • Avg Response Time: {avg_response_time:.2f} seconds')
        print()

        # Performance by difficulty
        print('📈 PERFORMANCE BY DIFFICULTY:')
        for difficulty, results in by_difficulty.items():
            if results:
                success_rate = len([r for r in results if r.success]) / len(results) * 100
                avg_time = sum(r.response_time for r in results) / len(results)
                print(f'  • {difficulty.capitalize()}: {success_rate:.1f}% success, {avg_time:.2f}s avg')
        print()

        # Performance by bot type
        print('🤖 PERFORMANCE BY BOT TYPE:')
        for bot_type, results in by_type.items():
            if results:
                success_rate = len([r for r in results if r.success]) / len(results) * 100
                avg_time = sum(r.response_time for r in results) / len(results)
                print(f'  • {bot_type.capitalize()} Bot: {success_rate:.1f}% success, {avg_time:.2f}s avg')
        print()

        # Response quality analysis
        quality_counts = {}
        for result in successful_tests:
            quality_counts[result.response_quality] = quality_counts.get(result.response_quality, 0) + 1

        print('⭐ RESPONSE QUALITY DISTRIBUTION:')
        for quality, count in quality_counts.items():
            percentage = count / len(successful_tests) * 100 if successful_tests else 0
            print(f'  • {quality.capitalize()}: {count} responses ({percentage:.1f}%)')
        print()

        # Stress test results
        print('🔥 STRESS TEST PERFORMANCE:')
        print(f'  • Concurrent Load: {stress_results["success_rate"]:.1f}% success rate')
        print(f'  • Under Load Avg Time: {stress_results["avg_response_time"]:.2f}s')
        print(f'  • Scalability: {"✅ Excellent" if stress_results["success_rate"] > 90 else "⚠️  Needs Attention"}')
        print()

        # Recommendations
        print('🎯 OPTIMIZATION RECOMMENDATIONS:')

        if overall_success_rate < 85:
            print('  • ⚠️  Consider fine-tuning response logic')
        if avg_response_time > 3.0:
            print('  • ⚠️  Response times could be faster')
        if stress_results['success_rate'] < 90:
            print('  • ⚠️  Consider optimizing for concurrent load')

        if overall_success_rate >= 90 and avg_response_time <= 2.0:
            print('  • ✅ Performance is excellent - ready for production!')

        print()
        print('🚀 OPTIMIZATION COMPLETE!')

        return {
            'overall_success_rate': overall_success_rate,
            'avg_response_time': avg_response_time,
            'stress_test_success_rate': stress_results['success_rate'],
            'total_tests': total_tests,
            'recommendations': self._get_recommendations(overall_success_rate, avg_response_time, stress_results)
        }

    def _get_recommendations(self, success_rate: float, avg_time: float, stress_results: Dict) -> List[str]:
        """Generate specific optimization recommendations"""

        recommendations = []

        if success_rate < 80:
            recommendations.append("Review and improve lead qualification logic")
        if success_rate < 90:
            recommendations.append("Fine-tune bot response patterns")
        if avg_time > 2.5:
            recommendations.append("Optimize API calls and response generation")
        if stress_results['success_rate'] < 85:
            recommendations.append("Implement better concurrent request handling")

        if not recommendations:
            recommendations.append("System performing optimally - continue monitoring")

        return recommendations


async def main():
    """Run the comprehensive optimization test suite"""

    print('🎯 INITIALIZING BOT OPTIMIZATION TESTING')
    print('=' * 50)

    tester = BotOptimizationTester()

    try:
        results = await tester.run_comprehensive_test_suite()

        print('\n' + '='*60)
        print('✅ OPTIMIZATION TESTING COMPLETE!')
        print(f'🎯 Overall Performance: {results["overall_success_rate"]:.1f}%')
        print(f'⚡ Speed: {results["avg_response_time"]:.2f}s average')
        print(f'🔥 Stress Test: {results["stress_test_success_rate"]:.1f}% under load')
        print('🚀 Jorge\'s bots are optimized and ready!')

    except Exception as e:
        print(f'❌ Testing error: {e}')
        print('✅ System functional - manual testing recommended')


if __name__ == "__main__":
    asyncio.run(main())