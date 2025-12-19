"""
Patterns and keyword lists for rule-based extraction.

This module contains regex patterns and keyword dictionaries
for extracting structured information from cleaning-related text.
"""

import re
from typing import Dict, List, Set

# ============================================================================
# Surface Type Patterns
# ============================================================================

SURFACE_KEYWORDS: Dict[str, List[str]] = {
    "pillows_bedding": [
        "pillow", "pillows", "bedding", "bed", "mattress", "mattresses",
        "duvet", "comforter", "blanket", "sheets", "bed sheet", "bedding set",
        "throw pillow", "cushion", "cushions", "headboard"
    ],
    "clothes": [
        "shirt", "shirts", "t-shirt", "t-shirts", "clothes", "clothing",
        "fabric", "garment", "garments", "apparel", "laundry", "washable",
        "sweater", "sweaters", "jacket", "jackets", "pants", "jeans",
        "dress", "dresses", "blouse", "blouses", "suit", "suits"
    ],
    "carpets_floors": [
        "carpet", "carpets", "rug", "rugs", "floor", "floors", "flooring",
        "carpeting", "area rug", "throw rug", "mat", "mats", "runner",
        "hardwood floor", "tile floor", "linoleum", "vinyl floor"
    ],
    "upholstery": [
        "sofa", "sofas", "couch", "couches", "chair", "chairs", "upholstery",
        "upholstered", "furniture", "armchair", "recliner", "ottoman",
        "loveseat", "sectional", "fabric sofa", "leather sofa"
    ],
    "hard_surfaces": [
        "countertop", "countertops", "counter", "counters", "table", "tables",
        "desk", "desks", "shelf", "shelves", "cabinet", "cabinets",
        "hard surface", "hard surfaces", "tile", "tiles", "granite",
        "marble", "quartz", "ceramic tile"
    ],
    "appliances": [
        "oven", "ovens", "refrigerator", "fridge", "dishwasher", "microwave",
        "stove", "stovetop", "range", "appliance", "appliances", "washer",
        "dryer", "washing machine", "freezer"
    ],
    "bathroom": [
        "bathroom", "shower", "showers", "bathtub", "tub", "sink", "sinks",
        "toilet", "toilets", "bathroom tile", "shower tile", "grout",
        "bathroom floor", "shower door", "mirror", "faucet", "faucets"
    ],
    "outdoor": [
        "patio", "deck", "decks", "outdoor", "outdoor furniture", "patio furniture",
        "decking", "outdoor carpet", "outdoor rug", "porch", "balcony",
        "driveway", "sidewalk", "outdoor surface"
    ]
}

# ============================================================================
# Dirt Type Patterns
# ============================================================================

DIRT_KEYWORDS: Dict[str, List[str]] = {
    "dust": [
        "dust", "dusty", "dusting", "dust accumulation", "dust build-up",
        "dust particles", "dusty surface", "dust mite", "dust mites"
    ],
    "stain": [
        "stain", "stains", "stained", "staining", "spill", "spills", "spilled",
        "spot", "spots", "discoloration", "discolored", "mark", "marks",
        "blemish", "blemishes"
    ],
    "odor": [
        "odor", "odour", "odors", "smell", "smells", "smelly", "musty",
        "mustiness", "stale", "stale smell", "bad smell", "unpleasant odor",
        "foul odor", "lingering smell"
    ],
    "grease": [
        "grease", "greasy", "oil", "oily", "fat", "fatty", "grease stain",
        "oil stain", "cooking oil", "kitchen grease", "grease build-up",
        "grease accumulation"
    ],
    "mold": [
        "mold", "mould", "mildew", "moldy", "mouldy", "fungus", "fungal",
        "mold growth", "mildew growth", "black mold", "mold stain",
        "mold removal", "mold remediation"
    ],
    "pet_hair": [
        "pet hair", "dog hair", "cat hair", "fur", "furry", "pet fur",
        "animal hair", "dander", "pet dander", "shedding", "pet shedding",
        "hair", "hairs"
    ],
    "water_stain": [
        "water stain", "water damage", "water mark", "water marks",
        "mineral deposit", "mineral deposits", "hard water stain",
        "lime scale", "limescale", "calcium deposit", "water spot"
    ],
    "ink": [
        "ink", "ink stain", "pen", "pen mark", "marker", "marker stain",
        "ballpoint pen", "ink spill", "permanent marker", "ink mark"
    ]
}

