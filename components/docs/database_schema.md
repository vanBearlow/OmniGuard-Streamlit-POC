# OMNIGUARD Database Schema Documentation

This document provides an overview of the database tables used in the OMNIGUARD application.

## Table Definitions

Based on the actual schema from Supabase:

### contributors

Stores information about users/contributors.

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| email | text | NO | null | Contributor's email address (required) |
| contributor_id | uuid | YES | null | Unique identifier for the contributor |
| created_at | timestamp without time zone | YES | now() | When the record was created |
| name | text | YES | null | Contributor's name |
| x | text | YES | null | Contributor's X (Twitter) handle |
| discord | text | YES | null | Contributor's Discord handle |
| linkedin | text | YES | null | Contributor's LinkedIn profile |

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

## Relationships

- `interactions.contributor_id` references `contributors.contributor_id`

## Notes

1. The `contributors` table uses `email` as a required field, suggesting it might be used as a unique identifier or for authentication.
2. The `interactions` table includes social media fields (name, x, discord, linkedin) which might be denormalized data from the contributors table or could be used for interactions from users who aren't registered contributors.
3. The `donations` table mentioned in the code was not found in the actual schema. It might be planned for future implementation or accessed through a different method.
4. Both tables use timestamps for tracking creation and modification times, with the `interactions` table using timezone-aware timestamps.
5. The `conversation` field in the `interactions` table replaces the previously identified `messages` field, but serves a similar purpose.

## Schema Differences from Code Analysis

Some differences were noted between the code references and the actual schema:

1. In the code, `messages` is referenced, but the actual schema uses `conversation`
2. The code references a `donations` table which is not present in the current schema
3. The actual schema includes social media fields in both tables that weren't apparent from the code analysis
4. The `contributor_id` is a UUID type rather than text as inferred from the code

After retrieving the actual schema from Supabase, please update this document with the accurate column definitions, constraints, and relationships. 