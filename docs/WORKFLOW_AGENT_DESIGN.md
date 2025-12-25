# Workflow Planner Agent Design

## Purpose

The Workflow Planner Agent is a LangChain-based intelligent agent that generates structured cleaning workflows for robots and AI agents. It serves as the core planning component of the Cleaning Workflow Planner Platform, translating natural language user queries into actionable, structured cleaning procedures.

**Key Capabilities:**
- Parse natural language cleaning scenarios (e.g., "Red wine stain on wool carpet")
- Normalize inputs to structured dimensions (surface_type, dirt_type, cleaning_method)
- Retrieve relevant procedures from the corpus via ClickHouse queries
- Compose multi-step workflows with tools, safety notes, and source references
- Ground responses in the actual corpus data (not hallucinated procedures)

**Target Users:**
- Robotics engineers building cleaning robots
- AI agents that need structured cleaning instructions
- Research teams studying procedural knowledge extraction

## Input Schema

### User Query (Natural Language)

The agent accepts free-form natural language queries describing cleaning scenarios:

**Examples:**
- "How do I remove red wine from a wool carpet?"
- "Clean grease off kitchen countertops"
- "Remove pet hair from upholstery, no harsh chemicals"
- "Bathroom mold removal with steam cleaning"

### Optional Structured Fields

For programmatic access, the agent also accepts structured input:

```json
{
  "query": "Remove red wine stain from wool carpet",
  "surface_type": "carpets_floors",  // Optional: pre-normalized
  "dirt_type": "stain",              // Optional: pre-normalized
  "cleaning_method": null,            // Optional: let agent choose
  "constraints": {
    "no_bleach": true,
    "no_harsh_chemicals": false,
    "preferred_method": null
  },
  "context": {
    "location": "living_room",
    "material": "wool",
    "urgency": "normal"
  }
}
```

### Input Processing

1. **Query Parsing**: Extract surface, dirt, and method mentions from natural language
2. **Normalization**: Map extracted terms to canonical values (e.g., "sofa" → "upholstery")
3. **Constraint Extraction**: Identify constraints (no bleach, gentle only, etc.)
4. **Context Enrichment**: Extract additional context (material type, location, urgency)

## Output Schema

The agent returns a structured workflow plan:

```json
{
  "workflow_id": "uuid-here",
  "scenario": {
    "surface_type": "carpets_floors",
    "dirt_type": "stain",
    "cleaning_method": "spot_clean",
    "normalized_query": "Remove stain from carpet using spot cleaning method"
  },
  "workflow": {
    "estimated_duration_minutes": 15,
    "difficulty": "moderate",
    "steps": [
      {
        "step_number": 1,
        "action": "Blot excess liquid",
        "description": "Use paper towels to blot up as much liquid as possible. Do not rub, as this can spread the stain.",
        "tools": ["paper_towels"],
        "duration_seconds": 60,
        "order": 1
      },
      {
        "step_number": 2,
        "action": "Prepare cleaning solution",
        "description": "Mix 1 part white vinegar with 2 parts cold water in a spray bottle.",
        "tools": ["vinegar", "cold_water", "spray_bottle"],
        "duration_seconds": 120,
        "order": 2
      },
      {
        "step_number": 3,
        "action": "Apply solution",
        "description": "Spray the solution onto the stain, covering the entire affected area.",
        "tools": ["spray_bottle"],
        "duration_seconds": 30,
        "order": 3
      },
      {
        "step_number": 4,
        "action": "Let sit",
        "description": "Allow the solution to sit for 10 minutes to break down the stain.",
        "tools": [],
        "duration_seconds": 600,
        "order": 4
      },
      {
        "step_number": 5,
        "action": "Blot dry",
        "description": "Blot the area with clean paper towels until dry. Repeat if necessary.",
        "tools": ["paper_towels"],
        "duration_seconds": 180,
        "order": 5
      }
    ],
    "required_tools": [
      {
        "tool_name": "vinegar",
        "category": "chemical",
        "quantity": "1 cup",
        "is_required": true
      },
      {
        "tool_name": "paper_towels",
        "category": "consumable",
        "quantity": "several",
        "is_required": true
      },
      {
        "tool_name": "spray_bottle",
        "category": "equipment",
        "quantity": "1",
        "is_required": true
      }
    ],
    "safety_notes": [
      "Test solution on a hidden area first to ensure it doesn't damage the carpet",
      "Do not use hot water, as it can set the stain",
      "Ventilate the area well during cleaning"
    ],
    "tips": [
      "Work from the outside of the stain toward the center to prevent spreading",
      "For older stains, you may need to repeat the process"
    ]
  },
  "source_documents": [
    {
      "document_id": "doc-123",
      "url": "https://example.com/carpet-stain-removal",
      "title": "How to Remove Stains from Carpets",
      "relevance_score": 0.92,
      "extraction_confidence": 0.85
    },
    {
      "document_id": "doc-456",
      "url": "https://example.com/wool-carpet-care",
      "title": "Wool Carpet Cleaning Guide",
      "relevance_score": 0.88,
      "extraction_confidence": 0.90
    }
  ],
  "metadata": {
    "generated_at": "2024-01-15T10:30:00Z",
    "agent_version": "1.0",
    "extraction_method": "llm",
    "confidence": 0.87,
    "corpus_coverage": {
      "matching_documents": 5,
      "total_combinations": 1,
      "coverage_score": 1.0
    }
  }
}
```