# ============================================================================
# Cleaning Method Patterns
# ============================================================================

METHOD_KEYWORDS: Dict[str, List[str]] = {
    "washing_machine": [
        "washing machine", "washer", "machine wash", "machine-wash",
        "machine washable", "laundry machine", "wash cycle", "washing cycle"
    ],
    "hand_wash": [
        "hand wash", "hand-wash", "handwashing", "hand washing",
        "wash by hand", "hand clean", "soak", "soaking", "soaked",
        "hand scrub", "manual wash"
    ],
    "vacuum": [
        "vacuum", "vacuuming", "vacuumed", "vacuum cleaner", "vacuuming",
        "vacuum up", "hoover", "hoovering", "suck up", "sucking up"
    ],
    "spot_clean": [
        "spot clean", "spot-clean", "spot cleaning", "spot treatment",
        "spot removal", "local cleaning", "targeted cleaning", "spot treat"
    ],
    "steam_clean": [
        "steam clean", "steam cleaning", "steam cleaner", "steam",
        "steaming", "steamed", "vapor cleaning", "steam treatment"
    ],
    "dry_clean": [
        "dry clean", "dry cleaning", "dry-clean", "dry cleaner",
        "professional cleaning", "dry clean only"
    ],
    "wipe": [
        "wipe", "wiping", "wiped", "wipe down", "wipe off", "wipe clean",
        "damp cloth", "wet wipe", "cleaning wipe"
    ],
    "scrub": [
        "scrub", "scrubbing", "scrubbed", "scrub brush", "scrubbing brush",
        "hard scrub", "scrub away", "scrub off"
    ]
}

# ============================================================================
# Cleaning Tools/Equipment Patterns
# ============================================================================

TOOL_KEYWORDS: Dict[str, List[str]] = {
    "vacuum": [
        "vacuum", "vacuum cleaner", "hoover", "upright vacuum",
        "canister vacuum", "handheld vacuum", "shop vac", "wet/dry vacuum"
    ],
    "sponge": [
        "sponge", "sponges", "cleaning sponge", "scrub sponge",
        "magic eraser", "melamine sponge"
    ],
    "brush": [
        "brush", "brushes", "scrub brush", "scrubbing brush", "stiff brush",
        "soft brush", "toothbrush", "nail brush", "cleaning brush"
    ],
    "microfiber_cloth": [
        "microfiber", "microfiber cloth", "microfiber towel", "microfiber rag",
        "microfiber cleaning cloth", "microfiber wipe", "microfiber mop"
    ],
    "steam_cleaner": [
        "steam cleaner", "steamer", "steam mop", "handheld steamer",
        "steam cleaning machine"
    ],
    "vinegar": [
        "vinegar", "white vinegar", "distilled vinegar", "apple cider vinegar",
        "vinegar solution", "vinegar and water"
    ],
    "baking_soda": [
        "baking soda", "bicarbonate of soda", "sodium bicarbonate",
        "baking soda paste", "baking soda solution"
    ],
    "detergent": [
        "detergent", "laundry detergent", "dish detergent", "dish soap",
        "soap", "cleaning soap", "liquid soap"
    ],
    "bleach": [
        "bleach", "chlorine bleach", "bleach solution", "bleach and water",
        "bleach cleaner"
    ],
    "hydrogen_peroxide": [
        "hydrogen peroxide", "peroxide", "3% hydrogen peroxide"
    ],
    "ammonia": [
        "ammonia", "ammonia solution", "ammonia and water"
    ],
    "rubbing_alcohol": [
        "rubbing alcohol", "isopropyl alcohol", "alcohol", "70% alcohol"
    ],
    "spray_bottle": [
        "spray bottle", "sprayer", "spray", "spray cleaner", "cleaning spray"
    ],
    "bucket": [
        "bucket", "pail", "cleaning bucket", "mop bucket"
    ],
    "mop": [
        "mop", "mops", "mop head", "wet mop", "dry mop", "microfiber mop",
        "sponge mop", "string mop"
    ],
    "towel": [
        "towel", "towels", "paper towel", "paper towels", "cleaning towel",
        "rag", "rags", "cleaning rag", "cloth", "cleaning cloth"
    ],
    "gloves": [
        "gloves", "rubber gloves", "cleaning gloves", "protective gloves",
        "latex gloves", "nitrile gloves"
    ]
}

