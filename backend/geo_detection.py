import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import spacy
from collections import Counter

logger = logging.getLogger(__name__)

class GeographicProcessor:
    """Extract and process geographic information from text"""
    
    def __init__(self):
        self.geolocator = Nominatim(user_agent="trendpulse")
        self.nlp = None
        self._load_spacy_model()
        
        # Country mappings and aliases
        self.country_aliases = {
            'usa': 'United States',
            'us': 'United States',
            'america': 'United States',
            'uk': 'United Kingdom',
            'britain': 'United Kingdom',
            'england': 'United Kingdom',
            'uae': 'United Arab Emirates',
            'russia': 'Russia',
            'china': 'China',
            'india': 'India',
            'japan': 'Japan',
            'germany': 'Germany',
            'france': 'France',
            'italy': 'Italy',
            'spain': 'Spain',
            'canada': 'Canada',
            'australia': 'Australia',
            'brazil': 'Brazil',
            'mexico': 'Mexico',
            'south korea': 'South Korea',
            'north korea': 'North Korea',
            'saudi arabia': 'Saudi Arabia',
            'south africa': 'South Africa'
        }
        
        # Major cities to countries mapping
        self.city_to_country = {
            'new york': 'United States',
            'los angeles': 'United States',
            'chicago': 'United States',
            'washington': 'United States',
            'boston': 'United States',
            'london': 'United Kingdom',
            'manchester': 'United Kingdom',
            'liverpool': 'United Kingdom',
            'paris': 'France',
            'marseille': 'France',
            'berlin': 'Germany',
            'munich': 'Germany',
            'rome': 'Italy',
            'milan': 'Italy',
            'madrid': 'Spain',
            'barcelona': 'Spain',
            'tokyo': 'Japan',
            'osaka': 'Japan',
            'beijing': 'China',
            'shanghai': 'China',
            'mumbai': 'India',
            'delhi': 'India',
            'sydney': 'Australia',
            'melbourne': 'Australia',
            'toronto': 'Canada',
            'vancouver': 'Canada',
            'moscow': 'Russia',
            'st petersburg': 'Russia'
        }
    
    def _load_spacy_model(self):
        """Load spaCy NLP model for named entity recognition"""
        try:
            # Try to load the English model
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Loaded spaCy English model successfully")
        except OSError:
            logger.warning("spaCy English model not found. Geographic detection will use basic pattern matching.")
            self.nlp = None
    
    def extract_locations_with_spacy(self, text: str) -> List[str]:
        """Extract locations using spaCy NER"""
        if not self.nlp:
            return []
        
        try:
            doc = self.nlp(text)
            locations = []
            
            for ent in doc.ents:
                if ent.label_ in ['GPE', 'LOC']:  # Geopolitical entities and locations
                    location = ent.text.strip().lower()
                    if location and len(location) > 2:  # Filter very short names
                        locations.append(location)
            
            return list(set(locations))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error in spaCy NER: {e}")
            return []
    
    def extract_locations_with_patterns(self, text: str) -> List[str]:
        """Extract locations using regex patterns"""
        locations = []
        text_lower = text.lower()
        
        # Look for country names and aliases
        for alias, country in self.country_aliases.items():
            if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
                locations.append(country.lower())
        
        # Look for city names
        for city, country in self.city_to_country.items():
            if re.search(r'\b' + re.escape(city) + r'\b', text_lower):
                locations.append(city)
                locations.append(country.lower())
        
        # Common location patterns
        location_patterns = [
            r'\bin\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "in Paris", "in New York"
            r'\bfrom\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "from London"
            r'\bat\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "at Berlin"
        ]
        
        for pattern in location_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                location = match.strip().lower()
                if len(location) > 2:
                    locations.append(location)
        
        return list(set(locations))
    
    def resolve_country_from_location(self, location: str) -> Optional[str]:
        """Resolve country from a location name"""
        location_lower = location.lower().strip()
        
        # Direct country match
        if location_lower in self.country_aliases:
            return self.country_aliases[location_lower]
        
        # City to country mapping
        if location_lower in self.city_to_country:
            return self.city_to_country[location_lower]
        
        # Try geocoding (with rate limiting)
        try:
            location_obj = self.geolocator.geocode(location, timeout=5)
            if location_obj and location_obj.address:
                # Extract country from address
                address_parts = location_obj.address.split(', ')
                if address_parts:
                    potential_country = address_parts[-1].strip()
                    # Normalize common country name variations
                    if potential_country.lower() in self.country_aliases:
                        return self.country_aliases[potential_country.lower()]
                    return potential_country
        except (GeocoderTimedOut, GeocoderServiceError):
            pass
        except Exception as e:
            logger.error(f"Geocoding error for '{location}': {e}")
        
        return None
    
    def calculate_confidence_score(self, locations: List[str], text: str) -> float:
        """Calculate confidence score for location detection"""
        if not locations:
            return 0.0
        
        # Factors that increase confidence:
        # 1. Number of location mentions
        # 2. Presence of country names vs. just cities
        # 3. Consistency of locations (same country/region)
        
        text_lower = text.lower()
        total_mentions = 0
        country_mentions = 0
        
        for location in locations:
            location_lower = location.lower()
            mentions = len(re.findall(r'\b' + re.escape(location_lower) + r'\b', text_lower))
            total_mentions += mentions
            
            # Check if it's a country
            if (location_lower in self.country_aliases or 
                location_lower in self.country_aliases.values()):
                country_mentions += mentions
        
        # Base confidence from number of mentions
        mention_score = min(total_mentions * 0.2, 0.8)
        
        # Bonus for country mentions
        country_bonus = min(country_mentions * 0.1, 0.2)
        
        # Bonus for multiple different locations (shows geographic context)
        diversity_bonus = min(len(set(locations)) * 0.05, 0.1)
        
        confidence = mention_score + country_bonus + diversity_bonus
        return min(confidence, 1.0)
    
    def extract_locations(self, text: str) -> Dict[str, Any]:
        """Main method to extract geographic information from text"""
        if not text:
            return {}
        
        # Extract locations using both methods
        spacy_locations = self.extract_locations_with_spacy(text)
        pattern_locations = self.extract_locations_with_patterns(text)
        
        # Combine and deduplicate
        all_locations = list(set(spacy_locations + pattern_locations))
        
        if not all_locations:
            return {}
        
        # Resolve countries for all locations
        countries = []
        resolved_locations = []
        
        for location in all_locations:
            country = self.resolve_country_from_location(location)
            if country:
                countries.append(country)
                resolved_locations.append({
                    'location': location,
                    'country': country,
                    'type': 'country' if location.lower() in self.country_aliases else 'city'
                })
        
        # Determine primary country (most mentioned)
        primary_country = None
        if countries:
            country_counts = Counter(countries)
            primary_country = country_counts.most_common(1)[0][0]
        
        # Calculate confidence
        confidence = self.calculate_confidence_score(all_locations, text)
        
        return {
            'locations': [loc['location'] for loc in resolved_locations],
            'resolved_locations': resolved_locations,
            'countries': list(set(countries)),
            'primary_country': primary_country,
            'confidence': confidence,
            'location_count': len(all_locations)
        }
    
    def get_country_code(self, country_name: str) -> Optional[str]:
        """Get ISO country code for a country name"""
        country_codes = {
            'united states': 'US',
            'united kingdom': 'GB',
            'germany': 'DE',
            'france': 'FR',
            'italy': 'IT',
            'spain': 'ES',
            'japan': 'JP',
            'china': 'CN',
            'india': 'IN',
            'russia': 'RU',
            'canada': 'CA',
            'australia': 'AU',
            'brazil': 'BR',
            'mexico': 'MX',
            'south korea': 'KR',
            'north korea': 'KP',
            'saudi arabia': 'SA',
            'south africa': 'ZA',
            'united arab emirates': 'AE'
        }
        
        return country_codes.get(country_name.lower()) 