### Output Field Descriptions

- **`workflow_id`**: Unique identifier for this workflow plan
- **`scenario`**: Normalized input scenario (surface, dirt, method)
- **`workflow.steps`**: Ordered list of cleaning steps with actions, descriptions, tools, and durations
- **`workflow.required_tools`**: Complete list of tools needed, with quantities and categories
- **`workflow.safety_notes`**: Important safety warnings and precautions
- **`workflow.tips`**: Optional tips for better results
- **`source_documents`**: References to corpus documents used to generate the workflow
- **`metadata`**: Generation metadata, confidence scores, and corpus coverage info

## Conceptual Tools

The agent uses a set of tools to interact with the data warehouse and compose workflows:

### 1. `fetch_methods`

**Purpose:** Retrieve available cleaning methods for a given surface × dirt combination.

**Input:**
```json
{
  "surface_type": "carpets_floors",
  "dirt_type": "stain"
}
```

**Output:**
```json
{
  "methods": [
    {
      "cleaning_method": "spot_clean",
      "document_count": 5,
      "avg_steps": 6,
      "avg_confidence": 0.85,
      "common_tools": ["vinegar", "paper_towels", "spray_bottle"]
    },
    {
      "cleaning_method": "steam_clean",
      "document_count": 2,
      "avg_steps": 4,
      "avg_confidence": 0.78,
      "common_tools": ["steam_cleaner", "cleaning_solution"]
    }
  ]
}
```

**ClickHouse Query:** Queries `fct_cleaning_procedures` filtered by surface_key and dirt_key.

### 2. `fetch_steps`

**Purpose:** Retrieve cleaning steps for a specific surface × dirt × method combination.

**Input:**
```json
{
  "surface_type": "carpets_floors",
  "dirt_type": "stain",
  "cleaning_method": "spot_clean",
  "limit": 10
}
```

**Output:**
```json
{
  "steps": [
    {
      "step_order": 1,
      "step_text": "Blot excess liquid with paper towels",
      "document_id": "doc-123",
      "confidence": 0.90
    },
    {
      "step_order": 2,
      "step_text": "Mix vinegar and water solution",
      "document_id": "doc-123",
      "confidence": 0.85
    }
  ],
  "total_steps": 25,
  "unique_documents": 5
}
```

**ClickHouse Query:** Queries `steps` table joined with `raw_documents`, filtered by surface/dirt/method, ordered by step_order.

### 3. `fetch_tools`

**Purpose:** Retrieve recommended tools for a specific combination.

**Input:**
```json
{
  "surface_type": "carpets_floors",
  "dirt_type": "stain",
  "cleaning_method": "spot_clean"
}
```

