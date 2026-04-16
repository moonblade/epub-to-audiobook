#!/usr/bin/env python3.12
"""
Extensive test suite for Ollama speaker detection using few-shot prompts.

GROUND TRUTH: All test cases are MANUALLY EXTRACTED by reading the actual EPUB text.
NO REGEX OR CODE WAS USED TO CREATE THESE TEST CASES.

Each test case includes:
- dialogue: The actual quoted speech from the text
- speaker: The speaker as attributed in the surrounding text (verified by human reading)
- context: The full context as it appears in the EPUB (dialogue + attribution)
- attr_type: AFTER (attribution follows dialogue) or BEFORE (attribution precedes dialogue)
- book: Source book name for reference
"""
import os
import re
import sys
from dataclasses import dataclass

import requests


OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "https://ollama.sirius.moonblade.work")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:1.5b")


@dataclass
class TestCase:
    dialogue: str
    speaker: str
    context: str
    attr_type: str  # AFTER or BEFORE
    book: str


# =============================================================================
# MANUALLY CRAFTED GROUND TRUTH TEST CASES
# Each case was verified by reading the actual EPUB text
# =============================================================================

MANUAL_TEST_CASES = [
    # =========================================================================
    # Return of the Runebound Professor - Chapter 867: Fair Play
    # Characters: Mordred, Brayden, Noah
    # =========================================================================
    TestCase(
        dialogue="What I want is simple",
        speaker="Mordred",
        context='"What I want is simple," Mordred said.',
        attr_type="AFTER",
        book="Runebound Professor",
    ),
    TestCase(
        dialogue="What kind of questions?",
        speaker="Brayden",
        context='"What kind of questions?" Brayden asked warily.',
        attr_type="AFTER",
        book="Runebound Professor",
    ),
    TestCase(
        dialogue="Why?",
        speaker="Mordred",
        context='"Why?" Mordred exclaimed, still rifling through his coat.',
        attr_type="AFTER",
        book="Runebound Professor",
    ),
    TestCase(
        dialogue="I don't have the faintest damn idea what that's meant to mean",
        speaker="Brayden",
        context='"I don\'t have the faintest damn idea what that\'s meant to mean," Brayden said.',
        attr_type="AFTER",
        book="Runebound Professor",
    ),
    TestCase(
        dialogue="Why does everyone keep saying that?",
        speaker="Mordred",
        context='"Why does everyone keep saying that?" Mordred asked.',
        attr_type="AFTER",
        book="Runebound Professor",
    ),
    TestCase(
        dialogue="Perhaps it's because you haven't said what knowledge it is you're after",
        speaker="Noah",
        context='"Perhaps it\'s because you haven\'t said what knowledge it is you\'re after and you manage to word everything in the most suspicious way possible," Noah said.',
        attr_type="AFTER",
        book="Runebound Professor",
    ),
    TestCase(
        dialogue="Just get on with it",
        speaker="Noah",
        context='"Just get on with it," Noah said with a sigh.',
        attr_type="AFTER",
        book="Runebound Professor",
    ),
    TestCase(
        dialogue="Your list?",
        speaker="Noah",
        context='"Your list?" Noah repeated.',
        attr_type="AFTER",
        book="Runebound Professor",
    ),
    TestCase(
        dialogue="This is sad",
        speaker="Brayden",
        context='"This is sad," he mouthed.',  # Brayden identified from context (he caught Noah's eye)
        attr_type="AFTER",
        book="Runebound Professor",
    ),
    TestCase(
        dialogue="What?",
        speaker="Noah",
        context='"What?" Noah asked.',
        attr_type="AFTER",
        book="Runebound Professor",
    ),

    # =========================================================================
    # The Legend of William Oh - Chapter 262: Wirehair Gorilla
    # Characters: Will, Loth, Brianna, Ria, Travis
    # =========================================================================
    TestCase(
        dialogue="North side!",
        speaker="Will",
        context='"North side!" Will shouted',
        attr_type="AFTER",
        book="Legend of William Oh",
    ),
    TestCase(
        dialogue="My traps aren't doing much damage",
        speaker="Loth",
        context='"My traps aren\'t doing much damage," Loth said, arriving beside him.',
        attr_type="AFTER",
        book="Legend of William Oh",
    ),
    TestCase(
        dialogue="It's the fur",
        speaker="Will",
        context='"It\'s the fur," Will said, studying the creature with the Uru Drake\'s Eyes.',
        attr_type="AFTER",
        book="Legend of William Oh",
    ),
    TestCase(
        dialogue="Piercing weapons, then",
        speaker="Loth",
        context='"Piercing weapons, then," Loth said, following his train of thought.',
        attr_type="AFTER",
        book="Legend of William Oh",
    ),
    TestCase(
        dialogue="By the way, mine's sixteen inches.",
        speaker="Loth",
        context='"By the way, mine\'s sixteen inches." Loth said without looking away from her work',
        attr_type="AFTER",
        book="Legend of William Oh",
    ),
    TestCase(
        dialogue="Boar spears!",
        speaker="Will",
        context='"Boar spears!" Will called to them.',
        attr_type="AFTER",
        book="Legend of William Oh",
    ),
    TestCase(
        dialogue="start pulling back!",
        speaker="Will",
        context='"start pulling back!" Will directed Ria and Travis.',
        attr_type="AFTER",
        book="Legend of William Oh",
    ),

    # =========================================================================
    # He Who Fights With Monsters - Chapter 959: Without Consequences
    # Characters: Jason, Clive, Taika, Danielle, Carlos, Emi, Jessica
    # =========================================================================
    TestCase(
        dialogue="Bro, it sounds like killing the leader kills all the minions, like in an old monster movie",
        speaker="Taika",
        context='"Bro, it sounds like killing the leader kills all the minions, like in an old monster movie," Taika said.',
        attr_type="AFTER",
        book="He Who Fights With Monsters",
    ),
    TestCase(
        dialogue="That would seem to be the case",
        speaker="Danielle",
        context='"That would seem to be the case," Danielle replied.',
        attr_type="AFTER",
        book="He Who Fights With Monsters",
    ),
    TestCase(
        dialogue="I don't suppose any of the victims have regained consciousness?",
        speaker="Jason",
        context='"I don\'t suppose any of the victims have regained consciousness?" Jason asked.',
        attr_type="AFTER",
        book="He Who Fights With Monsters",
    ),
    TestCase(
        dialogue="No",
        speaker="Carlos",
        context='"No," Carlos said.',
        attr_type="AFTER",
        book="He Who Fights With Monsters",
    ),
    TestCase(
        dialogue="You found your creepy magic experiment specialist?",
        speaker="Clive",
        context='"You found your creepy magic experiment specialist?" Clive asked.',
        attr_type="AFTER",
        book="He Who Fights With Monsters",
    ),
    TestCase(
        dialogue="I did",
        speaker="Jason",
        context='"I did," Jason said.',
        attr_type="AFTER",
        book="He Who Fights With Monsters",
    ),
    TestCase(
        dialogue="Why would we be rude?",
        speaker="Clive",
        context='"Why would we be rude?" Clive asked.',
        attr_type="AFTER",
        book="He Who Fights With Monsters",
    ),
    TestCase(
        dialogue="I'm not taking questions at this time",
        speaker="Jason",
        context='"I\'m not taking questions at this time," Jason said, without slowing down.',
        attr_type="AFTER",
        book="He Who Fights With Monsters",
    ),
    TestCase(
        dialogue="I'm aware, sir.",
        speaker="Jessica",
        context='"I\'m aware, sir."',  # Jessica Sunderland from dialogue context
        attr_type="AFTER",
        book="He Who Fights With Monsters",
    ),

    # =========================================================================
    # Nightmare Realm Summoner - Chapter 354: Shared Excitement
    # Characters: Alex, Derek, Orchid, May, Claire
    # =========================================================================
    TestCase(
        dialogue="Yup",
        speaker="Derek",
        context='"Yup," Derek said.',
        attr_type="AFTER",
        book="Nightmare Realm Summoner",
    ),
    TestCase(
        dialogue="What?",
        speaker="Alex",
        context='"What?" Alex asked, blinking his confusion away.',
        attr_type="AFTER",
        book="Nightmare Realm Summoner",
    ),
    # NOTE: The EPUB actually says "Trek said" (author typo for "Derek")
    # The LLM correctly extracts "Trek" from the text - so this is a PASS
    TestCase(
        dialogue="You're gonna go fight something strong",
        speaker="Trek",
        context='"You\'re gonna go fight something strong," Trek said, as if it were the most obvious thing in the world.',
        attr_type="AFTER",
        book="Nightmare Realm Summoner",
    ),
    TestCase(
        dialogue="Oh",
        speaker="Alex",
        context='"Oh," Alex said, somewhat intelligently.',
        attr_type="AFTER",
        book="Nightmare Realm Summoner",
    ),
    TestCase(
        dialogue="You're right",
        speaker="Alex",
        context='"You\'re right," Alex confirmed.',
        attr_type="AFTER",
        book="Nightmare Realm Summoner",
    ),
    TestCase(
        dialogue="What happened to you?",
        speaker="Orchid",
        context='"What happened to you?" Orchid asked without a hint of tact.',
        attr_type="AFTER",
        book="Nightmare Realm Summoner",
    ),
    TestCase(
        dialogue="Huh?",
        speaker="Derek",
        context='"Huh?" Derek asked. "Me?"',
        attr_type="AFTER",
        book="Nightmare Realm Summoner",
    ),
    TestCase(
        dialogue="Yes",
        speaker="Orchid",
        context='"Yes," Orchid said. "You."',
        attr_type="AFTER",
        book="Nightmare Realm Summoner",
    ),
    TestCase(
        dialogue="I guess it's because I got killed a few times in the bone tower",
        speaker="Derek",
        context='"I guess it\'s because I got killed a few times in the bone tower," Derek said idly.',
        attr_type="AFTER",
        book="Nightmare Realm Summoner",
    ),
    TestCase(
        dialogue="Wait",
        speaker="Alex",
        context='"Wait," Alex said. "What? The bone tower?"',
        attr_type="AFTER",
        book="Nightmare Realm Summoner",
    ),
    TestCase(
        dialogue="I guess",
        speaker="Derek",
        context='"I guess," Derek replied.',
        attr_type="AFTER",
        book="Nightmare Realm Summoner",
    ),
    TestCase(
        dialogue="Nah",
        speaker="Derek",
        context='"Nah," Derek said. "She just said you were looking for me."',
        attr_type="AFTER",
        book="Nightmare Realm Summoner",
    ),
    TestCase(
        dialogue="No",
        speaker="Derek",
        context='"No," Derek said.',
        attr_type="AFTER",
        book="Nightmare Realm Summoner",
    ),
    TestCase(
        dialogue="Yeah",
        speaker="Derek",
        context='"Yeah," Derek agreed.',
        attr_type="AFTER",
        book="Nightmare Realm Summoner",
    ),

    # =========================================================================
    # Rise of the Living Forge - Chapter 582: A Body
    # Characters: Arwin, Koyu
    # =========================================================================
    TestCase(
        dialogue="It's yours",
        speaker="Arwin",
        context='"It\'s yours," Arwin said, placing the Dungeon Heart down',
        attr_type="AFTER",
        book="Rise of the Living Forge",
    ),
    TestCase(
        dialogue="I believe we should leave!",
        speaker="Koyu",
        context='"I believe we should leave!" Koyu yelled over the growing roar.',
        attr_type="AFTER",
        book="Rise of the Living Forge",
    ),
    TestCase(
        dialogue="Go!",
        speaker="Arwin",
        context='"Go!" Arwin yelled back.',
        attr_type="AFTER",
        book="Rise of the Living Forge",
    ),
]


