from app.agents.workflow import classify

def test_exam_wifi_is_critical():
    category, priority, location = classify("Wi-Fi in CSE Block Room 302 failed before examination")
    assert category == "Wi-Fi / Network"
    assert priority == "Critical"
    assert "Room 302" in location

def test_projector_category():
    category, _, _ = classify("The projector is broken in the lecture hall")
    assert category == "Classroom Equipment"