**Output:**
```json
{
  "tools": [
    {
      "tool_name": "vinegar",
      "usage_count": 8,
      "avg_confidence": 0.88,
      "category": "chemical",
      "is_primary": true,
      "mentioned_in_steps": ["step-1", "step-2"]
    },
    {
      "tool_name": "paper_towels",
      "usage_count": 10,
      "avg_confidence": 0.92,
      "category": "consumable",
      "is_primary": true,
      "mentioned_in_steps": ["step-1", "step-5"]
    }
  ],
  "total_tools": 12
}
```

**ClickHouse Query:** Queries `fct_tool_usage` filtered by surface/dirt/method, aggregated by tool_name.

### 4. `fetch_reference_context`

**Purpose:** Retrieve full document context for reference and citation.

**Input:**
```json
{
  "document_ids": ["doc-123", "doc-456"],
  "include_steps": true,
  "include_tools": true
}
```

**Output:**
```json
{
  "documents": [
    {
      "document_id": "doc-123",
      "url": "https://example.com/carpet-stain-removal",
      "title": "How to Remove Stains from Carpets",
      "surface_type": "carpets_floors",
      "dirt_type": "stain",
      "cleaning_method": "spot_clean",
      "steps": [...],
      "tools": [...],
      "extraction_confidence": 0.85
    }
  ]
}
```

**ClickHouse Query:** Queries `raw_documents` with joins to `steps` and `tools` tables.

### 5. `search_similar_scenarios` (Optional)

**Purpose:** Find similar scenarios when exact match is not available.

**Input:**
```json
{
  "surface_type": "carpets_floors",
  "dirt_type": "stain",
  "fuzzy_match": true
}
```

**Output:**
```json
{
  "similar_combinations": [
    {
      "surface_type": "upholstery",
      "dirt_type": "stain",
      "cleaning_method": "spot_clean",
      "similarity_score": 0.75
    }
  ]
}
```

**ClickHouse Query:** Uses similarity search or fallback logic to find related combinations.

## Planning Strategy

The agent follows a structured planning strategy:

### Phase 1: Parse & Normalize

1. **Extract Entities**: Use LLM or NER to extract surface, dirt, and method mentions from query
2. **Normalize Values**: Map extracted terms to canonical values using lookup tables:
   - "sofa", "couch", "upholstered furniture" → "upholstery"
   - "red wine", "coffee", "ink" → "stain"
   - "spot treat", "spot clean" → "spot_clean"
3. **Extract Constraints**: Identify user constraints (no bleach, gentle only, etc.)
4. **Validate**: Check if normalized values are valid (in supported categories)

### Phase 2: Fetch & Retrieve

1. **Check Coverage**: Query `fetch_methods` to see available methods for the combination
2. **Select Method**: 
   - If user specified method, use it (if available)
   - If multiple methods available, choose based on:
     - Document count (more documents = more reliable)
     - Average confidence scores
     - User constraints (e.g., prefer "spot_clean" over "scrub" if user wants gentle)
3. **Retrieve Steps**: Call `fetch_steps` for the selected combination
4. **Retrieve Tools**: Call `fetch_tools` for the combination
5. **Get References**: Call `fetch_reference_context` for top documents

### Phase 3: Compose & Generate

1. **Deduplicate Steps**: Merge similar steps from multiple documents
2. **Order Steps**: Ensure logical sequence (prep → apply → wait → clean → dry)
3. **Enrich Descriptions**: Use LLM to create clear, actionable step descriptions
4. **Aggregate Tools**: Combine tools from all steps, mark required vs optional
5. **Generate Safety Notes**: Extract safety warnings from source documents
6. **Add Tips**: Include helpful tips from corpus
7. **Calculate Metadata**: Compute confidence, duration estimates, difficulty

### Phase 4: Validate & Refine

1. **Check Completeness**: Ensure workflow has at least 3-5 steps
2. **Validate Tools**: Ensure all tools mentioned in steps are in required_tools list
3. **Check Constraints**: Verify workflow respects user constraints (no bleach, etc.)
4. **Quality Check**: Ensure confidence scores meet minimum thresholds
5. **Fallback Logic**: If no exact match, try `search_similar_scenarios` and adapt

### Error Handling

- **No Match Found**: Return informative error with suggestions for similar scenarios
- **Low Confidence**: Warn user that workflow is based on limited data
- **Missing Tools**: Flag steps that require tools not in corpus
- **Constraint Violation**: If user constraints conflict with corpus data, explain the conflict

