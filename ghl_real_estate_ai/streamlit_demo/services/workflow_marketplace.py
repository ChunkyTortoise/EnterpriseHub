"""
Workflow Marketplace Service
Browse, search, and install pre-built workflow templates

This service provides a marketplace for workflow templates where users can:
- Browse templates by category
- Search and filter templates
- View ratings and reviews
- Install templates with one click
- Rate and review templates
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum


class TemplateSortBy(Enum):
    """Sort options for templates"""
    POPULAR = "popular"  # Most downloads
    TRENDING = "trending"  # Recent downloads
    NEWEST = "newest"  # Recently added
    RATING = "rating"  # Highest rated
    NAME = "name"  # Alphabetical


@dataclass
class TemplateReview:
    """User review for a template"""
    review_id: str
    template_id: str
    user_id: str
    rating: float
    comment: str
    created_at: str
    helpful_count: int = 0


@dataclass
class MarketplaceTemplate:
    """Template in the marketplace"""
    id: str
    name: str
    description: str
    category: str
    author: str
    version: str
    icon: str
    tags: List[str]
    rating: float
    reviews_count: int
    downloads_count: int
    price: float
    is_premium: bool
    is_featured: bool
    trigger: str
    steps_count: int
    estimated_time: str
    difficulty: str
    variables: List[Dict[str, Any]]
    screenshots: List[str]
    documentation: str
    created_at: str
    updated_at: str


class WorkflowMarketplaceService:
    """Service for browsing and managing workflow templates marketplace"""
    
    def __init__(self, data_dir: str = "data/marketplace"):
        self.data_dir = Path(data_dir)
        self.templates: Dict[str, MarketplaceTemplate] = {}
        self.categories: List[Dict[str, Any]] = []
        self.reviews: Dict[str, List[TemplateReview]] = {}
        self._load_data()
    
    def _load_data(self):
        """Load templates and categories from disk"""
        # Load templates
        templates_file = self.data_dir / "templates.json"
        if templates_file.exists():
            with open(templates_file, 'r') as f:
                data = json.load(f)
                for t in data.get('templates', []):
                    template = MarketplaceTemplate(**t)
                    self.templates[template.id] = template
        
        # Load categories
        categories_file = self.data_dir / "categories.json"
        if categories_file.exists():
            with open(categories_file, 'r') as f:
                data = json.load(f)
                self.categories = data.get('categories', [])
        
        # Load reviews
        reviews_file = self.data_dir / "reviews.json"
        if reviews_file.exists():
            with open(reviews_file, 'r') as f:
                data = json.load(f)
                for r in data.get('reviews', []):
                    review = TemplateReview(**r)
                    if review.template_id not in self.reviews:
                        self.reviews[review.template_id] = []
                    self.reviews[review.template_id].append(review)
    
    def browse_templates(
        self,
        category: Optional[str] = None,
        search_query: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_rating: Optional[float] = None,
        max_price: Optional[float] = None,
        difficulty: Optional[str] = None,
        sort_by: str = TemplateSortBy.POPULAR.value,
        limit: int = 50
    ) -> List[MarketplaceTemplate]:
        """
        Browse templates with filtering and sorting
        
        Args:
            category: Filter by category (e.g., "lead_nurturing")
            search_query: Search in name and description
            tags: Filter by tags
            min_rating: Minimum rating (0-5)
            max_price: Maximum price (0 for free only)
            difficulty: Filter by difficulty level
            sort_by: Sort order
            limit: Maximum results
        
        Returns:
            List of templates matching criteria
        """
        results = list(self.templates.values())
        
        # Apply filters
        if category:
            results = [t for t in results if t.category == category]
        
        if search_query:
            query_lower = search_query.lower()
            results = [
                t for t in results
                if query_lower in t.name.lower() 
                or query_lower in t.description.lower()
                or any(query_lower in tag.lower() for tag in t.tags)
            ]
        
        if tags:
            results = [
                t for t in results
                if any(tag in t.tags for tag in tags)
            ]
        
        if min_rating is not None:
            results = [t for t in results if t.rating >= min_rating]
        
        if max_price is not None:
            results = [t for t in results if t.price <= max_price]
        
        if difficulty:
            results = [t for t in results if t.difficulty == difficulty]
        
        # Sort results
        if sort_by == TemplateSortBy.POPULAR.value:
            results.sort(key=lambda t: t.downloads_count, reverse=True)
        elif sort_by == TemplateSortBy.RATING.value:
            results.sort(key=lambda t: t.rating, reverse=True)
        elif sort_by == TemplateSortBy.NEWEST.value:
            results.sort(key=lambda t: t.created_at, reverse=True)
        elif sort_by == TemplateSortBy.NAME.value:
            results.sort(key=lambda t: t.name)
        elif sort_by == TemplateSortBy.TRENDING.value:
            # Simple trending: featured + high recent downloads
            results.sort(
                key=lambda t: (t.is_featured, t.downloads_count / max((datetime.now() - datetime.fromisoformat(t.created_at.replace('Z', '+00:00'))).days, 1)),
                reverse=True
            )
        
        return results[:limit]
    
    def get_template_details(self, template_id: str) -> Optional[MarketplaceTemplate]:
        """Get detailed information about a specific template"""
        return self.templates.get(template_id)
    
    def get_template_reviews(self, template_id: str) -> List[TemplateReview]:
        """Get all reviews for a template"""
        return self.reviews.get(template_id, [])
    
    def search_templates(self, query: str, limit: int = 20) -> List[MarketplaceTemplate]:
        """
        Search templates by keyword
        
        Args:
            query: Search query
            limit: Maximum results
        
        Returns:
            List of matching templates
        """
        return self.browse_templates(search_query=query, limit=limit)
    
    def get_popular_templates(self, limit: int = 10) -> List[MarketplaceTemplate]:
        """Get most popular templates by downloads"""
        return self.browse_templates(sort_by=TemplateSortBy.POPULAR.value, limit=limit)
    
    def get_trending_templates(self, limit: int = 10) -> List[MarketplaceTemplate]:
        """Get trending templates"""
        return self.browse_templates(sort_by=TemplateSortBy.TRENDING.value, limit=limit)
    
    def get_featured_templates(self, limit: int = 10) -> List[MarketplaceTemplate]:
        """Get featured templates"""
        results = [t for t in self.templates.values() if t.is_featured]
        results.sort(key=lambda t: t.rating, reverse=True)
        return results[:limit]
    
    def get_free_templates(self, limit: int = 50) -> List[MarketplaceTemplate]:
        """Get all free templates"""
        return self.browse_templates(max_price=0, limit=limit)
    
    def get_premium_templates(self, limit: int = 50) -> List[MarketplaceTemplate]:
        """Get premium templates"""
        results = [t for t in self.templates.values() if t.is_premium]
        results.sort(key=lambda t: t.rating, reverse=True)
        return results[:limit]
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """Get all template categories"""
        return self.categories
    
    def get_category_templates(self, category_id: str) -> List[MarketplaceTemplate]:
        """Get all templates in a category"""
        return self.browse_templates(category=category_id)
    
    def add_review(
        self,
        template_id: str,
        user_id: str,
        rating: float,
        comment: str
    ) -> TemplateReview:
        """
        Add a review for a template
        
        Args:
            template_id: Template ID
            user_id: User ID
            rating: Rating (1-5)
            comment: Review comment
        
        Returns:
            Created review
        """
        import uuid
        
        review = TemplateReview(
            review_id=str(uuid.uuid4()),
            template_id=template_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
            created_at=datetime.utcnow().isoformat(),
            helpful_count=0
        )
        
        if template_id not in self.reviews:
            self.reviews[template_id] = []
        self.reviews[template_id].append(review)
        
        # Update template rating
        template = self.templates.get(template_id)
        if template:
            all_reviews = self.reviews[template_id]
            avg_rating = sum(r.rating for r in all_reviews) / len(all_reviews)
            template.rating = round(avg_rating, 1)
            template.reviews_count = len(all_reviews)
        
        self._save_reviews()
        return review
    
    def increment_downloads(self, template_id: str) -> bool:
        """Increment download count for a template"""
        template = self.templates.get(template_id)
        if template:
            template.downloads_count += 1
            self._save_templates()
            return True
        return False
    
    def get_similar_templates(
        self,
        template_id: str,
        limit: int = 5
    ) -> List[MarketplaceTemplate]:
        """
        Get similar templates based on category and tags
        
        Args:
            template_id: Template to find similar to
            limit: Maximum results
        
        Returns:
            List of similar templates
        """
        template = self.templates.get(template_id)
        if not template:
            return []
        
        # Find templates with same category or overlapping tags
        candidates = []
        for t in self.templates.values():
            if t.id == template_id:
                continue
            
            similarity_score = 0
            
            # Same category
            if t.category == template.category:
                similarity_score += 10
            
            # Overlapping tags
            common_tags = set(t.tags) & set(template.tags)
            similarity_score += len(common_tags) * 2
            
            # Similar rating
            rating_diff = abs(t.rating - template.rating)
            if rating_diff < 0.5:
                similarity_score += 3
            
            candidates.append((t, similarity_score))
        
        # Sort by similarity
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [t for t, _ in candidates[:limit]]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get marketplace statistics"""
        total_templates = len(self.templates)
        free_templates = len([t for t in self.templates.values() if not t.is_premium])
        premium_templates = len([t for t in self.templates.values() if t.is_premium])
        total_downloads = sum(t.downloads_count for t in self.templates.values())
        avg_rating = sum(t.rating for t in self.templates.values()) / total_templates if total_templates > 0 else 0
        
        return {
            "total_templates": total_templates,
            "free_templates": free_templates,
            "premium_templates": premium_templates,
            "total_downloads": total_downloads,
            "average_rating": round(avg_rating, 2),
            "total_reviews": sum(len(reviews) for reviews in self.reviews.values()),
            "categories": len(self.categories)
        }
    
    def _save_templates(self):
        """Save templates to disk"""
        templates_file = self.data_dir / "templates.json"
        data = {
            "templates": [asdict(t) for t in self.templates.values()]
        }
        with open(templates_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_reviews(self):
        """Save reviews to disk"""
        reviews_file = self.data_dir / "reviews.json"
        all_reviews = []
        for reviews in self.reviews.values():
            all_reviews.extend([asdict(r) for r in reviews])
        
        data = {"reviews": all_reviews}
        with open(reviews_file, 'w') as f:
            json.dump(data, f, indent=2)


# Demo/Test function
def demo_marketplace():
    """Demonstrate marketplace capabilities"""
    service = WorkflowMarketplaceService()
    
    print("🛒 Workflow Marketplace Demo\n")
    
    # Get stats
    stats = service.get_stats()
    print(f"📊 Marketplace Stats:")
    print(f"   Total Templates: {stats['total_templates']}")
    print(f"   Free: {stats['free_templates']} | Premium: {stats['premium_templates']}")
    print(f"   Total Downloads: {stats['total_downloads']:,}")
    print(f"   Average Rating: {stats['average_rating']}⭐")
    
    # Browse popular
    print(f"\n🔥 Popular Templates:")
    popular = service.get_popular_templates(5)
    for t in popular:
        price_str = "FREE" if t.price == 0 else f"${t.price}"
        print(f"   {t.icon} {t.name}")
        print(f"      {t.rating}⭐ ({t.reviews_count} reviews) | {t.downloads_count:,} downloads | {price_str}")
    
    # Browse by category
    print(f"\n📱 Lead Nurturing Templates:")
    lead_templates = service.get_category_templates("lead_nurturing")
    for t in lead_templates[:3]:
        print(f"   {t.icon} {t.name} - {t.description[:60]}...")
    
    # Search
    print(f"\n🔍 Search 'appointment':")
    search_results = service.search_templates("appointment", limit=3)
    for t in search_results:
        print(f"   {t.icon} {t.name}")
    
    # Featured
    print(f"\n⭐ Featured Templates:")
    featured = service.get_featured_templates(3)
    for t in featured:
        print(f"   {t.icon} {t.name} - {t.difficulty} | {t.estimated_time}")
    
    # Categories
    print(f"\n📂 Categories:")
    categories = service.get_categories()
    for cat in categories:
        print(f"   {cat['icon']} {cat['name']} ({cat['count']} templates)")
    
    return service


if __name__ == "__main__":
    demo_marketplace()