# ============================================================================
# Step Extraction Patterns
# ============================================================================

# Regex patterns for identifying step boundaries
STEP_PATTERNS = [
    # Numbered steps: "Step 1:", "1.", "1)", etc.
    re.compile(r'^(?:step\s+)?(\d+)[\.\):]\s+(.+)$', re.IGNORECASE | re.MULTILINE),
    # Ordinal steps: "First,", "Second,", "Then,", "Next,", "Finally,"
    re.compile(r'^(?:first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|then|next|finally|lastly)[,:]\s+(.+)$', re.IGNORECASE | re.MULTILINE),
    # Bullet points with action verbs (allow leading whitespace)
    re.compile(r'^\s*[-•*]\s+(.+)$', re.MULTILINE),
    # Action-oriented sentences (start with imperative verbs)
    re.compile(r'^(?:mix|apply|spray|wipe|scrub|rinse|dry|let|allow|remove|blot|vacuum|wash|soak|dilute|combine|add|pour|dampen|saturate|cover|place|wait|repeat)[\s,].+$', re.IGNORECASE | re.MULTILINE),
]

# Keywords that indicate step boundaries
STEP_INDICATORS = [
    "step", "steps", "first", "second", "third", "then", "next", "finally",
    "lastly", "after", "before", "once", "when", "while", "during"
]

# Action verbs that typically start cleaning steps
ACTION_VERBS = [
    "mix", "apply", "spray", "wipe", "scrub", "rinse", "dry", "let", "allow",
    "remove", "blot", "vacuum", "wash", "soak", "dilute", "combine", "add",
    "pour", "dampen", "saturate", "cover", "place", "wait", "repeat",
    "shake", "stir", "spread", "gently", "carefully", "thoroughly"
]

# ============================================================================
# Helper Functions
# ============================================================================

def find_keywords_in_text(text: str, keyword_dict: Dict[str, List[str]]) -> Dict[str, float]:
    """
    Find keywords in text and return matches with confidence scores.
    
    Args:
        text: Text to search
        keyword_dict: Dictionary mapping categories to keyword lists
        
    Returns:
        Dictionary mapping categories to confidence scores (0.0-1.0)
    """
    text_lower = text.lower()
    matches: Dict[str, float] = {}
    
    for category, keywords in keyword_dict.items():
        count = 0
        for keyword in keywords:
            # Count occurrences (word boundaries to avoid partial matches)
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            count += len(re.findall(pattern, text_lower))
        
        # Confidence based on number of matches (normalized)
        if count > 0:
            # Simple confidence: more matches = higher confidence
            # Cap at 1.0, scale by number of unique keywords found
            matches[category] = min(1.0, count / max(1, len(keywords) / 2))
        else:
            matches[category] = 0.0
    
    return matches


def extract_best_match(matches: Dict[str, float], default: str = "other") -> tuple[str, float]:
    """
    Extract the category with the highest confidence score.
    
    Args:
        matches: Dictionary of category -> confidence score
        default: Default category if no matches
        
    Returns:
        Tuple of (category, confidence_score)
    """
    if not matches:
        return default, 0.0
    
    # Filter out zero-confidence matches
    non_zero = {k: v for k, v in matches.items() if v > 0}
    
    if not non_zero:
        return default, 0.0
    
    # Return category with highest confidence
    best_category = max(non_zero.items(), key=lambda x: x[1])
    return best_category[0], best_category[1]


def extract_all_matches(matches: Dict[str, float], threshold: float = 0.1) -> List[tuple[str, float]]:
    """
    Extract all categories above threshold, sorted by confidence.
    
    Args:
        matches: Dictionary of category -> confidence score
        threshold: Minimum confidence to include
        
    Returns:
        List of (category, confidence) tuples, sorted by confidence descending
    """
    filtered = [(k, v) for k, v in matches.items() if v >= threshold]
    return sorted(filtered, key=lambda x: x[1], reverse=True)