def build_prompt_after(context: str) -> str:
    """Build few-shot prompt for AFTER attribution pattern."""
    return f'''Who speaks? Return only the name.

"Hello" John said. → John
"Why?" Mary asked. → Mary

{context} →'''


def build_prompt_before(context: str) -> str:
    """Build few-shot prompt for BEFORE attribution pattern."""
    return f'''Who speaks? Return only the name.

John said, "Hello" → John
Mary asked, "Why?" → Mary

{context} →'''


def query_ollama(prompt: str) -> str:
    """Query Ollama API with the given prompt."""
    try:
        response = requests.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.0,
                    "num_predict": 10,
                }
            },
            timeout=15
        )
        if response.status_code == 200:
            return response.json().get("response", "").strip()
    except Exception as e:
        return f"ERROR: {e}"
    return "ERROR"


def parse_response(response: str) -> str:
    """Parse LLM response to extract speaker name."""
    response = response.strip().split("\n")[0].strip()
    response = re.sub(r'[^\w\s]', '', response).strip()
    words = response.split()
    if words:
        # Handle titles like "Lady X", "Lord Y"
        if len(words) >= 2 and words[0].lower() in {"lady", "lord", "sir", "the", "king", "queen"}:
            return " ".join(words[:2])
        return words[0]
    return response


