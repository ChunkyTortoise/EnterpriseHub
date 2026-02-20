"""Objection response templates for the Jorge Seller Bot.

Phase 2.2: Multi-category objection handling with A/B testing support.

Each objection category has response templates at 4 graduation levels:
1. VALIDATE - Acknowledge the concern empathetically
2. DATA - Present market data and evidence
3. SOCIAL_PROOF - Share success stories and social proof
4. MARKET_TEST - Propose a low-risk market test or trial

Each template supports multiple variants for A/B testing to optimize
resolution rates across different seller personalities and objection types.
"""
from enum import Enum
from typing import Dict, List

from ghl_real_estate_ai.services.jorge.pricing_objection_engine import (
    ObjectionCategory,
    ObjectionType,
    ResponseGraduation,
)

# Response templates per objection TYPE per graduation level
# Multiple variants per template for A/B testing
OBJECTION_RESPONSE_TEMPLATES: Dict[ObjectionType, Dict[ResponseGraduation, List[str]]] = {
    # ========== PRICING CATEGORY ==========
    ObjectionType.PRICING_GENERAL: {
        ResponseGraduation.VALIDATE: [
            "I completely understand your concern about costs. Selling a home is a significant financial decision, and you want to make sure every dollar counts.",
            "Budget is always an important consideration. Let's talk about what you're looking to accomplish and how we can structure this to work for you.",
            "I appreciate you being upfront about pricing. It's important that we're aligned on value from the start.",
        ],
        ResponseGraduation.DATA: [
            "Let me break down the numbers. In Rancho Cucamonga, homes listed with full-service agents sell for an average of {price_premium}% more than discount listings, which typically covers the commission difference and then some.",
            "Here's what the data shows: professionally marketed homes in your area spend {avg_days_on_market} fewer days on market and receive {avg_offers} more offers on average, creating competitive bidding that drives up the final price.",
            "The real cost isn't the commission—it's leaving money on the table. Underpriced or poorly marketed homes in this area cost sellers an average of ${lost_value} in lost equity.",
        ],
        ResponseGraduation.SOCIAL_PROOF: [
            "A recent seller on {nearby_street} was considering a discount broker to save on commission. We ran the numbers, and my full marketing package got them ${additional_proceeds} more than they would have netted with the discount option.",
            "I helped three sellers in your neighborhood this year who had similar concerns. All three netted more after my commission than their neighbors who used discount services. I'm happy to share those examples.",
            "Sellers who work with me get access to my exclusive buyer network, professional staging consultation, and targeted marketing that reaches serious buyers. Recent clients averaged {days_to_offer} days to first offer.",
        ],
        ResponseGraduation.MARKET_TEST: [
            "Here's what I propose: let me prepare a no-obligation market analysis showing you the projected net proceeds with different pricing and commission structures. You'll see exactly what you'd walk away with under each scenario.",
            "I offer a performance guarantee. If we don't get you a qualified offer within {guarantee_days} days, we can renegotiate the terms or you can walk away—no hard feelings, no long-term commitment.",
            "Let's start with a 90-day listing agreement. If you're not seeing the results and activity I promise, you can cancel after the first 30 days. I'm confident you'll see the value.",
        ],
    },

    # ========== TIMING CATEGORY ==========
    ObjectionType.TIMING_NOT_READY: {
        ResponseGraduation.VALIDATE: [
            "I appreciate you being honest about where you are in the process. There's never a rush when it comes to something this important.",
            "Timing is everything, and I completely respect that you're not ready to move forward right now. That's actually a sign of good decision-making.",
            "I understand—selling a home is a big step, and it makes sense to make sure you're ready. There's no pressure here.",
        ],
        ResponseGraduation.DATA: [
            "Let me share some timing context. Right now we're in {market_season} in Rancho Cucamonga, which historically sees {seasonal_activity}. The next {upcoming_season} typically brings {upcoming_trend}.",
            "Here's what the data shows: homes that go on the market in the next {optimal_window} weeks tend to sell {time_advantage} faster and for {price_advantage}% more. Inventory is currently {inventory_level}.",
            "Carrying costs add up. Your monthly costs (mortgage, taxes, insurance, maintenance) are roughly ${monthly_cost}. Every month you wait costs ${monthly_cost} plus opportunity cost on your next move.",
        ],
        ResponseGraduation.SOCIAL_PROOF: [
            "I had a seller last year in {nearby_area} who wanted to wait for spring. We did the math on carrying costs versus potential price increase, and they decided to list in February. Sold in {days_to_sale} days for ${sale_price}, and they had no competition from other listings.",
            "Sellers who wait for 'perfect timing' often find that the market has shifted by then. I've seen {wait_outcome_stat}% of sellers who waited 6+ months actually receive lower offers than if they'd listed immediately.",
            "Three of my recent sellers were initially hesitant about timing. All three ended up glad they moved forward—less competition, motivated buyers, and they're now settled in their new homes.",
        ],
        ResponseGraduation.MARKET_TEST: [
            "Here's an option: let's prepare your home for market now, so when you're ready, we can go live within 48 hours. I'll do the staging consultation and photography prep—no commitment until you give me the green light.",
            "What if we did this: I'll prepare a detailed market analysis and pricing strategy now. When you're ready—whether that's 30 days or 90 days—you'll have everything in place to move quickly.",
            "Let me put together a custom timeline based on your ideal move date. We'll work backward from when you want to be in your new place, and I'll show you exactly when we need to list to hit that target.",
        ],
    },

    # ========== COMPETITION CATEGORY ==========
    ObjectionType.COMPETITION_SHOPPING: {
        ResponseGraduation.VALIDATE: [
            "Absolutely, you should interview other agents! This is an important decision, and you deserve to find the right fit. I'm confident you'll find that I bring a unique approach to selling homes in this market.",
            "I encourage you to shop around. In fact, I think it's a great idea. When you compare what I offer, I think you'll see why my clients consistently choose to work with me.",
            "That makes total sense. You're making a smart move by comparing agents. I'd be doing the same thing in your shoes.",
        ],
        ResponseGraduation.DATA: [
            "Here's what I'd suggest you ask other agents: What's your average days on market? How many homes in this price range have you sold in the past 12 months? What's your list-to-sale price ratio? Mine are {dom}, {homes_sold}, and {list_sale_ratio}.",
            "When you're comparing agents, make sure you're comparing apples to apples. Ask about their marketing budget, staging support, photographer quality, and buyer network reach. I invest ${marketing_budget} per listing on average.",
            "The numbers speak for themselves. My listings in Rancho Cucamonga sell for an average of {price_premium}% over list price and spend {days_advantage} fewer days on market than the area average.",
        ],
        ResponseGraduation.SOCIAL_PROOF: [
            "I compete for business every day, and I welcome the comparison. Here's what sets me apart: {unique_value_prop}. My last {recent_count} sellers all had multiple offers within {offer_timeline}.",
            "When sellers compare me to other agents, they typically notice three things: my targeted marketing reach, my staging expertise, and my buyer network that's already pre-qualified and actively looking.",
            "I've won business from sellers who interviewed 3-5 agents. What they tell me is that I bring a level of market data, strategic pricing, and hands-on support that others don't match. Here are some recent testimonials: {testimonial_snippet}",
        ],
        ResponseGraduation.MARKET_TEST: [
            "Here's what I'll do: give me 15 minutes to show you my marketing plan and recent sales results. If you're not impressed, no hard feelings. But I think you'll see why my clients choose to work exclusively with me.",
            "Let me prepare a custom marketing presentation for your home specifically—not a generic template, but a real strategy. Then you can compare what I'm offering against the other agents you're considering.",
            "I'll make this easy for you. Here's a side-by-side comparison checklist you can use when evaluating agents. I'm confident that when you compare what each agent offers, I'll come out on top.",
        ],
    },

    # ========== TRUST CATEGORY ==========
    ObjectionType.TRUST_CREDIBILITY: {
        ResponseGraduation.VALIDATE: [
            "That's a very fair concern. You're about to trust someone with one of your biggest assets—you should absolutely know who you're working with and what they've accomplished.",
            "I completely understand. Trust is earned, not given. Let me share more about my background and track record so you can feel confident about working together.",
            "You're right to ask. Choosing an agent is a big decision, and you deserve transparency about who I am and what I've achieved in this market.",
        ],
        ResponseGraduation.DATA: [
            "I've been selling real estate in Rancho Cucamonga for {years_experience} years. In that time, I've closed {total_sales} transactions worth ${total_volume} in sales volume. My average seller rating is {avg_rating}/5.",
            "Here are my credentials: {certifications}. I'm also a member of {professional_orgs}. In the past 12 months alone, I've sold {recent_sales} homes in your area with an average DOM of {recent_dom}.",
            "Let me share some numbers. My list-to-sale price ratio is {list_sale_ratio}, which means my clients get {ratio_percent}% of their asking price on average. The area average is {area_average}.",
        ],
        ResponseGraduation.SOCIAL_PROOF: [
            "I'd love to share some client testimonials. Here's what {client_name} from {nearby_area} said: '{testimonial}'. I can also provide references from recent sellers who are happy to speak with you.",
            "My reviews speak for themselves: {review_summary}. You can find all of them on {review_platforms}. I also have video testimonials from sellers who were initially skeptical and ended up very happy.",
            "I'm active in the local community. You might have seen me at {local_involvement}. I'm not just an agent who parachutes in—I live here, I raise my family here, and my reputation matters to me.",
        ],
        ResponseGraduation.MARKET_TEST: [
            "Here's what I suggest: let's start with a no-obligation market analysis. I'll show you how I'd position and market your home, and you can judge for yourself whether I know this market.",
            "I'd be happy to provide references from {reference_count} recent sellers in your neighborhood. Talk to them directly about their experience working with me, and then you can decide.",
            "Let me earn your trust with results. I'll provide a detailed competitive market analysis, a custom marketing plan, and staging recommendations—all for free. If you're not impressed, there's no obligation to move forward.",
        ],
    },

    # ========== AUTHORITY CATEGORY ==========
    ObjectionType.AUTHORITY_DECISION_MAKER: {
        ResponseGraduation.VALIDATE: [
            "Absolutely, this is a decision you should make together. I'd be happy to include your {partner_relation} in our next conversation so everyone's on the same page.",
            "That makes perfect sense. Big decisions like this should involve everyone who has a stake. When would be a good time for all of us to talk?",
            "I completely understand. This is a major decision, and you want to make sure you have buy-in from everyone involved. Let's set up a time when we can all discuss this together.",
        ],
        ResponseGraduation.DATA: [
            "When we meet with your {partner_relation}, I'll bring a complete market analysis, pricing strategy, and projected net proceeds. That way everyone has the same information to make an informed decision.",
            "I've prepared a detailed overview that includes comps, pricing strategy, marketing plan, and timeline. It's designed to address the questions your {partner_relation} will likely have.",
            "Here's what I'll cover when we all meet: current market conditions, pricing strategy, marketing approach, timeline, and projected outcomes. I want everyone to feel confident about the plan.",
        ],
        ResponseGraduation.SOCIAL_PROOF: [
            "I work with couples and families all the time. What I've found is that when everyone's involved from the start, the selling process goes much more smoothly. I make sure all decision-makers feel heard and informed.",
            "Many of my clients involve their {partner_relation} in the initial consultation. It's actually one of my favorite parts of the process—answering questions from different perspectives helps us build a stronger strategy.",
            "I recently worked with a family where the adult children were involved in the decision. We scheduled a group call, I walked everyone through the plan, and it made the whole process smoother because everyone was aligned.",
        ],
        ResponseGraduation.MARKET_TEST: [
            "Let's schedule a consultation that works for everyone. I'll present the full strategy, answer any questions, and we can make sure all decision-makers are comfortable before moving forward.",
            "Here's an idea: I'll send over a detailed summary of what we've discussed—market analysis, pricing recommendation, marketing plan—so your {partner_relation} can review it before we meet. That way we can hit the ground running.",
            "Why don't we do a quick video call with your {partner_relation}? I can walk through the key points in 15-20 minutes, answer their questions, and we can decide together if it makes sense to proceed.",
        ],
    },

    # ========== VALUE CATEGORY ==========
    ObjectionType.VALUE_PROPOSITION: {
        ResponseGraduation.VALIDATE: [
            "Great question. You should absolutely know what you're getting for your investment. Let me walk you through exactly what I provide and how it translates to results.",
            "I'm glad you asked. It's important that you understand the full value of what I offer. This isn't just about listing your home—it's about positioning it for maximum return.",
            "That's the right question to ask. Let me be very clear about what's included in my service and why it makes a difference in your final sale price.",
        ],
        ResponseGraduation.DATA: [
            "Here's what's included: {service_list}. My marketing budget per listing averages ${marketing_budget}, and I invest in professional photography, 3D virtual tours, targeted online advertising, and open house events.",
            "My full-service package includes: pre-listing consultation, staging support (up to ${staging_value}), professional photography and videography, MLS listing with {mls_reach} exposure, social media advertising, buyer agent outreach, and weekly updates.",
            "What makes me different: {differentiator_list}. I also provide {unique_service}, which has resulted in {result_stat}% faster sales for my clients.",
        ],
        ResponseGraduation.SOCIAL_PROOF: [
            "My clients consistently tell me that what sets me apart is {client_feedback}. Here's a recent testimonial: '{testimonial_quote}'",
            "Sellers who work with me get access to my exclusive buyer network of {buyer_count} pre-qualified buyers actively searching in Rancho Cucamonga. That head start often leads to offers before the home even hits MLS.",
            "I've sold {recent_sales} homes in your area in the past year. All of them received multiple offers, and {stat}% sold above asking price. That's the kind of results my marketing and positioning strategy delivers.",
        ],
        ResponseGraduation.MARKET_TEST: [
            "Let me show you exactly what I'll do for your home. I'll prepare a custom marketing plan with sample ads, staging recommendations, and a pricing strategy. You'll see the full scope of what you're getting.",
            "Here's my portfolio of recent listings. You can see the photography quality, marketing materials, and final results. I'll walk you through what I did for each one and how we'd approach your home.",
            "I'll provide a detailed service agreement that outlines everything included—no surprises, no hidden costs. You'll know exactly what you're getting and what results to expect.",
        ],
    },

    # ========== LEGACY PRICING OBJECTIONS (from original engine) ==========
    # These remain for backward compatibility
    ObjectionType.LOSS_AVERSION: {
        ResponseGraduation.VALIDATE: [
            "I completely understand the concern about selling below what you paid. No one wants to feel like they're losing money on their home.",
        ],
        ResponseGraduation.DATA: [
            "Let me share some context. The Rancho Cucamonga market has shifted since you purchased. Current comparable sales in your area show a median of {median_price}. The gap between your purchase price and current market is about {gap_percent}%.",
        ],
        ResponseGraduation.SOCIAL_PROOF: [
            "Several homeowners in your area faced the same situation. Those who priced competitively from the start actually netted more—overpriced homes averaged {avg_days_overpriced} days on market and sold for {avg_reduction}% below their original asking price.",
        ],
        ResponseGraduation.MARKET_TEST: [
            "Here's what I'd suggest: let's price at {suggested_price} for 14 days as a market test. If we get strong showing activity and offers, we know we're in the right range. If not, we can adjust. No long-term commitment.",
        ],
    },

    ObjectionType.ANCHORING: {
        ResponseGraduation.VALIDATE: [
            "Those online estimates are a great starting point for research! It's smart to come prepared with that information.",
        ],
        ResponseGraduation.DATA: [
            "Online estimates use broad algorithms that can't account for your home's unique features. Zillow's own data shows their Zestimate has a median error rate of about 7%. For your home, that could mean a {error_range} difference.",
        ],
        ResponseGraduation.SOCIAL_PROOF: [
            "I recently helped a seller on {nearby_street} whose Zillow estimate was ${zestimate_example}. After a proper CMA, we listed at ${actual_list} and sold for ${actual_sold}.",
        ],
        ResponseGraduation.MARKET_TEST: [
            "Let's do this: I'll prepare a detailed CMA using actual closed sales in the last 90 days within a mile of your property. We can compare that side-by-side with the online estimate and find the right price together.",
        ],
    },

    ObjectionType.NEIGHBOR_COMP: {
        ResponseGraduation.VALIDATE: [
            "That's a great reference point! Knowing what nearby homes sold for is exactly the kind of research that helps.",
        ],
        ResponseGraduation.DATA: [
            "Let me pull up that sale. Comparable sales need to account for square footage, lot size, condition, and upgrades. Even on the same street, homes can differ by {typical_variance}% in value.",
        ],
        ResponseGraduation.SOCIAL_PROOF: [
            "When we look at the actual comparables, your home has {advantages} that the neighbor's didn't, but their home had {neighbor_advantages}. The adjusted comparison puts your home at {adjusted_value}.",
        ],
        ResponseGraduation.MARKET_TEST: [
            "I'd suggest we list at {suggested_price} and see how the market responds in the first two weeks. Buyer activity will tell us exactly where we stand relative to your neighbor's sale.",
        ],
    },

    ObjectionType.MARKET_DENIAL: {
        ResponseGraduation.VALIDATE: [
            "I appreciate that perspective. Timing the market is something every seller thinks about.",
        ],
        ResponseGraduation.DATA: [
            "Here's what the data shows for Rancho Cucamonga: {market_trend}. Meanwhile, your carrying costs (mortgage, taxes, insurance, maintenance) add up to roughly ${monthly_carrying}/month while you wait.",
        ],
        ResponseGraduation.SOCIAL_PROOF: [
            "Sellers who waited 6+ months in similar market conditions in this area typically saw {wait_outcome}. The carrying costs alone can offset any potential price gain.",
        ],
        ResponseGraduation.MARKET_TEST: [
            "Here's an option: let's get your home market-ready now and list at a strong price. If we don't get the right offer in 30 days, we can reassess. You'll have real market data instead of predictions.",
        ],
    },

    ObjectionType.IMPROVEMENT_OVERVALUE: {
        ResponseGraduation.VALIDATE: [
            "Those improvements clearly show you've taken great care of your home! A remodeled {improvement_type} is definitely a selling point.",
        ],
        ResponseGraduation.DATA: [
            "Renovation ROI varies by project. According to the latest Cost vs. Value report, a {improvement_type} remodel in our market typically returns about {roi_percent}% of the investment. Your ${spent} investment adds roughly ${value_add} in market value.",
        ],
        ResponseGraduation.SOCIAL_PROOF: [
            "I see this often. A recent seller invested ${similar_spent} in upgrades and we were able to capture ${similar_recovered} of that in the final price. The key is positioning those upgrades as differentiators.",
        ],
        ResponseGraduation.MARKET_TEST: [
            "Let's highlight your {improvement_type} as a premium feature in our marketing. I'll prepare a targeted marketing plan that showcases these upgrades to buyers who specifically value them.",
        ],
    },
}


def get_response_template(
    objection_type: ObjectionType,
    graduation_level: ResponseGraduation,
    variant_index: int = 0,
) -> str:
    """Get a response template for an objection type and graduation level.

    Args:
        objection_type: The specific objection type.
        graduation_level: The current graduation level.
        variant_index: Which variant to use for A/B testing (default: 0).

    Returns:
        Response template string with placeholders for market data.
    """
    templates = OBJECTION_RESPONSE_TEMPLATES.get(objection_type, {})
    variants = templates.get(graduation_level, [""])

    if not variants:
        return ""

    # Wrap variant_index to handle out-of-bounds
    variant_idx = variant_index % len(variants)
    return variants[variant_idx]


def get_variant_count(
    objection_type: ObjectionType,
    graduation_level: ResponseGraduation,
) -> int:
    """Get the number of A/B test variants available for an objection type.

    Args:
        objection_type: The specific objection type.
        graduation_level: The current graduation level.

    Returns:
        Number of variants available (minimum 1).
    """
    templates = OBJECTION_RESPONSE_TEMPLATES.get(objection_type, {})
    variants = templates.get(graduation_level, [""])
    return max(1, len(variants))
