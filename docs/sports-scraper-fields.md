# Score sports scraper reference

The scraper currently supports 23 active schedules across 16 unique sports.
Schedule pages use the URL pattern:

```text
https://cornellbigred.com/sports/{schedule_slug}/schedule
```

## Field naming

The scraper and Mongo/Python model use `snake_case`, but GraphQL uses
`camelCase` because the schema enables `auto_camelcase=True`. The examples in
this document use GraphQL names; the storage/Python name is shown in
parentheses when it differs.

## Supported sports and detail source

| Sport | Active schedule(s) | Detail source | Detail fields |
| --- | --- | --- | --- |
| Baseball | Men's | Box score | `boxScore`, `scoreBreakdown` |
| Basketball | Men's, Women's | Box score | `boxScore`, `scoreBreakdown` |
| Equestrian | Women's | Recap link | `recapLink`, recap article fields |
| Fencing | Women's | Recap link | `recapLink`, recap article fields |
| Field Hockey | Women's | Box score | `boxScore`, `scoreBreakdown` |
| Football | Men's | Box score | `boxScore`, `scoreBreakdown` |
| Golf | Men's | Recap link | `recapLink`, recap article fields |
| Gymnastics | Women's | Recap link | `recapLink`, recap article fields |
| Ice Hockey | Men's, Women's | Box score | `boxScore`, `scoreBreakdown` |
| Lacrosse | Men's, Women's | Box score | `boxScore`, `scoreBreakdown` |
| Polo | Men's, Women's | Recap link | `recapLink`, recap article fields |
| Soccer | Men's, Women's | Box score | `boxScore`, `scoreBreakdown` |
| Softball | Women's | Box score | `boxScore`, `scoreBreakdown` |
| Swimming & Diving | Men's, Women's | Recap link | `recapLink`, recap article fields |
| Track & Field | Men's, Women's | Recap link | `recapLink`, recap article fields |
| Wrestling | Men's | Recap link | `recapLink`, recap article fields |

The following sports are not currently active: Cross Country, Rowing, Sprint
Football, Sailing, Squash, Tennis, and Volleyball.

## General fields for every sport

These fields are stored on a game and exposed through GraphQL `GameType`.

| GraphQL field | Storage/Python field | Description |
| --- | --- | --- |
| `id` | `id` | Unique ID for the game. |
| `city` | `city` | City where the game takes place. |
| `date` | `date` | Game date, including the inferred season year. |
| `gender` | `gender` | `Mens` or `Womens`. |
| `location` | `location` | Venue name, when available. |
| `opponentId` | `opponent_id` | ID of the opposing team. |
| `result` | `result` | Schedule result text, such as a win/loss result or score. |
| `sport` | `sport` | Canonical sport name. |
| `state` | `state` | State or location region parsed from the schedule. |
| `time` | `time` | Local scheduled time; unavailable times are stored as `TBA`. |
| `utcDate` | `utc_date` | ISO-formatted UTC date/time, when conversion is possible. |
| `ticketLink` | `ticket_link` | Link to purchase tickets, when available. |

`team` is a nested `TeamType` object, not a string. It represents the
opponent identified by `opponentId`. Its available GraphQL fields are
`id`, `name`, `color`, `image`, and `b64Image` (`b64_image` in storage/Python).
Request nested fields like this:

```graphql
team {
  name
}
```

## Box-score fields

For box-score sports, `boxScore` (`box_score`) is a list of scoring events.
Only the fields listed for that sport are emitted.

| Sport | Fields in each `boxScore` event |
| --- | --- |
| Baseball | `team`, `period`, `description`, `corScore`, `oppScore` |
| Basketball | No scoring-event fields; when a box-score page is parsed, `boxScore` is an empty list |
| Field Hockey | `time`, `team`, `description`, `corScore`, `oppScore` |
| Football | `team`, `period`, `time`, `description`, `corScore`, `oppScore` |
| Ice Hockey | `team`, `period`, `time`, `scorer`, `assist`, `description`, `corScore`, `oppScore` |
| Lacrosse | `team`, `period`, `time`, `scorer`, `assist`, `description`, `corScore`, `oppScore` |
| Soccer | `time`, `team`, `description`, `corScore`, `oppScore` |
| Softball | `team`, `period`, `description`, `corScore`, `oppScore` |

### Box-score field definitions

| GraphQL field | Storage/Python field | Description |
| --- | --- | --- |
| `team` | `team` | Team abbreviation or label for the scoring event. |
| `period` | `period` | Period, quarter, half, or inning for the event. |
| `time` | `time` | Game-clock time of the event. |
| `description` | `description` | Human-readable description of the scoring play. |
| `scorer` | `scorer` | Player credited with scoring. |
| `assist` | `assist` | Player credited with an assist. |
| `corScore` | `cor_score` | Cornell's cumulative score after the event. |
| `oppScore` | `opp_score` | Opponent's cumulative score after the event. |

`scoreBy` (`score_by`) exists in the GraphQL type but is not currently
populated by any sport parser.

## Score-breakdown fields

For box-score sports, `scoreBreakdown` (`score_breakdown`) is a two-dimensional
list of strings. It has no nested named fields; request it directly.

For baseball and softball, each inner list contains the inning scores followed
by the raw box-score columns `R`, `H`, and `E`:

```text
[inning_1, inning_2, ..., inning_n, R, H, E]
```

`R` is the final runs/score, `H` is hits, and `E` is errors. The frontend may
label the final-score column `F`, but the source box score uses `R`. Other
box-score sports contain their period scores followed by the final score, with
no `H`/`E` columns.

Each inner list therefore contains the source table's score columns in order:

```text
[
  [period_score_1, period_score_2, ..., final_score, ...],
  [period_score_1, period_score_2, ..., final_score, ...]
]
```

| Sport | Score columns represented |
| --- | --- |
| Baseball | Innings, final runs, hits, and errors (`R`, `H`, `E`) |
| Basketball | Periods and final score; the source `Records` column is excluded |
| Field Hockey | Periods and final score |
| Football | Quarters and final score |
| Ice Hockey | Periods and final score |
| Lacrosse | Periods and final score |
| Soccer | Period/half scores and final score |
| Softball | Innings, final runs, hits, and errors (`R`, `H`, `E`) |

The team rows are ordered with Cornell first for stored home-game data.
Recap-link sports do not populate `boxScore` or `scoreBreakdown`.

## Recap-link fields

Recap-link sports populate these fields when the schedule and linked story
page provide them:

| GraphQL field | Storage/Python field | Description |
| --- | --- | --- |
| `recapLink` | `recap_link` | Link to the schedule recap/details page. |
| `recapArticleTitle` | `recap_article_title` | Headline from the linked story. |
| `recapPublishedAt` | `recap_published_at` | Published date/time from the linked story. |
| `recapArticleImage` | `recap_article_image` | Primary image URL from the linked story. |

## Example GraphQL selection

```graphql
gamesBySport(sport: "Soccer") {
  sport
  opponentId
  date
  time
  ticketLink
  team {
    name
  }
  boxScore {
    time
    team
    description
    corScore
    oppScore
  }
  scoreBreakdown
}
```
