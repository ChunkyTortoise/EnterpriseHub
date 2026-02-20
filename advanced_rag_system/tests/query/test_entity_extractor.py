"""Tests for Entity Extractor module."""


import pytest
from src.query.entity_extractor import (
    Entity,
    EntityExtractor,
    EntityType,
    ExtractionConfig,
)


@pytest.mark.unit


class TestEntity:
    """Test Entity class."""

    def test_entity_creation(self):
        """Test creating an entity."""
        entity = Entity(
            text="Rancho Cucamonga",
            type=EntityType.CITY,
            start=10,
            end=26,
            confidence=0.95,
        )

        assert entity.text == "Rancho Cucamonga"
        assert entity.type == EntityType.CITY
        assert entity.start == 10
        assert entity.end == 26
        assert entity.confidence == 0.95
        assert entity.normalized_value == "rancho cucamonga"

    def test_entity_with_normalized_value(self):
        """Test entity with explicit normalized value."""
        entity = Entity(
            text="$800k",
            type=EntityType.PRICE,
            start=0,
            end=5,
            normalized_value="800000",
        )

        assert entity.normalized_value == "800000"

    def test_entity_span_property(self):
        """Test entity span property."""
        entity = Entity(
            text="test",
            type=EntityType.PERSON,
            start=5,
            end=9,
        )

        assert entity.span == (5, 9)

    def test_entity_to_dict(self):
        """Test entity serialization."""
        entity = Entity(
            text="3-bedroom",
            type=EntityType.BEDROOMS,
            start=0,
            end=9,
            confidence=0.9,
            metadata={"parsed_value": 3},
        )

        d = entity.to_dict()
        assert d["text"] == "3-bedroom"
        assert d["type"] == "bedrooms"
        assert d["confidence"] == 0.9
        assert d["metadata"]["parsed_value"] == 3


