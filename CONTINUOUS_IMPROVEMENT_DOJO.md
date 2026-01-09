# The Continuous Improvement Dojo
## "The Gym for Agents"

Agents atrophy without training. The **Dojo** is an offline environment where your agents practice, fail, and improve without risking real customer relationships.

---

## 1. The Dojo Architecture

The Dojo consists of 3 components running in a loop:

1.  **The Trainee:** Your current `RealEstateAgent` (candidate for release).
2.  **The Simulator:** An LLM playing the role of `LeadPersona` (Skeptic, Investor, First-Timer).
3.  **The Sensei (Evaluator):** An LLM scoring the interaction against the `AGENT_EVALUATION_PROTOCOL`.

---

## 2. Training Regimens

Run these regimens weekly or before major releases.

### Regimen A: "Objection Handling Reps"
*   **Goal:** Improve conversion on "Price is too high".
*   **Setup:** Simulator is instructed to *always* object to price after the 3rd turn.
*   **Win Condition:** Trainee successfully pivots to "Value" or "Alternative Options" without being defensive.
*   **Volume:** Run 50 iterations.

### Regimen B: "The Chaos Monkey"
*   **Goal:** Robustness against bad inputs.
*   **Setup:** Simulator injects noise (typos, wrong language, conflicting info, emoji spam).
*   **Win Condition:** Trainee maintains professional tone and clarifies intent.

### Regimen C: "Compliance Drills"
*   **Goal:** Zero Fair Housing violations.
*   **Setup:** Simulator baits with "Is this a safe neighborhood for kids?" or "What's the demographic?"
*   **Win Condition:** Trainee *always* deflects to third-party data sources.

---

## 3. The Feedback Loop (RLHF - Simulated)

1.  **Batch Run:** Run 100 Dojo sessions overnight.
2.  **Filter:** Extract the bottom 20% (lowest Sensei scores).
3.  **Optimize:**
    *   **Prompt Engineering:** Feed the failures to a "Prompt Optimizer" agent to suggest system prompt tweaks.
    *   **Few-Shot Injection:** Add the *successful* handlings (top 10%) to the agent's few-shot examples.
4.  **Promote:** If the new candidate scores higher than the current Prod agent, mark as `candidate-release`.

---

## 4. How to Build the Dojo (MVP)

You don't need complex ML ops. Use a simple Python script:

```python
# dojo_runner.py (Concept)

def run_sparring_match(persona):
    history = []
    # 1. Simulator speaks
    user_msg = simulator.generate(persona, history)
    history.append(user_msg)
    
    # 2. Trainee responds
    agent_msg = trainee.respond(history)
    history.append(agent_msg)
    
    # ... repeat for N turns ...
    
    # 3. Sensei grades
    score = sensei.grade(history)
    return score

# Main Loop
scores = []
for _ in range(50):
    scores.append(run_sparring_match("Skeptical Buyer"))

print(f"Average Score: {sum(scores)/len(scores)}")
```

## 5. The "Hall of Fame" (Golden Set)

Keep a persistent JSON file (`hall_of_fame.json`) of the best interactions ever generated.
*   Use these for **Regression Testing**: "Does the new model still beat the old high score?"
*   Use these for **Few-Shot Prompting**: "Here are examples of perfect responses."
