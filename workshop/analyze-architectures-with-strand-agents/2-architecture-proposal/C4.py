# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from diagrams import Diagram
from diagrams.c4 import (
    Database,
    Person,
    Relationship,
    System,
    SystemBoundary,
)

# pylint: disable=expression-not-assigned

graph_attr = {
    "splines": "spline",
}

with Diagram(
    "Content Publishing System Architecture",
    direction="TB",
    graph_attr=graph_attr,
    filename="C4-diagrams",
):
    # People
    editor = Person("Editor", "Creates and processes textbooks", external=True)
    customer = Person("Customer", "Searches for and views textbooks")

    # External Systems
    shakespeare = System(
        "Shakespeare",
        "The editorial service where textbooks are authored",
        external=True,
    )
    gutenberg = System(
        "Gutenberg",
        "The publishing service that converts textbooks into output formats",
        external=True,
    )
    alexandria = System(
        "Alexandria",
        "The library service where published textbooks are stored",
        external=True,
    )

    # Internal System Boundary
    with SystemBoundary("Content Publishing System"):
        search_microservice = System(
            "Search Microservice", "Provides search functionality for content"
        )
        display_microservice = System(
            "Display Microservice", "Enables viewing of content"
        )

        nosql_db = Database("NoSQL Database", "Stores indexed content for searching")
        sql_db = Database("SQL ENTITLEMENTS", "Stores user entitlement information")

    # Relationships
    editor >> Relationship("1. Get Textbook") >> shakespeare
    shakespeare >> Relationship("2. Convert to PDF") >> gutenberg
    gutenberg >> Relationship("3. Save PDF to Library") >> alexandria
    alexandria >> Relationship("4. Index content") >> nosql_db

    customer >> Relationship("5. Search for content") >> search_microservice
    search_microservice >> Relationship("Query indexed content") >> nosql_db

    customer >> Relationship("6. View content") >> display_microservice
    display_microservice >> Relationship("Check entitlements") >> sql_db
    display_microservice >> Relationship("Retrieve content") >> alexandria