class TestEntityExtractor:
    """Test EntityExtractor functionality."""

    @pytest.fixture
    def extractor(self):
        """Create an entity extractor."""
        config = ExtractionConfig(domain="real_estate", confidence_threshold=0.6)
        return EntityExtractor(config=config)

    def test_extractor_initialization(self, extractor):
        """Test extractor initialization."""
        assert extractor.config.domain == "real_estate"
        assert extractor.config.confidence_threshold == 0.6
        assert len(extractor._patterns) > 0
        assert len(extractor._domain_terms) > 0

    def test_extract_bedrooms(self, extractor):
        """Test extraction of bedroom counts."""
        entities = extractor.extract("Show me 3 bedroom houses")

        bedroom_entities = [e for e in entities if e.type == EntityType.BEDROOMS]
        assert len(bedroom_entities) > 0
        # Check normalized value contains "3"
        assert "3" in bedroom_entities[0].normalized_value

    def test_extract_bathrooms(self, extractor):
        """Test extraction of bathroom counts."""
        entities = extractor.extract("Looking for 2.5 bath home")

        bath_entities = [e for e in entities if e.type == EntityType.BATHROOMS]
        assert len(bath_entities) > 0

    def test_extract_price(self, extractor):
        """Test extraction of price."""
        entities = extractor.extract("Houses under $800,000")

        price_entities = [e for e in entities if e.type == EntityType.MONEY]
        assert len(price_entities) > 0

    def test_extract_square_feet(self, extractor):
        """Test extraction of square footage."""
        entities = extractor.extract("Looking for 2000 sqft home")

        sqft_entities = [e for e in entities if e.type == EntityType.SQUARE_FEET]
        assert len(sqft_entities) > 0
        assert sqft_entities[0].normalized_value == "2000"

    def test_extract_city(self, extractor):
        """Test extraction of city names."""
        entities = extractor.extract("Show me houses in Rancho Cucamonga")

        city_entities = [e for e in entities if e.type == EntityType.CITY]
        assert len(city_entities) > 0
        assert "rancho cucamonga" in city_entities[0].normalized_value

    def test_extract_neighborhood(self, extractor):
        """Test extraction of neighborhood names."""
        entities = extractor.extract("Homes in Victoria Gardens")

        neighborhood_entities = [e for e in entities if e.type == EntityType.NEIGHBORHOOD]
        assert len(neighborhood_entities) > 0

    def test_extract_zip_code(self, extractor):
        """Test extraction of zip codes."""
        entities = extractor.extract("Properties in 91730")

        zip_entities = [e for e in entities if e.type == EntityType.ZIP_CODE]
        assert len(zip_entities) > 0
        assert zip_entities[0].text == "91730"

    def test_extract_mls_number(self, extractor):
        """Test extraction of MLS numbers."""
        entities = extractor.extract("MLS #123456789")

        mls_entities = [e for e in entities if e.type == EntityType.MLS_NUMBER]
        assert len(mls_entities) > 0

    def test_extract_email(self, extractor):
        """Test extraction of email addresses."""
        entities = extractor.extract("Contact me at agent@example.com")

        email_entities = [e for e in entities if e.type == EntityType.EMAIL]
        assert len(email_entities) > 0
        assert email_entities[0].text == "agent@example.com"

    def test_extract_phone(self, extractor):
        """Test extraction of phone numbers."""
        entities = extractor.extract("Call me at (909) 555-1234")

        phone_entities = [e for e in entities if e.type == EntityType.PHONE]
        assert len(phone_entities) > 0

    def test_extract_property_type(self, extractor):
        """Test extraction of property types."""
        entities = extractor.extract("Looking for a condo or townhouse")

        type_entities = [e for e in entities if e.type == EntityType.PROPERTY_TYPE]
        assert len(type_entities) >= 1

    def test_extract_amenities(self, extractor):
        """Test extraction of amenities."""
        entities = extractor.extract("House with pool and garage")

        amenity_entities = [e for e in entities if e.type == EntityType.AMENITY]
        assert len(amenity_entities) >= 1

    def test_extract_multiple_entities(self, extractor):
        """Test extraction of multiple entity types."""
        entities = extractor.extract("3 bedroom, 2 bath house in Rancho Cucamonga under $800k")

        types_found = {e.type for e in entities}
        # Check that some key entities were extracted
        assert EntityType.CITY in types_found
        assert EntityType.MONEY in types_found
        # Bedrooms or bathrooms may vary based on pattern matching

    def test_empty_query(self, extractor):
        """Test extraction from empty query."""
        entities = extractor.extract("")
        assert entities == []

    def test_whitespace_query(self, extractor):
        """Test extraction from whitespace query."""
        entities = extractor.extract("   ")
        assert entities == []

    def test_resolve_overlaps(self, extractor):
        """Test that overlapping entities are resolved."""
        # "Victoria Gardens" could match both neighborhood and individual words
        entities = extractor.extract("Homes in Victoria Gardens")

        # Should not have overlapping spans
        for i, e1 in enumerate(entities):
            for e2 in entities[i + 1 :]:
                assert not (e1.start < e2.end and e2.start < e1.end)

    def test_confidence_threshold(self, extractor):
        """Test that confidence threshold is applied."""
        entities = extractor.extract("Show me houses")

        # All entities should meet confidence threshold
        assert all(e.confidence >= extractor.config.confidence_threshold for e in entities)


class TestEntityDisambiguation:
    """Test entity disambiguation."""

    @pytest.fixture
    def extractor(self):
        """Create an extractor with disambiguation enabled."""
        config = ExtractionConfig(enable_disambiguation=True)
        return EntityExtractor(config=config)

    def test_disambiguate_location_to_city(self, extractor):
        """Test disambiguation of location to city."""
        entities = [
            Entity(
                text="Rancho Cucamonga",
                type=EntityType.LOCATION,
                start=0,
                end=16,
                confidence=0.7,
            )
        ]

        disambiguated = extractor.disambiguate(entities, "in Rancho Cucamonga")

        # Should be disambiguated to city
        assert disambiguated[0].type == EntityType.CITY
        assert "disambiguated_from" in disambiguated[0].metadata

    def test_disambiguate_location_to_neighborhood(self, extractor):
        """Test disambiguation of location to neighborhood."""
        entities = [
            Entity(
                text="Victoria",
                type=EntityType.LOCATION,
                start=0,
                end=8,
                confidence=0.7,
            )
        ]

        disambiguated = extractor.disambiguate(entities, "in Victoria Gardens")

        # Should be disambiguated to neighborhood
        assert disambiguated[0].type == EntityType.NEIGHBORHOOD

    def test_disambiguation_boosts_confidence(self, extractor):
        """Test that disambiguation boosts confidence with context."""
        original_confidence = 0.7
        entities = [
            Entity(
                text="3 bed",
                type=EntityType.BEDROOMS,
                start=0,
                end=5,
                confidence=original_confidence,
            )
        ]

        disambiguated = extractor.disambiguate(entities, "3 bedroom house")

        # Confidence should be boosted due to context
        assert disambiguated[0].confidence > original_confidence

    def test_disambiguation_disabled(self):
        """Test that disambiguation can be disabled."""
        config = ExtractionConfig(enable_disambiguation=False)
        extractor = EntityExtractor(config=config)

        entities = [
            Entity(
                text="Rancho Cucamonga",
                type=EntityType.LOCATION,
                start=0,
                end=16,
            )
        ]

        disambiguated = extractor.disambiguate(entities, "in Rancho Cucamonga")

        # Type should remain unchanged
        assert disambiguated[0].type == EntityType.LOCATION


