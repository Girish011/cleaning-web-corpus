# API Design

## Overview

The Cleaning Workflow Planner Platform exposes a RESTful API via FastAPI for accessing workflow planning, procedure search, and corpus statistics. The API serves as the interface between clients (robots, agents, research tools) and the underlying workflow planner agent and data warehouse.

**Base URL:** `http://localhost:8000` (development)

**API Version:** `v1` (implicit, no versioning in path for MVP)

## Authentication

**MVP:** No authentication required (local development/research use)

**Future:** API key authentication for production deployments (out of scope for MVP)

## Endpoints

### 1. `POST /plan_workflow`

Plan a structured cleaning workflow from a natural language query.

#### Request

**Method:** `POST`

**Path:** `/plan_workflow`

**Content-Type:** `application/json`

**Request Body Schema:**

```json
{
  "query": "string (required)",
  "surface_type": "string (optional)",
  "dirt_type": "string (optional)",
  "cleaning_method": "string (optional)",
  "constraints": {
    "no_bleach": "boolean (optional)",
    "no_harsh_chemicals": "boolean (optional)",
    "preferred_method": "string | null (optional)",
    "gentle_only": "boolean (optional)"
  },
  "context": {
    "location": "string (optional)",
    "material": "string (optional)",
    "urgency": "string (optional, enum: 'low' | 'normal' | 'high')"
  }
}
```

**Field Descriptions:**

- `query` (required): Natural language description of cleaning scenario
  - Example: `"Remove red wine stain from wool carpet"`
- `surface_type` (optional): Pre-normalized surface type (if known)
  - Valid values: `"carpets_floors"`, `"clothes"`, `"pillows_bedding"`, `"upholstery"`, `"hard_surfaces"`, `"bathroom"`, `"appliances"`, `"outdoor"`
- `dirt_type` (optional): Pre-normalized dirt type (if known)
  - Valid values: `"stain"`, `"dust"`, `"grease"`, `"mold"`, `"pet_hair"`, `"odor"`, `"water_stain"`, `"ink"`
- `cleaning_method` (optional): Pre-normalized cleaning method (if known)
  - Valid values: `"vacuum"`, `"hand_wash"`, `"washing_machine"`, `"spot_clean"`, `"steam_clean"`, `"dry_clean"`, `"wipe"`, `"scrub"`
- `constraints` (optional): User constraints
  - `no_bleach`: Avoid bleach-based solutions
  - `no_harsh_chemicals`: Prefer gentle/natural cleaning methods
  - `preferred_method`: Prefer a specific method if available
  - `gentle_only`: Use only gentle methods (no scrubbing, minimal chemicals)
- `context` (optional): Additional context
  - `location`: Location context (e.g., `"living_room"`, `"kitchen"`)
  - `material`: Material type (e.g., `"wool"`, `"cotton"`, `"tile"`)
  - `urgency`: Urgency level (`"low"`, `"normal"`, `"high"`)

**Example Request:**

```json
{
  "query": "Remove red wine stain from wool carpet in living room",
  "constraints": {
    "no_bleach": true,
    "gentle_only": true
  },
  "context": {
    "location": "living_room",
    "material": "wool",
    "urgency": "normal"
  }
}
```

#### Response

**Status Code:** `200 OK`

**Content-Type:** `application/json`

**Response Body Schema:**

```json
{
  "workflow_id": "string (UUID)",
  "scenario": {
    "surface_type": "string",
    "dirt_type": "string",
    "cleaning_method": "string",
    "normalized_query": "string"
  },
  "workflow": {
    "estimated_duration_minutes": "integer",
    "difficulty": "string (enum: 'easy' | 'moderate' | 'hard')",
    "steps": [
      {
        "step_number": "integer",
        "action": "string",
        "description": "string",
        "tools": ["string"],
        "duration_seconds": "integer",
        "order": "integer"
      }
    ],
    "required_tools": [
      {
        "tool_name": "string",
        "category": "string",
        "quantity": "string",
        "is_required": "boolean",
        "alternative": "string | null (optional)"
      }
    ],
    "safety_notes": ["string"],
    "tips": ["string"]
  },
  "source_documents": [
    {
      "document_id": "string",
      "url": "string",
      "title": "string",
      "relevance_score": "float (0.0-1.0)",
      "extraction_confidence": "float (0.0-1.0)"
    }
  ],
  "metadata": {
    "generated_at": "string (ISO 8601 datetime)",
    "agent_version": "string",
    "extraction_method": "string",
    "confidence": "float (0.0-1.0)",
    "corpus_coverage": {
      "matching_documents": "integer",
      "total_combinations": "integer",
      "coverage_score": "float (0.0-1.0)"
    },
    "constraints_applied": ["string"],
    "method_selection": {
      "selected_method": "string",
      "alternatives_considered": ["string"],
      "selection_reason": "string"
    }
  }
}
```

