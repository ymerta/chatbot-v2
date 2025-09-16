"""
Entity extraction for Netmera knowledge graph construction
Pure regex-based implementation (no spaCy dependency required)
"""

import re
import logging
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class ExtractedEntity:
    """Extracted entity from text"""
    text: str
    entity_type: str
    confidence: float
    context: str
    start_pos: int
    end_pos: int

class EntityExtractor:
    """Extract Netmera-specific entities from documentation"""
    
    def __init__(self):
        """Initialize entity extractor with Netmera-specific patterns"""
        
        # Define Netmera domain patterns
        self.entity_patterns = {
            'SDK': [
                r'\bNetmera\s+SDK\b',
                r'\b(?:iOS|Android|React\s+Native|Flutter|Unity)\s+SDK\b',
                r'\bSDK\s+integration\b',
                r'\bNetmera\s+framework\b'
            ],
            'API': [
                r'\b(?:REST\s+)?API\b',
                r'\bendpoint\b',
                r'\b/api/[a-zA-Z0-9/_-]+\b',
                r'\bHTTP\s+(?:GET|POST|PUT|DELETE)\b',
                r'\bAPI\s+key\b',
                r'\bAPI\s+token\b'
            ],
            'Feature': [
                r'\bpush\s+notification[s]?\b',
                r'\bin-app\s+messaging\b', 
                r'\buser\s+segmentation\b',
                r'\bcampaign[s]?\b',
                r'\banalytics\b',
                r'\bA/B\s+test(?:ing)?\b',
                r'\bautomation\b',
                r'\bpersonalization\b',
                r'\bgeofencing\b'
            ],
            'Platform': [
                r'\biOS\b',
                r'\bAndroid\b',
                r'\bReact\s+Native\b',
                r'\bFlutter\b',
                r'\bUnity\b',
                r'\bWeb\b',
                r'\bmobile\s+app\b',
                r'\bnative\s+app\b'
            ],
            'Configuration': [
                r'\bGradle\b',
                r'\bpodfile\b',
                r'\bInfo\.plist\b',
                r'\bmanifest\.xml\b',
                r'\bconfig(?:uration)?\b',
                r'\bsettings\b',
                r'\benvironment\b',
                r'\bparameters?\b'
            ],
            'Error': [
                r'\berror\b',
                r'\bexception\b',
                r'\bfail(?:ed|ure)?\b',
                r'\bissue\b',
                r'\bproblem\b',
                r'\btroubleshoot(?:ing)?\b',
                r'\bdebug(?:ging)?\b'
            ],
            'Procedure': [
                r'\bstep[s]?\b',
                r'\binstall(?:ation)?\b',
                r'\bsetup\b',
                r'\bconfigure\b',
                r'\bimplement(?:ation)?\b',
                r'\bintegrate\b',
                r'\bguide\b',
                r'\btutorial\b'
            ],
            'Code': [
                r'\bclass\b',
                r'\bmethod\b',
                r'\bfunction\b',
                r'\bvariable\b',
                r'\bcode\s+example\b',
                r'\bsample\s+code\b',
                r'\bsnippet\b'
            ]
        }
        
        # Compile regex patterns
        self.compiled_patterns = {}
        for entity_type, patterns in self.entity_patterns.items():
            self.compiled_patterns[entity_type] = [
                re.compile(pattern, re.IGNORECASE) for pattern in patterns
            ]
        
        # Netmera-specific terms that are always entities
        self.netmera_terms = {
            'SDK': [
                'Netmera SDK', 'iOS SDK', 'Android SDK', 'React Native SDK',
                'Flutter SDK', 'Unity SDK', 'Web SDK'
            ],
            'Feature': [
                'Push Notifications', 'In-App Messaging', 'User Segmentation',
                'Campaign Management', 'Analytics Dashboard', 'A/B Testing',
                'Marketing Automation', 'Personalization Engine', 'Geofencing',
                'Deep Linking', 'Rich Media', 'Interactive Notifications'
            ],
            'API': [
                'Campaign API', 'Segmentation API', 'Analytics API', 'User API',
                'Notification API', 'Event API', 'Profile API'
            ],
            'Platform': [
                'iOS', 'Android', 'React Native', 'Flutter', 'Unity', 'Web',
                'Mobile App', 'Native App', 'Hybrid App'
            ]
        }
    
    def extract_entities(self, text: str, source_url: str = "") -> List[ExtractedEntity]:
        """Extract entities from text"""
        entities = []
        text_lower = text.lower()
        
        # Extract using regex patterns
        for entity_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    entity = ExtractedEntity(
                        text=match.group(),
                        entity_type=entity_type,
                        confidence=0.7,  # Base confidence for pattern matching
                        context=self._get_context(text, match.start(), match.end()),
                        start_pos=match.start(),
                        end_pos=match.end()
                    )
                    entities.append(entity)
        
        # Extract known Netmera terms
        for entity_type, terms in self.netmera_terms.items():
            for term in terms:
                term_lower = term.lower()
                start_pos = 0
                while True:
                    pos = text_lower.find(term_lower, start_pos)
                    if pos == -1:
                        break
                    
                    entity = ExtractedEntity(
                        text=text[pos:pos+len(term)],
                        entity_type=entity_type,
                        confidence=0.9,  # High confidence for known terms
                        context=self._get_context(text, pos, pos+len(term)),
                        start_pos=pos,
                        end_pos=pos+len(term)
                    )
                    entities.append(entity)
                    start_pos = pos + len(term)
        
        # Remove duplicates and overlaps
        entities = self._remove_overlaps(entities)
        
        logger.debug(f"Extracted {len(entities)} entities from text")
        return entities
    
    def extract_relationships(self, text: str, entities: List[ExtractedEntity]) -> List[Tuple[str, str, str]]:
        """Extract relationships between entities in text"""
        relationships = []
        
        # Relationship patterns
        relation_patterns = {
            'requires': [r'\brequires?\b', r'\bneeds?\b', r'\bdepends?\s+on\b'],
            'provides': [r'\bprovides?\b', r'\boffers?\b', r'\benables?\b'],
            'implements': [r'\bimplements?\b', r'\bsupports?\b', r'\bincludes?\b'],
            'configures': [r'\bconfigures?\b', r'\bsets?\s+up\b', r'\bsettings?\s+for\b'],
            'uses': [r'\buses?\b', r'\butilizes?\b', r'\bcalls?\b'],
            'contains': [r'\bcontains?\b', r'\bincludes?\b', r'\bhas\b']
        }
        
        # Look for relationship patterns between entities
        for i, entity1 in enumerate(entities):
            for j, entity2 in enumerate(entities):
                if i >= j:  # Avoid self-relations and duplicates
                    continue
                
                # Get text between entities
                start_pos = min(entity1.end_pos, entity2.end_pos)
                end_pos = max(entity1.start_pos, entity2.start_pos)
                
                if end_pos - start_pos > 100:  # Too far apart
                    continue
                
                between_text = text[start_pos:end_pos].lower()
                
                # Check for relationship patterns
                for relation_type, patterns in relation_patterns.items():
                    for pattern in patterns:
                        if re.search(pattern, between_text, re.IGNORECASE):
                            # Determine direction based on position
                            if entity1.start_pos < entity2.start_pos:
                                relationships.append((entity1.text, entity2.text, relation_type))
                            else:
                                relationships.append((entity2.text, entity1.text, relation_type))
                            break
        
        logger.debug(f"Extracted {len(relationships)} relationships")
        return relationships
    
    def _get_context(self, text: str, start: int, end: int, context_size: int = 50) -> str:
        """Get context around entity"""
        context_start = max(0, start - context_size)
        context_end = min(len(text), end + context_size)
        return text[context_start:context_end].strip()
    
    def _remove_overlaps(self, entities: List[ExtractedEntity]) -> List[ExtractedEntity]:
        """Remove overlapping entities, keeping higher confidence ones"""
        # Sort by confidence descending
        entities.sort(key=lambda x: x.confidence, reverse=True)
        
        non_overlapping = []
        for entity in entities:
            # Check if this entity overlaps with any existing one
            overlaps = False
            for existing in non_overlapping:
                if (entity.start_pos < existing.end_pos and 
                    entity.end_pos > existing.start_pos):
                    overlaps = True
                    break
            
            if not overlaps:
                non_overlapping.append(entity)
        
        return non_overlapping
    
    def generate_entity_id(self, entity_text: str, entity_type: str) -> str:
        """Generate consistent entity ID"""
        # Normalize text
        normalized = re.sub(r'\s+', '_', entity_text.lower().strip())
        normalized = re.sub(r'[^\w_]', '', normalized)
        return f"{entity_type.lower()}_{normalized}"