## Few-Shot Examples

### Example 1: Simple Stain Removal

**Input:**
```
User Query: "How do I remove a red wine stain from my wool carpet?"
```

**Agent Reasoning:**
```
1. Parse: surface="carpet" → "carpets_floors", dirt="red wine stain" → "stain", method=null
2. Fetch methods: Found "spot_clean" (5 docs, avg confidence 0.85) and "steam_clean" (2 docs)
3. Select method: "spot_clean" (more documents, suitable for stains)
4. Fetch steps: Retrieved 25 steps from 5 documents
5. Fetch tools: Found ["vinegar", "paper_towels", "spray_bottle", "cold_water"]
6. Compose: Deduplicated to 5 key steps, ordered logically
7. Generate: Created workflow with safety notes about testing on hidden area
```

**Output:**
```json
{
  "workflow_id": "wf-001",
  "scenario": {
    "surface_type": "carpets_floors",
    "dirt_type": "stain",
    "cleaning_method": "spot_clean",
    "normalized_query": "Remove stain from carpet using spot cleaning method"
  },
  "workflow": {
    "estimated_duration_minutes": 15,
    "difficulty": "moderate",
    "steps": [
      {
        "step_number": 1,
        "action": "Blot excess liquid",
        "description": "Use paper towels to blot up as much red wine as possible. Work from the outside of the stain toward the center. Do not rub, as this can spread the stain deeper into the carpet fibers.",
        "tools": ["paper_towels"],
        "duration_seconds": 60,
        "order": 1
      },
      {
        "step_number": 2,
        "action": "Prepare cleaning solution",
        "description": "Mix 1 part white vinegar with 2 parts cold water in a spray bottle. For wool carpets, use cold water only (hot water can damage wool fibers).",
        "tools": ["vinegar", "cold_water", "spray_bottle"],
        "duration_seconds": 120,
        "order": 2
      },
      {
        "step_number": 3,
        "action": "Test solution",
        "description": "Test the solution on a hidden area of the carpet (e.g., under furniture) to ensure it doesn't cause discoloration or damage.",
        "tools": ["spray_bottle"],
        "duration_seconds": 30,
        "order": 3
      },
      {
        "step_number": 4,
        "action": "Apply solution to stain",
        "description": "Spray the vinegar solution onto the stain, covering the entire affected area. Do not oversaturate.",
        "tools": ["spray_bottle"],
        "duration_seconds": 30,
        "order": 4
      },
      {
        "step_number": 5,
        "action": "Let solution sit",
        "description": "Allow the solution to sit for 10 minutes to break down the wine stain. Do not let it dry completely.",
        "tools": [],
        "duration_seconds": 600,
        "order": 5
      },
      {
        "step_number": 6,
        "action": "Blot dry",
        "description": "Blot the area with clean, dry paper towels until the carpet is dry. Repeat the process if the stain persists.",
        "tools": ["paper_towels"],
        "duration_seconds": 180,
        "order": 6
      }
    ],
    "required_tools": [
      {
        "tool_name": "white_vinegar",
        "category": "chemical",
        "quantity": "1 cup",
        "is_required": true
      },
      {
        "tool_name": "cold_water",
        "category": "consumable",
        "quantity": "2 cups",
        "is_required": true
      },
      {
        "tool_name": "paper_towels",
        "category": "consumable",
        "quantity": "several",
        "is_required": true
      },
      {
        "tool_name": "spray_bottle",
        "category": "equipment",
        "quantity": "1",
        "is_required": true
      }
    ],
    "safety_notes": [
      "Always test cleaning solutions on a hidden area of wool carpet first, as wool can be sensitive to certain chemicals",
      "Use only cold water for wool carpets - hot water can cause shrinkage and damage",
      "Do not rub or scrub wool carpet aggressively, as this can damage the fibers",
      "Ensure good ventilation when using vinegar"
    ],
    "tips": [
      "Work from the outside of the stain toward the center to prevent spreading",
      "For older or set-in stains, you may need to repeat the process 2-3 times",
      "If the stain persists, consider professional cleaning for valuable wool carpets"
    ]
  },
  "source_documents": [
    {
      "document_id": "doc-123",
      "url": "https://example.com/carpet-stain-removal",
      "title": "How to Remove Stains from Carpets",
      "relevance_score": 0.92,
      "extraction_confidence": 0.85
    },
    {
      "document_id": "doc-456",
      "url": "https://example.com/wool-carpet-care",
      "title": "Wool Carpet Cleaning Guide",
      "relevance_score": 0.88,
      "extraction_confidence": 0.90
    }
  ],
  "metadata": {
    "generated_at": "2024-01-15T10:30:00Z",
    "agent_version": "1.0",
    "extraction_method": "llm",
    "confidence": 0.87,
    "corpus_coverage": {
      "matching_documents": 5,
      "total_combinations": 1,
      "coverage_score": 1.0
    }
  }
}
```