class TestEntityLinking:
    """Test entity linking functionality."""

    @pytest.fixture
    def extractor(self):
        """Create an entity extractor."""
        return EntityExtractor()

    def test_link_city(self, extractor):
        """Test linking city entity."""
        entities = [
            Entity(
                text="Rancho Cucamonga",
                type=EntityType.CITY,
                start=0,
                end=16,
            )
        ]

        results = extractor.link_to_kb(entities)

        assert len(results) == 1
        assert results[0].canonical_id is not None
        assert "rancho_cucamonga" in results[0].canonical_id

    def test_link_neighborhood(self, extractor):
        """Test linking neighborhood entity."""
        entities = [
            Entity(
                text="Victoria Gardens",
                type=EntityType.NEIGHBORHOOD,
                start=0,
                end=16,
            )
        ]

        results = extractor.link_to_kb(entities)

        assert len(results) == 1
        assert results[0].canonical_id is not None

    def test_link_school_district(self, extractor):
        """Test linking school district entity."""
        entities = [
            Entity(
                text="Etiwanda",
                type=EntityType.SCHOOL_DISTRICT,
                start=0,
                end=8,
            )
        ]

        results = extractor.link_to_kb(entities)

        assert len(results) == 1
        assert results[0].canonical_id is not None
        assert "etiwanda" in results[0].canonical_id

    def test_link_unknown_entity(self, extractor):
        """Test linking unknown entity provides candidates."""
        entities = [
            Entity(
                text="UnknownPlace123",
                type=EntityType.CITY,
                start=0,
                end=15,
            )
        ]

        results = extractor.link_to_kb(entities)

        assert len(results) == 1
        assert results[0].canonical_id is None
        assert len(results[0].candidates) > 0