**Example Response:**

```json
{
  "workflow_id": "550e8400-e29b-41d4-a716-446655440000",
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
        "description": "Use paper towels to blot up as much red wine as possible. Work from the outside of the stain toward the center.",
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
        "tool_name": "paper_towels",
        "category": "consumable",
        "quantity": "several",
        "is_required": true
      }
    ],
    "safety_notes": [
      "Test solution on a hidden area first to ensure it doesn't damage the carpet",
      "Use only cold water for wool carpets - hot water can cause shrinkage"
    ],
    "tips": [
      "Work from the outside of the stain toward the center to prevent spreading"
    ]
  },
  "source_documents": [
    {
      "document_id": "doc-123",
      "url": "https://example.com/carpet-stain-removal",
      "title": "How to Remove Stains from Carpets",
      "relevance_score": 0.92,
      "extraction_confidence": 0.85
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
    },
    "constraints_applied": ["no_bleach", "gentle_only"],
    "method_selection": {
      "selected_method": "spot_clean",
      "alternatives_considered": ["steam_clean"],
      "selection_reason": "Most documents (5), highest confidence, meets gentle_only constraint"
    }
  }
}
```

#### Error Cases

**400 Bad Request** - Invalid request body or missing required fields

```json
{
  "error": "validation_error",
  "message": "Missing required field: query",
  "details": {
    "field": "query",
    "issue": "required"
  }
}
```

**404 Not Found** - No matching procedures found in corpus

```json
{
  "error": "no_match_found",
  "message": "No procedures found for surface_type='outdoor', dirt_type='ink', cleaning_method='dry_clean'",
  "suggestions": [
    {
      "surface_type": "clothes",
      "dirt_type": "ink",
      "cleaning_method": "spot_clean",
      "similarity_score": 0.65
    }
  ]
}
```

**422 Unprocessable Entity** - Constraint conflict (e.g., user wants gentle method but corpus only has aggressive methods)

```json
{
  "error": "constraint_conflict",
  "message": "Cannot satisfy constraint 'gentle_only' for surface_type='bathroom', dirt_type='mold'. Available methods require scrubbing.",
  "available_methods": ["scrub"],
  "suggestions": [
    {
      "message": "Consider removing 'gentle_only' constraint or using alternative surface/dirt combination"
    }
  ]
}
```

**500 Internal Server Error** - Agent or database error

```json
{
  "error": "internal_error",
  "message": "Workflow planning failed due to database connection error",
  "request_id": "req-12345"
}
```

**503 Service Unavailable** - ClickHouse or LLM service unavailable

```json
{
  "error": "service_unavailable",
  "message": "ClickHouse database is temporarily unavailable",
  "retry_after": 30
}
```

---

### 2. `GET /search_procedures`

Search for cleaning procedures in the corpus by filters.

#### Request

**Method:** `GET`

**Path:** `/search_procedures`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `surface_type` | string | No | Filter by surface type |
| `dirt_type` | string | No | Filter by dirt type |
| `cleaning_method` | string | No | Filter by cleaning method |
| `limit` | integer | No | Maximum number of results (default: 20, max: 100) |
| `offset` | integer | No | Pagination offset (default: 0) |
| `min_confidence` | float | No | Minimum extraction confidence (0.0-1.0, default: 0.0) |
| `include_steps` | boolean | No | Include steps in response (default: true) |
| `include_tools` | boolean | No | Include tools in response (default: true) |

**Valid Values:**

- `surface_type`: `"carpets_floors"`, `"clothes"`, `"pillows_bedding"`, `"upholstery"`, `"hard_surfaces"`, `"bathroom"`, `"appliances"`, `"outdoor"`
- `dirt_type`: `"stain"`, `"dust"`, `"grease"`, `"mold"`, `"pet_hair"`, `"odor"`, `"water_stain"`, `"ink"`
- `cleaning_method`: `"vacuum"`, `"hand_wash"`, `"washing_machine"`, `"spot_clean"`, `"steam_clean"`, `"dry_clean"`, `"wipe"`, `"scrub"`

