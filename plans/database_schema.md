# Database Schema for Jazz Periodica

This document outlines the database schema for the `jazz-periodica` project, based on the requirements specified in GitHub Issue #6.

## Entities

The following entities and their attributes will be included in the database:

### Users
- `user_id` (PK): Unique identifier for the user.
- `email`: User's email address (unique).
- `name`: User's full name.
- `password_hash`: Hashed password for security.
- `subscription_status`: Current subscription status of the user.
- `created_at`: Timestamp for when the user account was created.

### Albums
- `album_id` (PK): Unique identifier for the album.
- `title`: Title of the album.
- `artist`: Artist(s) of the album.
- `release_year`: Year the album was released.
- `cover_image_url`: URL to the album's cover image.
- `streaming_link_spotify`: URL to the album on Spotify.
- `streaming_link_apple`: URL to the album on Apple Music.

### Recommendations
- `recommendation_id` (PK): Unique identifier for the recommendation.
- `user_id` (FK to Users): Foreign key referencing the `user_id` in the `Users` table.
- `album_id` (FK to Albums): Foreign key referencing the `album_id` in the `Albums` table.
- `sent_date`: Date the recommendation was sent.

## Relationships

- A `User` can have multiple `Recommendations`.
- An `Album` can be included in multiple `Recommendations`.
- `Recommendations` link `Users` to `Albums`.

## Schema Diagram

```mermaid
erDiagram
    Users ||--o{ Recommendations : has
    Albums ||--o{ Recommendations : includes

    Users {
        VARCHAR user_id PK
        VARCHAR email
        VARCHAR name
        VARCHAR password_hash
        VARCHAR subscription_status
        DATETIME created_at
    }

    Albums {
        VARCHAR album_id PK
        VARCHAR title
        VARCHAR artist
        INT release_year
        VARCHAR cover_image_url
        VARCHAR streaming_link_spotify
        VARCHAR streaming_link_apple
    }

    Recommendations {
        VARCHAR recommendation_id PK
        VARCHAR user_id FK
        VARCHAR album_id FK
        DATETIME sent_date
    }