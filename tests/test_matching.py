from fastapi import FastAPI, HTTPException
from app.services.matching_service import MatchingService

def test_matching_service():
    matching_service = MatchingService()

    # Test case 1: Exact match
    item_name = "YELLOW ONION 3LB"
    expected_match = "Onion, fresh"
    match = matching_service.match_item(item_name)
    assert match == expected_match, f"Expected {expected_match}, but got {match}"

    # Test case 2: Abbreviated match
    item_name = "GRN BELL PPR"
    expected_match = "Green Bell Pepper"
    match = matching_service.match_item(item_name)
    assert match == expected_match, f"Expected {expected_match}, but got {match}"

    # Test case 3: Low confidence match
    item_name = "BLUBRY MNCH"
    match, suggestions = matching_service.match_item(item_name)
    assert match is None, "Expected no match for low confidence item"
    assert len(suggestions) > 0, "Expected suggestions for low confidence item"

    # Test case 4: Non-existent item
    item_name = "UNKNOWN ITEM"
    match, suggestions = matching_service.match_item(item_name)
    assert match is None, "Expected no match for non-existent item"
    assert len(suggestions) > 0, "Expected suggestions for non-existent item"