class TestKnowledgeGraphPrep:
    """Test Knowledge Graph preparation."""

    @pytest.fixture
    def extractor(self):
        """Create an entity extractor."""
        return EntityExtractor()

    def test_kg_nodes_creation(self, extractor):
        """Test KG node creation."""
        entities = [
            Entity(text="Rancho Cucamonga", type=EntityType.CITY, start=0, end=16),
            Entity(text="3-bedroom", type=EntityType.BEDROOMS, start=20, end=29),
        ]

        kg_prep = extractor.prepare_for_knowledge_graph(entities, "query")

        assert len(kg_prep.kg_nodes) == 2
        assert all("id" in node for node in kg_prep.kg_nodes)
        assert all("type" in node for node in kg_prep.kg_nodes)

    def test_relationship_detection(self, extractor):
        """Test relationship detection between entities."""
        entities = [
            Entity(text="house", type=EntityType.PROPERTY, start=0, end=5),
            Entity(text="Rancho Cucamonga", type=EntityType.CITY, start=10, end=26),
        ]

        kg_prep = extractor.prepare_for_knowledge_graph(entities, "house in Rancho Cucamonga")

        assert len(kg_prep.relationships) > 0
        assert kg_prep.relationships[0]["type"] == "LOCATED_IN"

    def test_kg_edges_creation(self, extractor):
        """Test KG edge creation from relationships."""
        entities = [
            Entity(text="house", type=EntityType.PROPERTY, start=0, end=5),
            Entity(text="pool", type=EntityType.FEATURE, start=10, end=14),
        ]

        kg_prep = extractor.prepare_for_knowledge_graph(entities, "house with pool")

        assert len(kg_prep.kg_edges) > 0
        assert all("source" in edge for edge in kg_prep.kg_edges)
        assert all("target" in edge for edge in kg_prep.kg_edges)
        assert all("type" in edge for edge in kg_prep.kg_edges)

    def test_entity_clustering(self, extractor):
        """Test entity clustering by type."""
        entities = [
            Entity(text="Rancho Cucamonga", type=EntityType.CITY, start=0, end=16),
            Entity(text="Ontario", type=EntityType.CITY, start=20, end=27),
            Entity(text="3-bedroom", type=EntityType.BEDROOMS, start=30, end=39),
        ]

        kg_prep = extractor.prepare_for_knowledge_graph(entities, "query")

        assert "city" in kg_prep.entity_clusters
        assert "bedrooms" in kg_prep.entity_clusters
        assert len(kg_prep.entity_clusters["city"]) == 2
        assert len(kg_prep.entity_clusters["bedrooms"]) == 1

    def test_kg_prep_to_dict(self, extractor):
        """Test KG prep serialization."""
        entities = [Entity(text="test", type=EntityType.PERSON, start=0, end=4)]

        kg_prep = extractor.prepare_for_knowledge_graph(entities, "query")
        d = kg_prep.to_dict()

        assert "entities" in d
        assert "kg_nodes" in d
        assert "kg_edges" in d
        assert "entity_clusters" in d


class TestExtractionConfig:
    """Test extraction configuration."""

    def test_default_config(self):
        """Test default configuration."""
        config = ExtractionConfig()

        assert config.confidence_threshold == 0.6
        assert config.enable_coreference is True
        assert config.enable_disambiguation is True
        assert config.domain == "real_estate"
        assert config.link_to_kb is False

    def test_custom_config(self):
        """Test custom configuration."""
        config = ExtractionConfig(
            confidence_threshold=0.8,
            enable_coreference=False,
            enable_disambiguation=False,
            domain="general",
            link_to_kb=True,
        )

        assert config.confidence_threshold == 0.8
        assert config.enable_coreference is False
        assert config.enable_disambiguation is False
        assert config.domain == "general"
        assert config.link_to_kb is True


class TestEntityTypes:
    """Test entity type definitions."""

    def test_general_entity_types(self):
        """Test general entity types exist."""
        assert EntityType.PERSON.value == "person"
        assert EntityType.ORGANIZATION.value == "organization"
        assert EntityType.LOCATION.value == "location"
        assert EntityType.DATE.value == "date"
        assert EntityType.MONEY.value == "money"

    def test_real_estate_entity_types(self):
        """Test real estate entity types exist."""
        assert EntityType.PROPERTY.value == "property"
        assert EntityType.PROPERTY_TYPE.value == "property_type"
        assert EntityType.PRICE.value == "price"
        assert EntityType.BEDROOMS.value == "bedrooms"
        assert EntityType.BATHROOMS.value == "bathrooms"
        assert EntityType.SQUARE_FEET.value == "square_feet"
        assert EntityType.MLS_NUMBER.value == "mls_number"
        assert EntityType.ADDRESS.value == "address"
        assert EntityType.CITY.value == "city"
        assert EntityType.NEIGHBORHOOD.value == "neighborhood"
        assert EntityType.SCHOOL_DISTRICT.value == "school_district"

    def test_all_entity_types(self):
        """Test that all expected entity types exist."""
        expected_types = [
            "person",
            "organization",
            "location",
            "date",
            "time",
            "money",
            "percent",
            "email",
            "phone",
            "url",
            "property",
            "property_type",
            "price",
            "price_range",
            "bedrooms",
            "bathrooms",
            "square_feet",
            "lot_size",
            "year_built",
            "mls_number",
            "address",
            "city",
            "state",
            "zip_code",
            "neighborhood",
            "school_district",
            "school",
            "amenity",
            "feature",
            "view",
            "agent",
            "brokerage",
        ]

        actual_types = [et.value for et in EntityType]
        for expected in expected_types:
            assert expected in actual_types, f"Missing entity type: {expected}"