### Example 2: Constraint-Based Query

**Input:**
```
User Query: "Remove pet hair from my couch, but I don't want to use any harsh chemicals"
```

**Agent Reasoning:**
```
1. Parse: surface="couch" → "upholstery", dirt="pet hair" → "pet_hair", method=null, constraint="no harsh chemicals"
2. Fetch methods: Found "vacuum" (8 docs) and "steam_clean" (3 docs, but may use chemicals)
3. Select method: "vacuum" (meets constraint, more documents)
4. Fetch steps: Retrieved 15 steps from 8 documents
5. Fetch tools: Found ["vacuum", "lint_roller", "rubber_gloves", "damp_cloth"]
6. Compose: Focused on mechanical methods (vacuum, lint roller), excluded chemical-based steps
7. Generate: Emphasized natural, chemical-free approach
```

**Output:**
```json
{
  "workflow_id": "wf-002",
  "scenario": {
    "surface_type": "upholstery",
    "dirt_type": "pet_hair",
    "cleaning_method": "vacuum",
    "normalized_query": "Remove pet hair from upholstery using vacuum method (no harsh chemicals)"
  },
  "workflow": {
    "estimated_duration_minutes": 20,
    "difficulty": "easy",
    "steps": [
      {
        "step_number": 1,
        "action": "Remove loose debris",
        "description": "Remove any large debris or objects from the couch cushions and surface.",
        "tools": [],
        "duration_seconds": 30,
        "order": 1
      },
      {
        "step_number": 2,
        "action": "Vacuum with upholstery attachment",
        "description": "Use a vacuum cleaner with an upholstery attachment to vacuum the entire couch surface. Work in sections, going over each area multiple times in different directions to lift embedded pet hair.",
        "tools": ["vacuum", "upholstery_attachment"],
        "duration_seconds": 600,
        "order": 2
      },
      {
        "step_number": 3,
        "action": "Use lint roller",
        "description": "Go over the couch with a lint roller, especially in crevices and corners where the vacuum may have missed hair.",
        "tools": ["lint_roller"],
        "duration_seconds": 300,
        "order": 3
      },
      {
        "step_number": 4,
        "action": "Damp cloth method (optional)",
        "description": "For stubborn hair, lightly dampen a microfiber cloth and wipe the surface. The slight moisture helps lift hair without using chemicals.",
        "tools": ["microfiber_cloth", "water"],
        "duration_seconds": 180,
        "order": 4
      }
    ],
    "required_tools": [
      {
        "tool_name": "vacuum",
        "category": "equipment",
        "quantity": "1",
        "is_required": true
      },
      {
        "tool_name": "upholstery_attachment",
        "category": "equipment",
        "quantity": "1",
        "is_required": true
      },
      {
        "tool_name": "lint_roller",
        "category": "consumable",
        "quantity": "1",
        "is_required": true
      },
      {
        "tool_name": "microfiber_cloth",
        "category": "consumable",
        "quantity": "1",
        "is_required": false
      }
    ],
    "safety_notes": [
      "This method uses no harsh chemicals, making it safe for households with pets and children",
      "Test the damp cloth method on a hidden area first if your couch has delicate fabric",
      "Ensure the vacuum is set to an appropriate suction level for upholstery to avoid damage"
    ],
    "tips": [
      "Vacuum in multiple directions (up-down, left-right, diagonal) to catch hair from all angles",
      "For best results, vacuum regularly (weekly) to prevent pet hair buildup",
      "Consider using a rubber glove method: put on a rubber glove, dampen slightly, and wipe - the rubber creates static that attracts hair"
    ]
  },
  "source_documents": [
    {
      "document_id": "doc-789",
      "url": "https://example.com/upholstery-pet-hair",
      "title": "How to Remove Pet Hair from Upholstery",
      "relevance_score": 0.95,
      "extraction_confidence": 0.88
    }
  ],
  "metadata": {
    "generated_at": "2024-01-15T10:35:00Z",
    "agent_version": "1.0",
    "extraction_method": "llm",
    "confidence": 0.90,
    "constraints_applied": ["no_harsh_chemicals"],
    "corpus_coverage": {
      "matching_documents": 8,
      "total_combinations": 1,
      "coverage_score": 1.0
    }
  }
}
```

