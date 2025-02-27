# Database Schema Documentation

## Interactions Table

The `interactions` table stores information about user interactions and conversations within the system.

| Field | Type | Description |
|-------|------|-------------|
| id | text | Unique identifier for the interaction |
| conversation | jsonb | JSON data containing the conversation details |
| metadata | jsonb | Additional metadata about the interaction |
| created_at | timestamptz | Timestamp when the interaction was created |
| updated_at | timestamptz | Timestamp when the interaction was last updated |
| compliant | bool | Flag indicating whether the interaction is compliant with policies |
| verifier | text | Identifier or name of the entity that verified the interaction |
| submitted_for_review | bool | Flag indicating whether the interaction has been submitted for review |
| contributor_id | uuid | Unique identifier for the contributor/user |
| name | text | Name associated with the interaction or contributor |
| x | text | X (Twitter) handle or identifier |
| discord | text | Discord handle or identifier |
| linkedin | text | LinkedIn profile or identifier |
| schema_violation | bool | Flag indicating whether the interaction violates the schema rules |
| action | text | Action taken or to be taken for this interaction |

### Data Types
- `text`: String data
- `jsonb`: JSON data stored in binary format for efficient querying and storage
- `timestamptz`: Timestamp with timezone information
- `bool`: Boolean value (true/false)
- `uuid`: Universally unique identifier
