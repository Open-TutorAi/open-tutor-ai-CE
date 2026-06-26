# Diagrammes — Module Blockly

## 3.1 Diagramme de Classes
┌─────────────────────────────────────────────────────────────┐
│ BACKEND (Python / FastAPI) │
│ │
│ ┌──────────────────────┐ ┌────────────────────────────┐ │
│ │ BlocklyRouter │───▶│ BlocklySandbox │ │
│ │ /api/blockly/* │ │ execute_python(code, t) │ │
│ │ │ │ timeout: 5s │ │
│ │ POST /execute │ │ retourne: stdout, stderr │ │
│ │ POST /test │ │ error, timed_out │ │
│ │ POST /submit │ └────────────────────────────┘ │
│ │ POST /generate/ │ │
│ │ POST /workspace/save│ ┌────────────────────────────┐ │
│ │ GET /workspace/{id}│───▶│ BlocklyLLMGenerator │ │
│ └──────────────────────┘ │ Ollama qwen2.5:0.5b │ │
│ │ │ │ │
│ │ │ generate_exercise() │ │
│ ▼ │ get_feedback() │ │
│ ┌──────────────────────┐ └────────────────────────────┘ │
│ │ ExecutionRequest │ │
│ │ python_code: str │ ┌────────────────────────────┐ │
│ │ assignment_id: str │ │ GenerateRequest │ │
│ │ level: str │ │ level, course │ │
│ └──────────────────────┘ │ objectives, prerequisites│ │
│ └────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ FRONTEND (SvelteKit) │
│ │
│ ┌──────────────────┐ ┌──────────────────────────────┐ │
│ │ Dashboard.svelte │─────▶│ BlocklyPopup (inline) │ │
│ │ Bouton Blockly │ │ course, objectives │ │
│ └──────────────────┘ │ prerequisites, level │ │
│ └─────────────┬────────────────┘ │
│ │ goto() │
│ ┌─────────────▼────────────────┐ │
│ │ /student/blockly/new │ │
│ │ +page.svelte │ │
│ │ │ │
│ │ VUE 1 : ExerciseCard │ │
│ │ VUE 2 : BlocklyEditor │ │
│ └──────────┬────────────────────┘ │
│ │ │
│ ┌────────────────────────┼─────────────────┐ │
│ ▼ ▼ ▼ │
│ ┌─────────────────┐ ┌─────────────────────┐ ┌──────────┐ │
│ │ blocklyStore │ │ pythonGenerator │ │ blockly │ │
│ │ level │ │ workspaceToCode() │ │ API │ │
│ │ consecutiveSuc │ └─────────────────────┘ │ index.ts│ │
│ └─────────────────┘ └──────────┘ │
└─────────────────────────────────────────────────────────────┘

text


## 3.2 Diagramme de Séquence
Étudiant Dashboard /blockly/new /api/blockly Ollama Sandbox
│ │ │ │ │ │
│─clic──────▶ │ │ │ │
│ Blockly │─popup──────▶ │ │ │
│ │ formulaire│ │ │ │
│─submit form────────────▶ │ │ │
│ │ │─POST /generate/stream─────▶ │
│ │ │ │─prompt────▶ │
│ │ │ │◀─response── │
│ │ │◀─SSE chunks───│ │ │
│◀─ExerciseCard──────────│ │ │ │
│ │ │ │ │ │
│─clic Ouvrir Blockly────▶ │ │ │
│ │ │ [init Blockly workspace] │ │
│ │ │ │ │ │
│─glisse blocs + clic ▶──▶ │ │ │
│ │ │─POST /execute─────────────────────▶ │
│ │ │ │ │─run────▶ │
│ │ │ │ │◀─stdout── │
│ │ │◀─stdout/err─────────────── │
│◀─console output────────│ │ │ │
│ │ │ │ │ │
│─clic Soumettre─────────▶ │ │ │
│ │ │─POST /submit──────────────────────▶ │
│ │ │ │ │─run────▶ │
│ │ │ │ │◀─result── │
│ │ │◀─SSE: score─────────────── │
│◀─badge score───────────│ │ │ │
│ │ │ │─feedback──▶ │
│ │ │◀─SSE: feedback────────────◀─text── │
│◀─feedback IA───────────│ │ │ │

text


## 3.3 Diagramme d'Activité — Progression de Niveau
[Étudiant soumet une solution]
│
▼
[Score calculé]
│
┌───────┴──────────┐
│ Score >= 70 ? │
└───────┬──────────┘
│ Non ──────────────▶ [consecutiveSuccesses = 0]
│ │
│ Oui ▼
▼ [Afficher feedback]
[consecutiveSuccesses += 1] │
│ [FIN iteration]
┌───────┴──────────┐
│ >= 2 succès ? │
└───────┬──────────┘
│ Non ──────────────▶ [FIN iteration]
│
│ Oui
▼
┌───────────────────┐
│ level == advanced?│
└───────┬───────────┘
│ Oui ──────────────▶ [Message "🏆 Niveau max !"]
│ │
│ Non [FIN]
▼
[level = niveau suivant]
│
▼
[Mettre à jour toolbox]
│
▼
[Persister localStorage]
│
▼
[Afficher "🎉 Niveau suivant !"]
│
▼
[Générer nouvel exercice (3s)]
│
▼
[FIN]