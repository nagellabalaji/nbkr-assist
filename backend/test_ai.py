# Local NLP Classifier Dry-Run Test Script
import sys
import os

# Adjust path to import app package
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'app')))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from app.ai.classifier import LocalNLPClassifier

def run_tests():
    classifier = LocalNLPClassifier()
    
    test_cases = [
        "My hostel room fan is not working and it is very hot.",
        "The washroom sink has a broken faucet and water is leaking on the floor.",
        "A wire is sparking from the classroom switchboard. There is smoke!",
        "The computer in DSP laboratory is not starting, screen is black.",
        "College bus number 12 is delayed and arriving late.",
        "Dustbins in the library corridor are full and spilling garbage.",
        "The study table in my hostel room has a broken wobbly leg."
      ]

    print("=" * 60)
    print(" DRY RUN TEST FOR LOCAL NLP CLASSIFICATION & ROUTING ENGINE ")
    print("=" * 60)
    
    for i, desc in enumerate(test_cases, 1):
        cat, priority, dept, conf = classifier.classify_complaint(desc)
        print(f"\nTest #{i}: '{desc}'")
        print("-" * 40)
        print(f" -> Predicted Category:   {cat}")
        print(f" -> Predicted Priority:   {priority}")
        print(f" -> Suggested Department: {dept}")
        print(f" -> Classifier Confidence: {conf * 100:.0f}%")
        print("-" * 40)

if __name__ == '__main__':
    run_tests()
