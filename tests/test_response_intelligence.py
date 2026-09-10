from om_ai.core.response import (
    ResponseEngine,
)


engine = ResponseEngine()


tests = [
    (
        "hello OM",
        "conversation",
        "Hello! How can I help you?"
    ),

    (
        "create login page in react",
        "coding",
        """
import React from "react";

export default function Login() {
    return <div>Login</div>;
}
""",
    ),

    (
        "create login page in react",
        "coding",
        """
ressive wastinta originals
HinesCLICK Dixon stumbling
cellar Blairigan random words
YAX Bavarian callous
"""
    ),
]


for message, intent, draft in tests:

    state = engine.prepare(
        message=message,
        intent=intent,
    )

    state = engine.validate(
        state=state,
        response=draft,
    )

    print("=" * 70)
    print("Message:", message)
    print("Approved:", state.approved)
    print("Score:", state.quality_score)
    print("Issues:", state.issues)