**Example Request:**

```
GET /search_procedures?surface_type=carpets_floors&dirt_type=stain&limit=10&min_confidence=0.7
```

#### Response

**Status Code:** `200 OK`

**Content-Type:** `application/json`

**Response Body Schema:**

```json
{
  "total": "integer",
  "limit": "integer",
  "offset": "integer",
  "procedures": [
    {
      "document_id": "string",
      "url": "string",
      "title": "string",
      "surface_type": "string",
      "dirt_type": "string",
      "cleaning_method": "string",
      "extraction_confidence": "float (0.0-1.0)",
      "extraction_method": "string",
      "steps": [
        {
          "step_order": "integer",
          "step_text": "string",
          "confidence": "float (0.0-1.0)"
        }
      ],
      "tools": [
        {
          "tool_name": "string",
          "category": "string",
          "confidence": "float (0.0-1.0)"
        }
      ],
      "fetched_at": "string (ISO 8601 datetime)",
      "word_count": "integer"
    }
  ]
}
```

**Example Response:**

```json
{
  "total": 5,
  "limit": 10,
  "offset": 0,
  "procedures": [
    {
      "document_id": "doc-123",
      "url": "https://example.com/carpet-stain-removal",
      "title": "How to Remove Stains from Carpets",
      "surface_type": "carpets_floors",
      "dirt_type": "stain",
      "cleaning_method": "spot_clean",
      "extraction_confidence": 0.85,
      "extraction_method": "rule_based",
      "steps": [
        {
          "step_order": 1,
          "step_text": "Blot excess liquid with paper towels",
          "confidence": 0.90
        },
        {
          "step_order": 2,
          "step_text": "Mix vinegar and water solution",
          "confidence": 0.85
        }
      ],
      "tools": [
        {
          "tool_name": "vinegar",
          "category": "chemical",
          "confidence": 0.88
        },
        {
          "tool_name": "paper_towels",
          "category": "consumable",
          "confidence": 0.92
        }
      ],
      "fetched_at": "2024-01-10T08:00:00Z",
      "word_count": 1250
    }
  ]
}
```

#### Error Cases

**400 Bad Request** - Invalid query parameters

```json
{
  "error": "validation_error",
  "message": "Invalid surface_type: 'invalid_type'. Valid values: carpets_floors, clothes, ...",
  "details": {
    "parameter": "surface_type",
    "value": "invalid_type"
  }
}
```

**422 Unprocessable Entity** - Invalid parameter combination

```json
{
  "error": "validation_error",
  "message": "Limit cannot exceed 100",
  "details": {
    "parameter": "limit",
    "value": 200,
    "max": 100
  }
}
```

**500 Internal Server Error** - Database error

```json
{
  "error": "internal_error",
  "message": "Database query failed",
  "request_id": "req-12345"
}
```

---

### 3. `GET /stats/coverage`

Get coverage statistics and matrices for the corpus.

#### Request

**Method:** `GET`

**Path:** `/stats/coverage`

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `surface_type` | string | No | Filter by surface type |
| `dirt_type` | string | No | Filter by dirt type |
| `cleaning_method` | string | No | Filter by cleaning method |
| `include_matrix` | boolean | No | Include coverage matrix in response (default: false) |
| `matrix_type` | string | No | Matrix type: `"surface_dirt"`, `"surface_method"`, `"dirt_method"`, `"full"` (default: `"full"`) |

**Example Request:**

```
GET /stats/coverage?include_matrix=true&matrix_type=surface_dirt
```

#### Response

**Status Code:** `200 OK`

**Content-Type:** `application/json`

**Response Body Schema:**

```json
{
  "summary": {
    "total_documents": "integer",
    "total_combinations": "integer",
    "total_possible_combinations": "integer (512 for 8×8×8)",
    "coverage_percentage": "float (0.0-100.0)",
    "surface_types_covered": "integer (out of 8)",
    "dirt_types_covered": "integer (out of 8)",
    "methods_covered": "integer (out of 8)"
  },
  "distributions": {
    "surface_types": {
      "carpets_floors": "integer",
      "clothes": "integer",
      ...
    },
    "dirt_types": {
      "stain": "integer",
      "dust": "integer",
      ...
    },
    "cleaning_methods": {
      "vacuum": "integer",
      "hand_wash": "integer",
      ...
    }
  },
  "coverage_matrix": {
    "type": "string",
    "matrix": {
      "surface_dirt": {
        "carpets_floors": {
          "stain": "integer",
          "dust": "integer",
          ...
        },
        ...
      },
      "surface_method": {
        ...
      },
      "dirt_method": {
        ...
      },
      "full": {
        "carpets_floors": {
          "stain": {
            "spot_clean": "integer",
            "vacuum": "integer",
            ...
          },
          ...
        },
        ...
      }
    }
  },
  "gaps": {
    "missing_surface_types": ["string"],
    "missing_dirt_types": ["string"],
    "missing_methods": ["string"],
    "low_coverage_combinations": [
      {
        "surface_type": "string",
        "dirt_type": "string",
        "cleaning_method": "string",
        "document_count": "integer"
      }
    ]
  }
}
```

