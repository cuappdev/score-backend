# score-backend

Tech stack:

1. Python
2. MongoDB
3. GraphQL

## Installation

Clone the project with

`git clone https://github.com/cuappdev/score-backend.git`

After cloning the project `cd` into the new directory and install dependencies with

`pip install -r requirements.txt`

To start the project, run the following command in the terminal

`python app.py`

## Setting up the database

Create a Mongo database named `score_db` and another named `daily_sun_db`. A partnership with the Daily Sun has given us access to their articles which we copy and paginate the results for frontend.

Add /graphql to the url to access the interactive GraphQL platform

## Authentication

The backend verifies Google Firebase ID tokens and then issues its own JWT access
and refresh tokens. Configure these environment variables before starting the
server:

`JWT_SECRET_KEY` must be a long, random secret used to sign backend JWTs.

`GOOGLE_APPLICATION_CREDENTIALS` must point to the Firebase service-account JSON
file. For Docker Compose, set `FIREBASE_CREDENTIALS_HOST_PATH` to the host path
of that file; it is mounted into the container automatically.

Clients should call `signupUser` once with the Firebase `idToken`, or call
`loginUser` for an existing account. Send the returned access token on protected
requests using:

`Authorization: Bearer <access_token>`

Use the refresh token with `refreshAccessToken` after the access token expires.
