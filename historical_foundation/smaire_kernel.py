def SMAIRE(S, custom_checks=None):

    if S.get("forbidden"):
        return "REFUSE: FORBIDDEN"

    if S.get("conflict"):
        return "REFUSE: CONFLICT"

    if S.get("abstain"):
        return "ABSTAIN"

    required = [
        "sender_identity",
        "delivery_authorization",
        "delivery_intent",
        "message_context"
    ]

    if any(not S.get(k) for k in required):
        return "REFUSE: INCOMPLETE"

    if custom_checks:
        for check in custom_checks:
            if check(S):
                return "REFUSE: CUSTOM_VIOLATION"

    return "SMS_ADMISSIBLE"

result = SMAIRE({
    "sender_identity": True,
    "delivery_authorization": True,
    "delivery_intent": True,
    "message_context": True,
    "conflict": False,
    "forbidden": False
})

print(result)
# SMS_ADMISSIBLE

# Failure-state examples - same invariant, different structures:

print(SMAIRE({"forbidden": True}))
# REFUSE: FORBIDDEN

print(SMAIRE({"conflict": True, "abstain": True}))
# REFUSE: CONFLICT  <- conflict takes precedence over abstain

print(SMAIRE({
    "sender_identity": True,
    "conflict": False,
    "forbidden": False,
    # delivery_authorization, delivery_intent,
    # and message_context are missing
}))
# REFUSE: INCOMPLETE

print(SMAIRE({
    "abstain": True,
    "sender_identity": True,
    "delivery_authorization": True,
    "delivery_intent": True,
    "message_context": True,
    "conflict": False,
    "forbidden": False
}))
# ABSTAIN  <- structure valid, delivery intentionally withheld

# The invariant holds across admissible and inadmissible states alike.