**Example Response:**

```json
{
  "summary": {
    "total_documents": 50,
    "total_combinations": 25,
    "total_possible_combinations": 512,
    "coverage_percentage": 4.88,
    "surface_types_covered": 5,
    "dirt_types_covered": 4,
    "methods_covered": 6
  },
  "distributions": {
    "surface_types": {
      "carpets_floors": 8,
      "clothes": 15,
      "pillows_bedding": 5,
      "upholstery": 12,
      "hard_surfaces": 10
    },
    "dirt_types": {
      "stain": 20,
      "dust": 15,
      "grease": 8,
      "pet_hair": 7
    },
    "cleaning_methods": {
      "vacuum": 12,
      "hand_wash": 10,
      "spot_clean": 8,
      "steam_clean": 5,
      "wipe": 10,
      "scrub": 5
    }
  },
  "coverage_matrix": {
    "type": "full",
    "matrix": {
      "full": {
        "carpets_floors": {
          "stain": {
            "spot_clean": 3,
            "vacuum": 1
          },
          "dust": {
            "vacuum": 2
          }
        },
        "clothes": {
          "stain": {
            "hand_wash": 5,
            "spot_clean": 2
          }
        }
      }
    }
  },
  "gaps": {
    "missing_surface_types": ["bathroom", "appliances", "outdoor"],
    "missing_dirt_types": ["mold", "odor", "water_stain", "ink"],
    "missing_methods": ["dry_clean"],
    "low_coverage_combinations": [
      {
        "surface_type": "upholstery",
        "dirt_type": "pet_hair",
        "cleaning_method": "vacuum",
        "document_count": 1
      }
    ]
  }
}
```

#### Error Cases

**400 Bad Request** - Invalid query parameters

```json
{
  "error": "validation_error",
  "message": "Invalid matrix_type: 'invalid'. Valid values: surface_dirt, surface_method, dirt_method, full",
  "details": {
    "parameter": "matrix_type",
    "value": "invalid"
  }
}
```

**500 Internal Server Error** - Database error

```json
{
  "error": "internal_error",
  "message": "Failed to compute coverage statistics",
  "request_id": "req-12345"
}
```

---

## Common Error Response Format

All error responses follow this structure:

```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    // Additional error-specific details
  },
  "request_id": "string (optional, for tracking)"
}
```

**Standard HTTP Status Codes:**

- `200 OK` - Success
- `400 Bad Request` - Invalid request (validation errors)
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Semantic validation errors (constraint conflicts, etc.)
- `500 Internal Server Error` - Server-side errors
- `503 Service Unavailable` - External service (ClickHouse, LLM) unavailable

## Rate Limiting

**MVP:** No rate limiting (local development/research use)

**Future:** Rate limiting for production deployments (out of scope for MVP)

## CORS

**MVP:** CORS enabled for all origins (local development)

**Future:** Configurable CORS for production (out of scope for MVP)

## Response Times

**Expected Response Times (MVP):**

- `/plan_workflow`: 2-5 seconds (LLM + multiple database queries)
- `/search_procedures`: 100-500ms (single database query)
- `/stats/coverage`: 200-1000ms (aggregation queries, faster with materialized views)

## Pagination

**Pagination Strategy:**

- Use `limit` and `offset` query parameters
- Default `limit`: 20
- Maximum `limit`: 100
- Response includes `total`, `limit`, `offset` for client-side pagination

## Filtering

**Filter Strategy:**

- All filters are optional (AND logic when multiple filters provided)
- Filters are case-sensitive (use exact normalized values)
- Invalid filter values return `400 Bad Request` with validation error

## Data Consistency

- All data is read from ClickHouse warehouse (single source of truth)
- No caching in MVP (always fresh data)
- Future: Consider caching for `/stats/coverage` if performance becomes an issue

