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

| Column | Format | Type | Description |
|--------|--------|------|-------------|
| id | text | string | Unique identifier for the interaction |
| metadata | jsonb | json | Additional metadata about the interaction |
| created_at | timestamp with time zone | string | Timestamp when the interaction was created |
| updated_at | timestamp with time zone | string | Timestamp when the interaction was last updated |
| compliant | boolean | boolean | Flag indicating whether the interaction is compliant with policies |
| verifier | text | string | Identifier or name of the entity that verified the interaction |
| submitted_for_review | boolean | boolean | Flag indicating whether the interaction has been submitted for review |
| contributor_id | uuid | string | Unique identifier for the contributor/user |
| name | text | string | Name associated with the interaction or contributor |
| x | text | string | X (Twitter) handle or identifier |
| discord | text | string | Discord handle or identifier |
| linkedin | text | string | LinkedIn profile or identifier |
| schema_violation | boolean | boolean | Flag indicating whether the interaction violates the schema rules |
| action | public."Action" | string | Action taken or to be taken for this interaction |
| rules_violated | text[] | array | Array of rules that were violated in this interaction |
| instructions | text | string | Developer Message |
| input | text | string | User Message |
| output | text | string | Assistant Message |

### Data Types
- `text`: String data type for storing text values
- `jsonb`: JSON data stored in binary format for efficient querying and storage
- `timestamp with time zone`: Timestamp that includes timezone information
- `boolean`: Boolean value (true/false)
- `uuid`: Universally unique identifier
- `text[]`: Array of text values
- `public."Action"`: Enumerated type for action values

## Relationships

- `interactions.contributor_id` references `contributors.contributor_id`

## Notes

1. The `contributors` table uses `email` as a required field, suggesting it might be used as a unique identifier or for authentication.
2. The `interactions` table includes social media fields (name, x, discord, linkedin) which might be denormalized data from the contributors table or could be used for interactions from users who aren't registered contributors.
3. The `donations` table mentioned in the code was not found in the actual schema. It might be planned for future implementation or accessed through a different method.
4. Both tables use timestamps for tracking creation and modification times, with the `interactions` table using timezone-aware timestamps.
5. The `interactions` table now includes fields for storing conversation data: `instructions` (Developer Message), `input` (User Message), and `output` (Assistant Message).
6. The `rules_violated` field stores an array of text values indicating which rules were violated in an interaction.
7. The `action` field uses a custom enum type `public."Action"` to specify actions taken for an interaction.

## Schema Updates

The schema has been updated based on the latest database structure:

1. The `conversation` field previously mentioned has been replaced with specific message fields: `instructions`, `input`, and `output`.
2. Boolean fields are now explicitly typed as `boolean` rather than `bool`.
3. Timestamp fields are explicitly defined as `timestamp with time zone`.
4. Added new fields: `rules_violated`, `instructions`, `input`, and `output`.
5. The `action` field is now typed as `public."Action"` rather than plain text.