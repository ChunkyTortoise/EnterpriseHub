#!/usr/bin/env python3
"""
National Market Expansion Demo Script

Demonstrates the complete National Market Expansion system including:
- National Market Registry and Fortune 500 corporate headquarters mapping
- Corporate Relocation Service for multi-city employee housing
- National Market Intelligence for cross-market analytics
- Market configuration validation for Denver, Phoenix, and Seattle

This demo validates the $1M+ annual revenue enhancement capabilities
through enterprise partnerships and nationwide market expansion.

Usage:
    python demo_national_market_expansion.py

Author: EnterpriseHub AI
Created: 2026-01-18
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import Dict, List, Any

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from ghl_real_estate_ai.markets.national_registry import (
    get_national_market_registry,
    CorporateHeadquarters,
    CorporatePartnerTier
)
from ghl_real_estate_ai.services.corporate_relocation_service import (
    get_corporate_relocation_service,
    EmployeeLevel
)
from ghl_real_estate_ai.services.national_market_intelligence import (
    get_national_market_intelligence
)


class NationalExpansionDemo:
    """Demo class for National Market Expansion system"""

    def __init__(self):
        """Initialize demo components"""
        self.national_registry = None
        self.corporate_service = None
        self.market_intelligence = None
        self.demo_results = {}

    async def run_complete_demo(self) -> Dict[str, Any]:
        """Run complete national expansion demo"""
        print("🚀 Starting National Market Expansion Demo")
        print("=" * 60)

        try:
            # Initialize services
            await self._initialize_services()

            # Run demo scenarios
            await self._demo_market_configurations()
            await self._demo_corporate_headquarters_mapping()
            await self._demo_corporate_relocation_workflow()
            await self._demo_multi_city_coordination()
            await self._demo_cross_market_analytics()
            await self._demo_national_market_intelligence()
            await self._demo_expansion_opportunities()

            # Generate summary
            self._generate_demo_summary()

            print("\n✅ National Market Expansion Demo Completed Successfully!")
            return self.demo_results

        except Exception as e:
            print(f"\n❌ Demo failed: {str(e)}")
            raise

    async def _initialize_services(self):
        """Initialize all national expansion services"""
        print("\n📋 Initializing National Expansion Services...")

        try:
            # Initialize services
            self.national_registry = get_national_market_registry()
            self.corporate_service = get_corporate_relocation_service()
            self.market_intelligence = get_national_market_intelligence()

            # Perform health checks
            health_checks = {
                'national_registry': self.national_registry.health_check(),
                'corporate_service': self.corporate_service.health_check(),
                'market_intelligence': self.market_intelligence.health_check()
            }

            for service, health in health_checks.items():
                status = health.get('status', 'unknown')
                print(f"   {service}: {status}")

            self.demo_results['initialization'] = {
                'status': 'success',
                'services_initialized': len(health_checks),
                'health_checks': health_checks
            }

            print("✅ All services initialized successfully")

        except Exception as e:
            print(f"❌ Service initialization failed: {str(e)}")
            raise

    async def _demo_market_configurations(self):
        """Demo new market configurations (Denver, Phoenix, Seattle)"""
        print("\n🏙️  Demonstrating Market Configurations...")

        try:
            # Get available markets
            markets = self.national_registry.base_registry.list_markets()
            print(f"   📊 Total markets available: {len(markets)}")

            # Validate new markets
            new_markets = ['denver', 'phoenix', 'seattle']
            validated_markets = []

            for market_id in new_markets:
                config = self.national_registry.base_registry.get_market_config(market_id)
                if config:
                    validated_markets.append({
                        'market_id': market_id,
                        'market_name': config.get('market_name', 'Unknown'),
                        'market_type': config.get('market_type', 'Unknown'),
                        'state': config.get('state', 'Unknown'),
                        'median_home_price': config.get('median_home_price', 0),
                        'neighborhoods_count': len(config.get('neighborhoods', [])),
                        'employers_count': len(config.get('employers', []))
                    })
                    print(f"   ✅ {config.get('market_name', market_id)}: "
                          f"{config.get('market_type', 'unknown')} market")
                else:
                    print(f"   ❌ {market_id}: Configuration not found")

            self.demo_results['market_configurations'] = {
                'total_markets': len(markets),
                'new_markets_added': len(validated_markets),
                'validated_markets': validated_markets
            }

            print(f"✅ Successfully validated {len(validated_markets)} new markets")

        except Exception as e:
            print(f"❌ Market configuration demo failed: {str(e)}")
            raise

    async def _demo_corporate_headquarters_mapping(self):
        """Demo Fortune 500 corporate headquarters mapping"""
        print("\n🏢 Demonstrating Corporate Headquarters Mapping...")

        try:
            # Get Fortune 500 companies in registry
            corporations = list(self.national_registry.corporate_headquarters.keys())
            print(f"   📈 Fortune 500 companies mapped: {len(corporations)}")

            # Demo major tech companies
            major_companies = []
            for company_id in ['amazon', 'microsoft', 'google', 'boeing', 'intel']:
                program = await self.national_registry.get_corporate_relocation_program(company_id)
                if program:
                    company_info = program['company_info']
                    relocation_info = program['relocation_program']

                    major_companies.append({
                        'company': company_info['name'],
                        'industry': company_info['industry'],
                        'partnership_tier': company_info['partnership_tier'],
                        'annual_volume': relocation_info['annual_volume'],
                        'preferred_markets': relocation_info['preferred_markets'],
                        'average_budget': relocation_info['average_budget']
                    })

                    print(f"   🎯 {company_info['name']}: "
                          f"{relocation_info['annual_volume']} relocations/year, "
                          f"${relocation_info['average_budget']:,} avg budget")

            self.demo_results['corporate_mapping'] = {
                'total_corporations': len(corporations),
                'major_companies_profiled': len(major_companies),
                'company_details': major_companies
            }

            print(f"✅ Successfully mapped {len(corporations)} corporate headquarters")

        except Exception as e:
            print(f"❌ Corporate mapping demo failed: {str(e)}")
            raise

    async def _demo_corporate_relocation_workflow(self):
        """Demo complete corporate relocation workflow"""
        print("\n🚚 Demonstrating Corporate Relocation Workflow...")

        try:
            # Sample employee relocation request
            sample_employees = [
                {
                    'company': 'Amazon',
                    'employee': {
                        'name': 'Sarah Chen',
                        'email': 'sarah.chen@amazon.com',
                        'level': 'vp_director',
                        'current_location': 'Austin, TX',
                        'family_size': 3
                    },
                    'requirements': {
                        'target_market': 'seattle',
                        'start_date': (date.today() + timedelta(days=90)).isoformat(),
                        'timeline_requirement': 'flexible',
                        'budget_min': 800000,
                        'budget_max': 1200000,
                        'special_requirements': ['spouse_career_assistance', 'private_school_search'],
                        'housing_preferences': {
                            'property_type': 'single_family',
                            'bedrooms': 4,
                            'school_rating_min': 9.0
                        }
                    }
                },
                {
                    'company': 'Microsoft',
                    'employee': {
                        'name': 'David Rodriguez',
                        'email': 'david.rodriguez@microsoft.com',
                        'level': 'senior_manager',
                        'current_location': 'Dallas, TX',
                        'family_size': 4
                    },
                    'requirements': {
                        'target_market': 'denver',
                        'start_date': (date.today() + timedelta(days=120)).isoformat(),
                        'timeline_requirement': 'expedited',
                        'budget_min': 600000,
                        'budget_max': 850000,
                        'special_requirements': ['cultural_integration'],
                        'housing_preferences': {
                            'property_type': 'single_family',
                            'bedrooms': 5,
                            'school_rating_min': 8.5
                        }
                    }
                }
            ]

            created_requests = []

            for sample in sample_employees:
                # Create relocation request
                request_id = await self.corporate_service.create_relocation_request(
                    sample['company'],
                    sample['employee'],
                    sample['requirements']
                )

                # Get request status
                status = await self.corporate_service.get_relocation_status(request_id)

                created_requests.append({
                    'request_id': request_id,
                    'company': sample['company'],
                    'employee_name': sample['employee']['name'],
                    'target_market': sample['requirements']['target_market'],
                    'service_tier': status['service_details']['package_tier'],
                    'estimated_cost': status['budget_information']['estimated_total_cost'],
                    'assigned_specialist': status['service_details']['assigned_specialist']
                })

                print(f"   📝 Created request {request_id} for {sample['employee']['name']}")
                print(f"      Target: {sample['requirements']['target_market']}")
                print(f"      Service Tier: {status['service_details']['package_tier']}")
                print(f"      Estimated Cost: ${status['budget_information']['estimated_total_cost']:,.0f}")

            self.demo_results['relocation_workflow'] = {
                'requests_created': len(created_requests),
                'request_details': created_requests
            }

            print(f"✅ Successfully created {len(created_requests)} relocation requests")

        except Exception as e:
            print(f"❌ Relocation workflow demo failed: {str(e)}")
            raise

    async def _demo_multi_city_coordination(self):
        """Demo multi-city coordination for large corporate moves"""
        print("\n🌐 Demonstrating Multi-City Coordination...")

        try:
            # Sample multi-city project
            project_details = {
                'project_name': 'Tech Expansion Initiative 2026',
                'affected_markets': ['denver', 'phoenix', 'seattle'],
                'employee_count': 250,
                'coordination_type': 'office_expansion',
                'timeline': {
                    'project_start': (date.today() + timedelta(days=30)).isoformat(),
                    'denver_phase': (date.today() + timedelta(days=90)).isoformat(),
                    'phoenix_phase': (date.today() + timedelta(days=150)).isoformat(),
                    'seattle_phase': (date.today() + timedelta(days=210)).isoformat()
                },
                'budget_total': 25000000.0,
                'project_manager': 'Jennifer Walsh'
            }

            # Create multi-city coordination
            coordination_id = await self.corporate_service.create_multi_city_coordination(
                'Amazon',
                project_details
            )

            print(f"   🎯 Created coordination project: {coordination_id}")
            print(f"      Project: {project_details['project_name']}")
            print(f"      Markets: {', '.join(project_details['affected_markets'])}")
            print(f"      Employees: {project_details['employee_count']}")
            print(f"      Budget: ${project_details['budget_total']:,.0f}")

            self.demo_results['multi_city_coordination'] = {
                'coordination_id': coordination_id,
                'project_name': project_details['project_name'],
                'affected_markets': project_details['affected_markets'],
                'employee_count': project_details['employee_count'],
                'budget_total': project_details['budget_total']
            }

            print("✅ Successfully created multi-city coordination project")

        except Exception as e:
            print(f"❌ Multi-city coordination demo failed: {str(e)}")
            raise

    async def _demo_cross_market_analytics(self):
        """Demo cross-market analytics and migration insights"""
        print("\n📊 Demonstrating Cross-Market Analytics...")

        try:
            # Sample cross-market comparisons
            market_pairs = [
                ('austin', 'denver'),
                ('dallas', 'seattle'),
                ('houston', 'phoenix')
            ]

            migration_insights = []

            for source, target in market_pairs:
                insights = await self.national_registry.get_cross_market_insights(source, target)

                if insights:
                    migration_insights.append({
                        'route': f"{source} → {target}",
                        'migration_volume': insights.migration_volume,
                        'salary_delta': insights.average_salary_delta,
                        'col_comparison': insights.cost_of_living_comparison,
                        'success_probability': insights.success_probability,
                        'driving_factors': insights.corporate_driving_factors[:3],
                        'peak_season': max(insights.seasonal_patterns.items(), key=lambda x: x[1])[0]
                    })

                    print(f"   📈 {source.title()} → {target.title()}:")
                    print(f"      Annual migration: {insights.migration_volume}")
                    print(f"      Salary delta: {insights.average_salary_delta:+.1f}%")
                    print(f"      Success rate: {insights.success_probability:.1%}")

            self.demo_results['cross_market_analytics'] = {
                'comparisons_analyzed': len(migration_insights),
                'migration_insights': migration_insights
            }

            print(f"✅ Successfully analyzed {len(migration_insights)} market migration routes")

        except Exception as e:
            print(f"❌ Cross-market analytics demo failed: {str(e)}")
            raise

    async def _demo_national_market_intelligence(self):
        """Demo national market intelligence overview"""
        print("\n🧠 Demonstrating National Market Intelligence...")

        try:
            # Generate national market overview
            overview = await self.market_intelligence.get_national_market_overview()

            print(f"   📊 National Summary:")
            summary = overview['summary']
            print(f"      Total Markets: {summary['total_markets']}")
            print(f"      Avg Opportunity Score: {summary['average_opportunity_score']:.1f}")
            print(f"      National Median Price: ${summary['national_median_price']:,.0f}")
            print(f"      Corporate Headquarters: {summary['total_corporate_headquarters']}")

            # Show top opportunities
            top_opportunities = overview['top_opportunities'][:3]
            print(f"\n   🎯 Top Market Opportunities:")
            for i, opp in enumerate(top_opportunities, 1):
                print(f"      {i}. {opp['market_name']} - Score: {opp['opportunity_score']:.1f}")
                print(f"         Trend: {opp['market_trend']}, Price: ${opp['median_home_price']:,.0f}")

            # Market trends
            trends = overview['market_trends']
            print(f"\n   📈 Market Trends:")
            print(f"      Growing markets: {trends['growth_markets']}")
            print(f"      Stable markets: {trends['stable_markets']}")
            print(f"      Avg appreciation: {trends['average_appreciation']:.1f}%")

            self.demo_results['market_intelligence'] = {
                'overview': overview['summary'],
                'top_opportunities': [opp['market_name'] for opp in top_opportunities],
                'market_trends': trends
            }

            print("✅ Successfully generated national market intelligence")

        except Exception as e:
            print(f"❌ Market intelligence demo failed: {str(e)}")
            raise

    async def _demo_expansion_opportunities(self):
        """Demo expansion opportunity analysis"""
        print("\n🚀 Demonstrating Expansion Opportunities...")

        try:
            # Get expansion opportunities
            opportunities = await self.national_registry.get_expansion_opportunities()

            print(f"   💰 Revenue Enhancement Opportunities:")
            total_revenue_potential = 0

            for opp in opportunities[:5]:  # Top 5 opportunities
                total_revenue_potential += opp.estimated_annual_revenue_potential
                print(f"      🎯 {opp.market_name}:")
                print(f"         Priority: {opp.expansion_priority}/10")
                print(f"         Revenue Potential: ${opp.estimated_annual_revenue_potential:,.0f}")
                print(f"         ROI Projection: {opp.roi_projection:.1f}x")
                print(f"         Timeline: {opp.expansion_timeline}")
                print(f"         Investment: ${opp.investment_required:,.0f}")

            print(f"\n   📊 Total Revenue Enhancement Target: ${total_revenue_potential:,.0f}")

            self.demo_results['expansion_opportunities'] = {
                'opportunities_identified': len(opportunities),
                'total_revenue_potential': total_revenue_potential,
                'top_markets': [opp.market_name for opp in opportunities[:5]],
                'average_roi': sum(opp.roi_projection for opp in opportunities) / len(opportunities) if opportunities else 0
            }

            print(f"✅ Successfully identified {len(opportunities)} expansion opportunities")

        except Exception as e:
            print(f"❌ Expansion opportunities demo failed: {str(e)}")
            raise

    def _generate_demo_summary(self):
        """Generate comprehensive demo summary"""
        print("\n📋 DEMO SUMMARY REPORT")
        print("=" * 60)

        try:
            # Calculate total revenue impact
            total_revenue = 0
            if 'expansion_opportunities' in self.demo_results:
                total_revenue = self.demo_results['expansion_opportunities']['total_revenue_potential']

            # Count total features demonstrated
            features_demo = {
                'Market Configurations': self.demo_results.get('market_configurations', {}).get('new_markets_added', 0),
                'Corporate Headquarters': self.demo_results.get('corporate_mapping', {}).get('total_corporations', 0),
                'Relocation Requests': self.demo_results.get('relocation_workflow', {}).get('requests_created', 0),
                'Multi-City Projects': 1 if 'multi_city_coordination' in self.demo_results else 0,
                'Cross-Market Routes': self.demo_results.get('cross_market_analytics', {}).get('comparisons_analyzed', 0),
                'Expansion Opportunities': self.demo_results.get('expansion_opportunities', {}).get('opportunities_identified', 0)
            }

            print(f"🎯 NATIONAL EXPANSION CAPABILITIES:")
            for feature, count in features_demo.items():
                print(f"   ✅ {feature}: {count}")

            print(f"\n💰 REVENUE ENHANCEMENT TARGET:")
            print(f"   📈 Total Annual Revenue Potential: ${total_revenue:,.0f}")
            print(f"   🎯 Target Achievement: {'✅ $1M+ Target Met' if total_revenue >= 1000000 else '⚠️ Below $1M Target'}")

            print(f"\n🏢 ENTERPRISE PARTNERSHIPS:")
            if 'corporate_mapping' in self.demo_results:
                companies = self.demo_results['corporate_mapping']['major_companies_profiled']
                print(f"   🤝 Fortune 500 Companies: {companies}")

            print(f"\n🌐 MULTI-MARKET COORDINATION:")
            if 'multi_city_coordination' in self.demo_results:
                coordination = self.demo_results['multi_city_coordination']
                print(f"   🚚 Project Scale: {coordination['employee_count']} employees")
                print(f"   💵 Project Value: ${coordination['budget_total']:,.0f}")

            print(f"\n📊 MARKET INTELLIGENCE:")
            if 'market_intelligence' in self.demo_results:
                intelligence = self.demo_results['market_intelligence']['overview']
                print(f"   🏙️  Total Markets: {intelligence['total_markets']}")
                print(f"   🎯 Avg Opportunity Score: {intelligence['average_opportunity_score']:.1f}")

            # Overall assessment
            success_score = sum(1 for count in features_demo.values() if count > 0)
            total_features = len(features_demo)

            print(f"\n🎖️  OVERALL ASSESSMENT:")
            print(f"   📈 Features Demonstrated: {success_score}/{total_features} ({success_score/total_features:.1%})")
            print(f"   💰 Revenue Target: {'✅ ACHIEVED' if total_revenue >= 1000000 else '❌ NOT MET'}")
            print(f"   🚀 System Status: {'🟢 PRODUCTION READY' if success_score >= total_features * 0.8 else '🟡 NEEDS REVIEW'}")

            self.demo_results['summary'] = {
                'features_demonstrated': success_score,
                'total_features': total_features,
                'success_rate': success_score / total_features,
                'revenue_potential': total_revenue,
                'target_achieved': total_revenue >= 1000000,
                'production_ready': success_score >= total_features * 0.8
            }

        except Exception as e:
            print(f"❌ Summary generation failed: {str(e)}")
            self.demo_results['summary'] = {'error': str(e)}


async def main():
    """Main demo execution function"""
    print("🌟 Jorge's National Market Expansion System")
    print("💼 Enterprise Real Estate AI Platform")
    print("🎯 Targeting $1M+ Annual Revenue Enhancement")
    print("\n" + "=" * 60)

    demo = NationalExpansionDemo()

    try:
        # Run complete demo
        results = await demo.run_complete_demo()

        # Save results to file
        results_file = Path(__file__).parent / "demo_results_national_expansion.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        print(f"\n📄 Demo results saved to: {results_file}")

        # Return success code
        return 0

    except Exception as e:
        print(f"\n💥 DEMO FAILED: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys

    # Run the demo
    exit_code = asyncio.run(main())
    sys.exit(exit_code)