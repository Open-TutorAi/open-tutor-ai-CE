
class TestScoreThreshold:
    """Tests du seuil de score (70)."""

    def test_score_65_no_increment(self):
        """Score 65 < 70 → pas d'incrément."""
        consecutive = 0
        score = 65.0
        consecutive = consecutive + 1 if score >= 70 else 0
        assert consecutive == 0

    def test_score_70_increments(self):
        """Score 70 exactement → incrément."""
        consecutive = 0
        score = 70.0
        consecutive = consecutive + 1 if score >= 70 else 0
        assert consecutive == 1

    def test_score_85_increments(self):
        """Score 85 > 70 → incrément."""
        consecutive = 0
        score = 85.0
        consecutive = consecutive + 1 if score >= 70 else 0
        assert consecutive == 1

    def test_fail_resets_counter(self):
        """Score < 70 après succès → remise à zéro."""
        consecutive = 1
        score = 60.0
        consecutive = consecutive + 1 if score >= 70 else 0
        assert consecutive == 0


class TestLevelProgression:
    """Tests de la logique de changement de niveau."""

    def test_two_successes_beginner_to_intermediate(self):
        """2 succès consécutifs → beginner passe à intermediate."""
        levels = ['beginner', 'intermediate', 'advanced']
        level = 'beginner'
        consecutive = 0

        for score in [80.0, 75.0]:
            if score >= 70:
                consecutive += 1
                if consecutive >= 2:
                    idx = levels.index(level)
                    if idx < len(levels) - 1:
                        level = levels[idx + 1]
                        consecutive = 0
            else:
                consecutive = 0

        assert level == 'intermediate'
        assert consecutive == 0

    def test_two_successes_intermediate_to_advanced(self):
        """2 succès consécutifs → intermediate passe à advanced."""
        levels = ['beginner', 'intermediate', 'advanced']
        level = 'intermediate'
        consecutive = 0

        for score in [90.0, 80.0]:
            if score >= 70:
                consecutive += 1
                if consecutive >= 2:
                    idx = levels.index(level)
                    if idx < len(levels) - 1:
                        level = levels[idx + 1]
                        consecutive = 0
            else:
                consecutive = 0

        assert level == 'advanced'

    def test_max_level_stays_advanced(self):
        """Niveau max : reste à advanced, pas d'erreur index."""
        levels = ['beginner', 'intermediate', 'advanced']
        level = 'advanced'
        idx = levels.index(level)
        next_level = levels[idx + 1] if idx < len(levels) - 1 else level
        assert next_level == 'advanced'

    def test_one_success_no_levelup(self):
        """1 seul succès → pas de changement de niveau."""
        levels = ['beginner', 'intermediate', 'advanced']
        level = 'beginner'
        consecutive = 1
        if consecutive >= 2:
            idx = levels.index(level)
            if idx < len(levels) - 1:
                level = levels[idx + 1]
        assert level == 'beginner'

    def test_full_sequence(self):
        """Séquence complète : beginner → intermediate → advanced."""
        levels = ['beginner', 'intermediate', 'advanced']
        idx = 0
        idx = min(idx + 1, len(levels) - 1)
        assert levels[idx] == 'intermediate'
        idx = min(idx + 1, len(levels) - 1)
        assert levels[idx] == 'advanced'
        idx = min(idx + 1, len(levels) - 1)
        assert levels[idx] == 'advanced'  # reste au max