def run_tests(cases: list[TestCase]) -> dict:
    """Run all test cases against Ollama and return results."""
    results = {"passed": 0, "failed": 0, "details": []}
    
    print(f"\n{'='*80}")
    print(f"Running {len(cases)} MANUALLY VERIFIED test cases against {OLLAMA_MODEL}")
    print(f"Host: {OLLAMA_HOST}")
    print(f"{'='*80}\n")
    
    for i, case in enumerate(cases):
        if case.attr_type == "AFTER":
            prompt = build_prompt_after(case.context)
        else:
            prompt = build_prompt_before(case.context)
        
        raw_response = query_ollama(prompt)
        predicted = parse_response(raw_response)
        expected = case.speaker
        
        # Case-insensitive comparison
        passed = predicted.lower() == expected.lower()
        
        if passed:
            results["passed"] += 1
            status = "✅"
        else:
            results["failed"] += 1
            status = "❌"
        
        results["details"].append({
            "case": i + 1,
            "dialogue": case.dialogue[:30],
            "context": case.context[:50],
            "expected": expected,
            "predicted": predicted,
            "raw_response": raw_response,
            "passed": passed,
            "book": case.book,
        })
        
        dialogue_preview = case.dialogue[:25] + "..." if len(case.dialogue) > 25 else case.dialogue
        print(f"{i+1:3}. {status} \"{dialogue_preview}\" → {predicted:15} (expected: {expected}) [{case.book[:15]}]")
    
    return results