### Example 3: Method Selection with Multiple Options

**Input:**
```
User Query: "Clean mold from bathroom tiles"
```

**Agent Reasoning:**
```
1. Parse: surface="bathroom tiles" → "bathroom", dirt="mold" → "mold", method=null
2. Fetch methods: Found "scrub" (12 docs, high confidence), "steam_clean" (5 docs), "wipe" (3 docs)
3. Select method: "scrub" (most documents, most appropriate for mold)
4. Fetch steps: Retrieved 40 steps from 12 documents
5. Fetch tools: Found ["bleach", "vinegar", "scrub_brush", "rubber_gloves", "spray_bottle"]
6. Compose: Combined steps from multiple sources, prioritized safety (ventilation, gloves)
7. Generate: Emphasized safety due to mold and cleaning chemicals
```

**Output:**
```json
{
  "workflow_id": "wf-003",
  "scenario": {
    "surface_type": "bathroom",
    "dirt_type": "mold",
    "cleaning_method": "scrub",
    "normalized_query": "Remove mold from bathroom using scrubbing method"
  },
  "workflow": {
    "estimated_duration_minutes": 30,
    "difficulty": "moderate",
    "steps": [
      {
        "step_number": 1,
        "action": "Ventilate area",
        "description": "Open windows and turn on exhaust fan to ensure good ventilation. Mold removal can release spores and cleaning chemicals can produce fumes.",
        "tools": [],
        "duration_seconds": 60,
        "order": 1
      },
      {
        "step_number": 2,
        "action": "Put on protective gear",
        "description": "Wear rubber gloves, safety goggles, and a mask to protect yourself from mold spores and cleaning chemicals.",
        "tools": ["rubber_gloves", "safety_goggles", "mask"],
        "duration_seconds": 60,
        "order": 2
      },
      {
        "step_number": 3,
        "action": "Prepare cleaning solution",
        "description": "Mix 1 part bleach with 4 parts water in a spray bottle. Alternatively, use undiluted white vinegar for a less harsh option.",
        "tools": ["bleach", "water", "spray_bottle"],
        "duration_seconds": 120,
        "order": 3
      },
      {
        "step_number": 4,
        "action": "Apply solution to mold",
        "description": "Spray the cleaning solution directly onto the moldy areas. Ensure complete coverage, but avoid oversaturating.",
        "tools": ["spray_bottle"],
        "duration_seconds": 60,
        "order": 4
      },
      {
        "step_number": 5,
        "action": "Let solution sit",
        "description": "Allow the solution to sit for 10-15 minutes to kill mold and loosen it from the surface.",
        "tools": [],
        "duration_seconds": 900,
        "order": 5
      },
      {
        "step_number": 6,
        "action": "Scrub with brush",
        "description": "Use a stiff-bristled scrub brush to scrub the moldy areas. Apply firm pressure and work in circular motions. For grout lines, use a smaller brush or old toothbrush.",
        "tools": ["scrub_brush", "toothbrush"],
        "duration_seconds": 600,
        "order": 6
      },
      {
        "step_number": 7,
        "action": "Rinse thoroughly",
        "description": "Rinse the area thoroughly with clean water to remove all cleaning solution and mold residue. Use a clean cloth or sponge to wipe away residue.",
        "tools": ["water", "sponge", "clean_cloth"],
        "duration_seconds": 180,
        "order": 7
      },
      {
        "step_number": 8,
        "action": "Dry completely",
        "description": "Dry the area completely with a clean towel or allow to air dry. Mold thrives in moisture, so ensuring the area is dry helps prevent regrowth.",
        "tools": ["towel"],
        "duration_seconds": 300,
        "order": 8
      }
    ],
    "required_tools": [
      {
        "tool_name": "bleach",
        "category": "chemical",
        "quantity": "1 cup",
        "is_required": true,
        "alternative": "white_vinegar"
      },
      {
        "tool_name": "water",
        "category": "consumable",
        "quantity": "4 cups",
        "is_required": true
      },
      {
        "tool_name": "spray_bottle",
        "category": "equipment",
        "quantity": "1",
        "is_required": true
      },
      {
        "tool_name": "scrub_brush",
        "category": "equipment",
        "quantity": "1",
        "is_required": true
      },
      {
        "tool_name": "rubber_gloves",
        "category": "safety",
        "quantity": "1 pair",
        "is_required": true
      },
      {
        "tool_name": "safety_goggles",
        "category": "safety",
        "quantity": "1",
        "is_required": true
      },
      {
        "tool_name": "mask",
        "category": "safety",
        "quantity": "1",
        "is_required": true
      }
    ],
    "safety_notes": [
      "CRITICAL: Ensure excellent ventilation when using bleach. Never mix bleach with ammonia or other cleaning products - this can produce toxic fumes",
      "Wear protective gear (gloves, goggles, mask) to protect from mold spores and chemical exposure",
      "If you have respiratory issues, consider using vinegar instead of bleach",
      "Keep the area well-ventilated for at least 30 minutes after cleaning",
      "If mold covers a large area (more than 10 square feet), consider consulting a professional"
    ],
    "tips": [
      "For prevention, ensure bathroom has good ventilation and fix any leaks that cause moisture",
      "Regular cleaning with vinegar can help prevent mold regrowth",
      "For stubborn mold in grout, you may need to repeat the process 2-3 times",
      "Consider using a dehumidifier in the bathroom to reduce moisture levels"
    ]
  },
  "source_documents": [
    {
      "document_id": "doc-101",
      "url": "https://example.com/bathroom-mold-removal",
      "title": "How to Remove Mold from Bathroom Tiles",
      "relevance_score": 0.94,
      "extraction_confidence": 0.90
    },
    {
      "document_id": "doc-102",
      "url": "https://example.com/mold-cleaning-safety",
      "title": "Safe Mold Removal Guide",
      "relevance_score": 0.91,
      "extraction_confidence": 0.88
    }
  ],
  "metadata": {
    "generated_at": "2024-01-15T10:40:00Z",
    "agent_version": "1.0",
    "extraction_method": "llm",
    "confidence": 0.92,
    "corpus_coverage": {
      "matching_documents": 12,
      "total_combinations": 1,
      "coverage_score": 1.0
    },
    "method_selection": {
      "selected_method": "scrub",
      "alternatives_considered": ["steam_clean", "wipe"],
      "selection_reason": "Most documents (12), highest confidence, most appropriate for mold removal"
    }
  }
}
```

## Implementation Considerations

### LangChain Integration

- Use **LangChain Agents** with tool calling capabilities
- Implement tools as **LangChain Tools** that wrap ClickHouse queries
- Use **LLM** (GPT-4, Claude, or local model) for query parsing and workflow composition
- Implement **Memory** for conversation context if needed

### Error Handling

- **No Match**: Return helpful error with suggestions for similar scenarios
- **Low Confidence**: Warn user and provide alternative methods if available
- **Constraint Conflicts**: Explain why constraints cannot be met and suggest alternatives
- **Database Errors**: Graceful fallback with cached results or simplified workflows

### Performance

- Cache frequently accessed combinations
- Use ClickHouse materialized views for fast method/tool lookups
- Batch tool calls when possible
- Implement request timeouts for long-running queries

### Evaluation

- Track workflow generation success rate
- Measure user satisfaction (if feedback available)
- Compare generated workflows against reference procedures
- Monitor corpus coverage impact on workflow quality

