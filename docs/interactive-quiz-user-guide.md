# Interactive Quiz & "Je n'ai pas compris" — User Guide

## Overview

The Open TutorAI student chat includes two AI-powered learning tools to help you understand and test your knowledge:

1. **🧠 Interactive Quiz** — Test your understanding with multiple choice questions and get instant feedback
2. **😕 "Je n'ai pas compris"** — Get the concept re-explained 3 different ways when you're stuck

---

## How to Access the Features

Both features are available in the **pedagogical shortcuts toolbar** at the bottom of the chat, above the message input field.

```
[ Difficulté ] [ Comprendre ] [ Je n'ai pas compris ] [ Résumer ] [ Prochaine étape ] [ Quiz ]
```

---

## Feature 1: Interactive Quiz 🧠

### What it does
When you click **Quiz → Multiple Choice**, the AI generates a short quiz (2 questions) based on the topic you've been discussing. You can answer by clicking on the options and see immediately whether you were right or wrong, with an explanation.

### Step-by-step guide

#### Step 1 — Start a conversation
First, chat with your tutor about a topic you want to be tested on.

> **Example:** Ask "Explain what a variable is in algorithms"

#### Step 2 — Open the quiz
Click the **Quiz** button in the shortcuts toolbar, then click **Multiple Choice**.

#### Step 3 — Wait for generation
A loading screen appears while the AI generates your quiz questions (this takes 10–60 seconds depending on your machine).

#### Step 4 — Answer the questions
Click on one of the 4 answer options (A, B, C, or D).

**If your answer is correct ✅:**
- The option turns **green**
- A congratulatory message appears
- The explanation of why this answer is correct is shown

**If your answer is incorrect ❌:**
- Your chosen option turns **red**
- The correct answer is highlighted in **green**
- An explanation of the correct answer is shown
- A brief concept recap helps you understand what you missed

#### Step 5 — Continue to the next question
Click **"Question suivante →"** to move to the next question.

#### Step 6 — See your results
After the last question, click **"Résultats 🏆"** to see:
- Your final score (e.g., 2/2)
- Your percentage (e.g., 100%)
- A performance label (Excellent / Bien / À revoir / Continue !)
- A recap of all questions with explanations for wrong answers

#### Step 7 — Retry if needed
Click **"↻ Réessayer"** to redo the quiz from the beginning, or **"✓ Terminer"** to close.

---

### Quiz Score Guide

| Score | Label | Meaning |
|-------|-------|---------|
| 80–100% | 🏆 Excellent ! | Great job! You've mastered this topic |
| 60–79% | 👍 Bien ! | Good work, minor gaps to review |
| 40–59% | 📚 À revoir | Some concepts need more practice |
| 0–39% | 💪 Continue ! | Keep learning, you'll get there! |

---

## Feature 2: "Je n'ai pas compris" 😕

### What it does
When you don't understand the tutor's explanation, click **"Je n'ai pas compris"** and the AI will re-explain the same concept in **3 completely different ways**:

1. **🔁 Une analogie** — A simple comparison to something from everyday life
2. **💡 Un exemple concret** — A practical, step-by-step real-world example  
3. **📊 Un tableau ou schéma** — A visual text table or structured diagram

### When to use it
- When the tutor's explanation is too abstract or confusing
- When you want to see the concept from a different angle
- When you need a simpler explanation

### Step-by-step guide

#### Step 1 — Read the tutor's explanation
After the tutor explains something, if you don't understand it...

#### Step 2 — Click "Je n'ai pas compris"
Click the **😕 Je n'ai pas compris** button in the shortcuts toolbar.

#### Step 3 — Read the 3 re-explanations
The tutor will respond with 3 different approaches:

**Example response for "variables in algorithms":**

> 🔁 **Analogie:** Imagine a variable as a box with a label. The label is the variable name (like `x`), and what's inside the box is the value (like `5`).
>
> 💡 **Exemple concret:** In a program that calculates your age, you write `age = 25`. The variable `age` now stores the value `25`. Later you can change it: `age = 26`.
>
> 📊 **Tableau:**
> | Concept | Description | Example |
> |---------|-------------|---------|
> | Variable name | The label of the box | `age`, `name`, `score` |
> | Variable value | What's stored inside | `25`, `"Alice"`, `100` |
> | Assignment | Putting a value in the box | `age = 25` |

---

## Tips for Best Results

| Tip | Details |
|-----|---------|
| **Chat first, then quiz** | The quiz is generated based on your conversation. The more you've discussed a topic, the more relevant the questions will be. |
| **Be patient** | Quiz generation can take up to 60 seconds. Don't click again — the spinner means it's working. |
| **Use both features together** | If you fail a quiz question, use "Je n'ai pas compris" to get a better explanation, then retry the quiz. |
| **Retry the quiz** | You can retry as many times as you want to improve your score. |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Quiz shows "Erreur" | Click "🔄 Réessayer". If it fails again, start a new chat and try again. |
| Quiz takes too long | This is normal for the first generation. Wait up to 2 minutes. |
| Questions are not about my topic | Make sure you've discussed the topic first before clicking Multiple Choice. |
| "Je n'ai pas compris" gives a generic answer | Try asking a more specific question first to give the AI more context. |

---

## Keyboard Shortcuts

There are no keyboard shortcuts for these features. All interactions are done by clicking.

---

## Frequently Asked Questions

**Q: How many questions does the quiz have?**  
A: The quiz generates 2 questions per session.

**Q: Can I choose a different topic for the quiz?**  
A: The quiz is always based on your current conversation. To quiz on a different topic, start a new conversation about that topic first.

**Q: Are my quiz results saved?**  
A: Currently, quiz results are not saved. Once you close the quiz modal, the results are gone.

**Q: Can I use these features on mobile?**  
A: Yes, both features work on mobile browsers, but the experience is optimized for desktop.

**Q: Why does the quiz sometimes fail?**  
A: The quiz relies on the AI generating valid JSON. Sometimes the AI model produces an incorrect format. Simply click "Réessayer" to try again.