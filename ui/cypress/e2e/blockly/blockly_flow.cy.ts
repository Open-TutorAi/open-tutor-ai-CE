describe('Module Blockly — Parcours complet étudiant', () => {

  beforeEach(() => {
    cy.visit('/auth')
    cy.get('input[name="email"]').type('student@test.com')
    cy.get('input[name="password"]').type('password123')
    cy.get('button[type="submit"]').click()
    cy.url().should('include', '/student/dashboard')
  })

  // ────────────────────────────────────────────────────────────
  // US-B01 — Accès au module
  // ────────────────────────────────────────────────────────────

  describe('US-B01 — Accès au module', () => {

    it('Le bouton Blockly est visible dans le dashboard', () => {
      cy.contains('button', 'Blockly').should('be.visible')
    })

    it('Cliquer sur Blockly ouvre le popup formulaire', () => {
      cy.contains('button', 'Blockly').click()
      cy.get('[role="dialog"]').should('be.visible')
      cy.contains('Exercice Blockly').should('be.visible')
    })

    it('Le formulaire contient : Cours, Objectifs, Prérequis, Niveau', () => {
      cy.contains('button', 'Blockly').click()
      cy.contains('Cours').should('be.visible')
      cy.contains('Objectifs').should('be.visible')
      cy.contains('Prérequis').should('be.visible')
      cy.contains('Débutant').should('be.visible')
      cy.contains('Intermédiaire').should('be.visible')
      cy.contains('Avancé').should('be.visible')
    })

    it('Le bouton Démarrer est désactivé si Cours est vide', () => {
      cy.contains('button', 'Blockly').click()
      cy.contains('button', 'Démarrer').should('be.disabled')
    })

    it('Remplir Cours active le bouton Démarrer', () => {
      cy.contains('button', 'Blockly').click()
      cy.get('input[placeholder*="Cours"]').type('Variables Python')
      cy.contains('button', 'Démarrer').should('not.be.disabled')
    })

    it('Fermer le popup le masque', () => {
      cy.contains('button', 'Blockly').click()
      cy.get('[role="dialog"]').should('be.visible')
      cy.get('[aria-label="Fermer"]').click()
      cy.get('[role="dialog"]').should('not.exist')
    })

  })

  // ────────────────────────────────────────────────────────────
  // US-B02 — Génération d'exercice
  // ────────────────────────────────────────────────────────────

  describe('US-B02 — Génération d\'exercice par IA', () => {

    beforeEach(() => {
      cy.intercept('POST', '/api/blockly/generate/stream', {
        body: [
          'data: {"type":"chunk","content":"{\\"title\\":\\"Calcul de somme\\",\\"description\\":\\"Calculez 3+5\\",\\"test_cases\\":[{\\"expected_output\\":\\"8\\"}],\\"hints\\":[\\"Utilisez +\\"]}"}',
          'data: {"type":"done","assignment_id":"test-uuid-001"}',
          ''
        ].join('\n')
      }).as('generate')
    })

    it('Le formulaire rempli redirige vers /student/blockly/new', () => {
      cy.contains('button', 'Blockly').click()
      cy.get('input[placeholder*="Cours"]').type('Maths Python')
      cy.contains('button', 'Démarrer').click()
      cy.url().should('include', '/student/blockly/new')
    })

    it('La carte exercice affiche le titre généré', () => {
      cy.visit('/student/blockly/new')
      cy.wait('@generate')
      cy.contains('Calcul de somme').should('be.visible')
    })

    it('La carte exercice affiche la description', () => {
      cy.visit('/student/blockly/new')
      cy.wait('@generate')
      cy.contains('Calculez 3+5').should('be.visible')
    })

    it('En cas d\'erreur réseau, le bouton Réessayer s\'affiche', () => {
      cy.intercept('POST', '/api/blockly/generate/stream', {
        forceNetworkError: true
      }).as('generateError')
      cy.visit('/student/blockly/new')
      cy.wait('@generateError')
      cy.contains('Réessayer').should('be.visible')
    })

  })

  // ────────────────────────────────────────────────────────────
  // US-B03 — Éditeur Blockly visuel
  // ────────────────────────────────────────────────────────────

  describe('US-B03 — Éditeur Blockly', () => {

    beforeEach(() => {
      cy.intercept('POST', '/api/blockly/generate/stream', {
        body: 'data: {"type":"chunk","content":"{\\"title\\":\\"Somme\\",\\"description\\":\\"Calc\\",\\"hints\\":[],\\"test_cases\\":[]}"}' + '\n' +
              'data: {"type":"done","assignment_id":"test-001"}' + '\n'
      }).as('generate')
      cy.visit('/student/blockly/new')
      cy.wait('@generate')
      cy.contains('Ouvrir l\'éditeur Blockly').click()
    })

    it('La toolbox affiche les catégories de base', () => {
      cy.contains('Logique').should('be.visible')
      cy.contains('Boucles').should('be.visible')
      cy.contains('Maths').should('be.visible')
      cy.contains('Texte').should('be.visible')
      cy.contains('Variables').should('be.visible')
    })

    it('Le bouton Reset est visible', () => {
      cy.contains('Reset').should('be.visible')
    })

    it('Le panneau "Python généré" est visible', () => {
      cy.contains('Python généré').should('be.visible')
    })

  })

  // ────────────────────────────────────────────────────────────
  // US-B04 — Exécution du code
  // ────────────────────────────────────────────────────────────

  describe('US-B04 — Exécution du code', () => {

    beforeEach(() => {
      cy.intercept('POST', '/api/blockly/generate/stream', {
        body: 'data: {"type":"chunk","content":"{\\"title\\":\\"T\\",\\"description\\":\\"D\\",\\"hints\\":[],\\"test_cases\\":[]}"}' + '\n' +
              'data: {"type":"done","assignment_id":"t1"}' + '\n'
      }).as('generate')
      cy.visit('/student/blockly/new')
      cy.wait('@generate')
      cy.contains('Ouvrir l\'éditeur Blockly').click()
    })

    it('Le bouton Exécuter est visible et cliquable', () => {
      cy.contains('Exécuter').should('be.visible').and('not.be.disabled')
    })

    it('Cliquer Exécuter appelle POST /api/blockly/execute', () => {
      cy.intercept('POST', '/api/blockly/execute', {
        body: { stdout: '8\n', stderr: '', error: null, timed_out: false, execution_time_ms: 12 }
      }).as('execute')
      cy.contains('Exécuter').click()
      cy.wait('@execute')
    })

    it('Le stdout s\'affiche dans la console', () => {
      cy.intercept('POST', '/api/blockly/execute', {
        body: { stdout: '42\n', stderr: '', error: null, timed_out: false, execution_time_ms: 11 }
      }).as('execute')
      cy.contains('Exécuter').click()
      cy.wait('@execute')
      cy.contains('42').should('be.visible')
    })

    it('Une erreur d\'exécution affiche le préfixe ❌', () => {
      cy.intercept('POST', '/api/blockly/execute', {
        body: { stdout: '', stderr: 'SyntaxError', error: 'SyntaxError', timed_out: false, execution_time_ms: 5 }
      }).as('execute')
      cy.contains('Exécuter').click()
      cy.wait('@execute')
      cy.contains('❌').should('be.visible')
    })

  })

  // ────────────────────────────────────────────────────────────
  // US-B05 — Soumission et feedback IA
  // ────────────────────────────────────────────────────────────

  describe('US-B05 — Soumission et feedback IA', () => {

    beforeEach(() => {
      cy.intercept('POST', '/api/blockly/generate/stream', {
        body: 'data: {"type":"chunk","content":"{\\"title\\":\\"T\\",\\"description\\":\\"D\\",\\"hints\\":[],\\"test_cases\\":[]}"}' + '\n' +
              'data: {"type":"done","assignment_id":"t2"}' + '\n'
      }).as('generate')
      cy.visit('/student/blockly/new')
      cy.wait('@generate')
      cy.contains('Ouvrir l\'éditeur Blockly').click()
    })

    it('Le bouton Soumettre est visible', () => {
      cy.contains('Soumettre').should('be.visible')
    })

    it('Soumettre appelle POST /api/blockly/submit', () => {
      cy.intercept('POST', '/api/blockly/submit', {
        body: 'data: {"type":"score","value":85}\ndata: {"type":"feedback","content":"Bravo !"}\ndata: {"type":"done"}\n'
      }).as('submit')
      cy.contains('Soumettre').click()
      cy.wait('@submit')
    })

    it('Le score 85/100 s\'affiche en badge vert ✅', () => {
      cy.intercept('POST', '/api/blockly/submit', {
        body: 'data: {"type":"score","value":85}\ndata: {"type":"feedback","content":"Bravo !"}\ndata: {"type":"done"}\n'
      }).as('submit')
      cy.contains('Soumettre').click()
      cy.wait('@submit')
      cy.contains('85/100').should('be.visible')
      cy.contains('✅').should('be.visible')
    })

    it('Le score 50/100 s\'affiche en badge rouge ❌', () => {
      cy.intercept('POST', '/api/blockly/submit', {
        body: 'data: {"type":"score","value":50}\ndata: {"type":"feedback","content":"Courage !"}\ndata: {"type":"done"}\n'
      }).as('submit')
      cy.contains('Soumettre').click()
      cy.wait('@submit')
      cy.contains('50/100').should('be.visible')
      cy.contains('❌').should('be.visible')
    })

    it('Le feedback IA s\'affiche après soumission', () => {
      cy.intercept('POST', '/api/blockly/submit', {
        body: 'data: {"type":"score","value":85}\ndata: {"type":"feedback","content":"Excellent travail !"}\ndata: {"type":"done"}\n'
      }).as('submit')
      cy.contains('Soumettre').click()
      cy.wait('@submit')
      cy.contains('Excellent travail !').should('be.visible')
    })

  })

})