def print_summary(results: dict):
    """Print test summary with pass/fail stats."""
    total = results["passed"] + results["failed"]
    accuracy = (results["passed"] / total * 100) if total > 0 else 0
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    print(f"Total tests: {total}")
    print(f"Passed: {results['passed']} ({accuracy:.1f}%)")
    print(f"Failed: {results['failed']}")
    print(f"{'='*80}")
    
    if results["failed"] > 0:
        print("\nFailed cases (with raw LLM response):")
        for d in results["details"]:
            if not d["passed"]:
                print(f"\n  [{d['book']}] \"{d['dialogue']}...\"")
                print(f"    Context: {d['context']}...")
                print(f"    Expected: {d['expected']}")
                print(f"    Predicted: {d['predicted']}")
                print(f"    Raw response: {d['raw_response']}")


if __name__ == "__main__":
    print("Using MANUALLY VERIFIED ground truth test cases...")
    print(f"Total test cases: {len(MANUAL_TEST_CASES)}")
    
    results = run_tests(MANUAL_TEST_CASES)
    print_summary(results)
    
    # Exit with failure if accuracy is below threshold
    total = results["passed"] + results["failed"]
    accuracy = (results["passed"] / total * 100) if total > 0 else 0
    
    if accuracy < 80:
        print(f"\n⚠️  Accuracy {accuracy:.1f}% is below 80% threshold")
        sys.exit(1)
    else:
        print(f"\n✅ Accuracy {accuracy:.1f}% meets threshold")
        sys.exit(0)
