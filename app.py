from flask import Flask
from flask_graphql import GraphQLView
from graphene import Schema
from src.schema import Query, Mutation
from src.database import init_db

app = Flask(__name__)

schema = Schema(query=Query, mutation=Mutation)


app.add_url_rule(
    "/graphql", view_func=GraphQLView.as_view("graphql", schema=schema, graphiql=True)
)

init_db()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
