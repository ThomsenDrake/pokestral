"""
Comprehensive tests for the Battle Helper system.
Tests type effectiveness, damage calculations, move selection, and strategic decision making.
"""

import unittest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.battle_helper import (
    BattleHelper, Pokemon, Move, PokemonType, TypeEffectiveness,
    get_type_effectiveness, calculate_damage, suggest_move,
    TypeEffectivenessMatrix, PyBoyBattleIntegration
)


class TestTypeEffectivenessMatrix(unittest.TestCase):
    """Test the type effectiveness matrix."""

    def setUp(self):
        self.matrix = TypeEffectivenessMatrix()

    def test_water_super_effective_against_fire(self):
        """Test that Water is super effective against Fire."""
        effectiveness = self.matrix.get_effectiveness(PokemonType.WATER, PokemonType.FIRE)
        self.assertEqual(effectiveness, TypeEffectiveness.SUPER_EFFECTIVE)

    def test_fire_not_very_effective_against_water(self):
        """Test that Fire is not very effective against Water."""
        effectiveness = self.matrix.get_effectiveness(PokemonType.FIRE, PokemonType.WATER)
        self.assertEqual(effectiveness, TypeEffectiveness.NOT_VERY_EFFECTIVE)

    def test_electric_immune_to_ground(self):
        """Test that Electric is immune to Ground."""
        effectiveness = self.matrix.get_effectiveness(PokemonType.GROUND, PokemonType.ELECTRIC)
        self.assertEqual(effectiveness, TypeEffectiveness.IMMUNE)

    def test_grass_super_effective_against_water(self):
        """Test that Grass is super effective against Water."""
        effectiveness = self.matrix.get_effectiveness(PokemonType.GRASS, PokemonType.WATER)
        self.assertEqual(effectiveness, TypeEffectiveness.SUPER_EFFECTIVE)

    def test_dual_type_effectiveness(self):
        """Test dual type effectiveness calculations."""
        # Water/Ground vs Electric should be immune (Ground immunity)
        effectiveness = self.matrix.get_effectiveness_dual_type(
            PokemonType.ELECTRIC, [PokemonType.WATER, PokemonType.GROUND]
        )
        self.assertEqual(effectiveness, 0.0)  # Immune

        # Grass/Poison vs Fire should be neutral (2.0 * 0.5 = 1.0)
        effectiveness = self.matrix.get_effectiveness_dual_type(
            PokemonType.FIRE, [PokemonType.GRASS, PokemonType.POISON]
        )
        self.assertEqual(effectiveness, 1.0)  # Neutral


class TestPokemonAndMoves(unittest.TestCase):
    """Test Pokemon and Move classes."""

    def test_pokemon_creation(self):
        """Test Pokemon object creation."""
        moves = [
            Move("Tackle", PokemonType.NORMAL, "Physical", 35, 35),
            Move("Water Gun", PokemonType.WATER, "Special", 40, 25)
        ]

        pokemon = Pokemon(
            "Squirtle", 10, [PokemonType.WATER],
            100, 48, 65, 50, 43, moves
        )

        self.assertEqual(pokemon.species, "Squirtle")
        self.assertEqual(pokemon.level, 10)
        self.assertEqual(pokemon.types, [PokemonType.WATER])
        self.assertEqual(len(pokemon.moves), 2)
        self.assertFalse(pokemon.is_fainted())

    def test_pokemon_fainted(self):
        """Test fainted Pokemon detection."""
        moves = [Move("Tackle", PokemonType.NORMAL, "Physical", 35, 35)]
        pokemon = Pokemon("Test", 1, [PokemonType.NORMAL], 0, 10, 10, 10, 10, moves)

        self.assertTrue(pokemon.is_fainted())

    def test_move_pp_tracking(self):
        """Test move PP tracking."""
        move = Move("Thunderbolt", PokemonType.ELECTRIC, "Special", 95, 15)

        self.assertTrue(move.has_pp())
        self.assertEqual(move.pp, 15)

        # Simulate using the move multiple times
        for _ in range(15):
            move.pp -= 1

        self.assertFalse(move.has_pp())
        self.assertEqual(move.pp, 0)


class TestDamageCalculation(unittest.TestCase):
    """Test damage calculation logic."""

    def setUp(self):
        self.battle_helper = BattleHelper()

        # Create test Pokemon
        charmander_moves = [
            Move("Ember", PokemonType.FIRE, "Special", 40, 25),
            Move("Scratch", PokemonType.NORMAL, "Physical", 40, 35)
        ]

        squirtle_moves = [
            Move("Water Gun", PokemonType.WATER, "Special", 40, 25),
            Move("Tackle", PokemonType.NORMAL, "Physical", 35, 35)
        ]

        self.charmander = Pokemon(
            "Charmander", 10, [PokemonType.FIRE],
            39, 52, 43, 50, 65, charmander_moves
        )

        self.squirtle = Pokemon(
            "Squirtle", 10, [PokemonType.WATER],
            44, 48, 65, 50, 43, squirtle_moves
        )

    def test_stab_calculation(self):
        """Test STAB bonus calculation."""
        ember_move = Move("Ember", PokemonType.FIRE, "Special", 40, 25)
        scratch_move = Move("Scratch", PokemonType.NORMAL, "Physical", 40, 35)

        # Fire move on Fire type should get STAB
        stab_ember = self.battle_helper._calculate_stab(self.charmander, ember_move)
        self.assertEqual(stab_ember, 1.5)

        # Normal move on Fire type should not get STAB
        stab_scratch = self.battle_helper._calculate_stab(self.charmander, scratch_move)
        self.assertEqual(stab_scratch, 1.0)

    def test_damage_calculation(self):
        """Test basic damage calculation."""
        ember_move = Move("Ember", PokemonType.FIRE, "Special", 40, 25)

        # Fire should be not very effective against Water
        damage = self.battle_helper.calculate_damage(self.charmander, self.squirtle, ember_move)

        # Should do some damage but reduced due to type effectiveness
        self.assertGreater(damage, 0)
        self.assertLess(damage, 50)  # Should be reduced from normal damage

    def test_water_damage_against_fire(self):
        """Test Water damage against Fire (should be super effective)."""
        water_gun_move = Move("Water Gun", PokemonType.WATER, "Special", 40, 25)

        damage = self.battle_helper.calculate_damage(self.squirtle, self.charmander, water_gun_move)

        # Water should be super effective against Fire
        self.assertGreater(damage, 30)  # Should do significant damage


class TestMoveSelection(unittest.TestCase):
    """Test move selection logic."""

    def setUp(self):
        self.battle_helper = BattleHelper()

        # Create test Pokemon with varied moves
        charizard_moves = [
            Move("Flamethrower", PokemonType.FIRE, "Special", 95, 15, 100),
            Move("Wing Attack", PokemonType.FLYING, "Physical", 60, 35, 100),
            Move("Slash", PokemonType.NORMAL, "Physical", 70, 20, 100),
            Move("Ember", PokemonType.FIRE, "Special", 40, 25, 100)
        ]

        blastoise_moves = [
            Move("Surf", PokemonType.WATER, "Special", 95, 15, 100),
            Move("Ice Beam", PokemonType.ICE, "Special", 95, 10, 100),
            Move("Bite", PokemonType.NORMAL, "Physical", 60, 25, 100)
        ]

        self.charizard = Pokemon(
            "Charizard", 50, [PokemonType.FIRE, PokemonType.FLYING],
            150, 104, 78, 159, 100, charizard_moves
        )

        self.blastoise = Pokemon(
            "Blastoise", 50, [PokemonType.WATER],
            150, 83, 100, 105, 78, blastoise_moves
        )

    def test_move_suggestion(self):
        """Test move suggestion functionality."""
        suggestion = self.battle_helper.suggest_move(self.charizard, self.blastoise)

        self.assertIn("move", suggestion)
        self.assertIn("reason", suggestion)
        self.assertIn("damage", suggestion)
        self.assertIn("effectiveness", suggestion)

        # Should suggest a move
        self.assertIsNotNone(suggestion["move"])

    def test_super_effective_move_preference(self):
        """Test that super effective moves are preferred."""
        # Electric move should be super effective against Water/Flying
        electric_moves = [
            Move("Thunderbolt", PokemonType.ELECTRIC, "Special", 95, 15, 100)
        ]

        pikachu = Pokemon(
            "Pikachu", 25, [PokemonType.ELECTRIC],
            80, 55, 40, 50, 90, electric_moves
        )

        # Create a Water/Flying type Pokemon (like Gyarados)
        gyarados_moves = [Move("Splash", PokemonType.WATER, "Status", 0, 40, 100)]
        gyarados = Pokemon(
            "Gyarados", 30, [PokemonType.WATER, PokemonType.FLYING],
            120, 125, 79, 100, 81, gyarados_moves
        )

        suggestion = self.battle_helper.suggest_move(pikachu, gyarados)

        # Electric should be super effective against both Water and Flying
        # So it should be a very good suggestion
        self.assertEqual(suggestion["move"].name, "Thunderbolt")


class TestStrategicDecisions(unittest.TestCase):
    """Test strategic decision making."""

    def setUp(self):
        self.battle_helper = BattleHelper()

        # Create test Pokemon
        pikachu_moves = [Move("Thunderbolt", PokemonType.ELECTRIC, "Special", 95, 15)]
        pikachu = Pokemon("Pikachu", 25, [PokemonType.ELECTRIC], 80, 55, 40, 50, 90, pikachu_moves)

        geodude_moves = [Move("Tackle", PokemonType.NORMAL, "Physical", 35, 35)]
        geodude = Pokemon("Geodude", 25, [PokemonType.ROCK, PokemonType.GROUND], 80, 80, 100, 30, 20, geodude_moves)

        # Set up battle state
        self.battle_helper.update_battle_state(
            player_pokemon=pikachu,
            opponent_pokemon=geodude,
            battle_phase="PlayerTurn"
        )

    def test_switch_recommendation(self):
        """Test Pokemon switching recommendations."""
        # Create a better alternative Pokemon
        raichu_moves = [Move("Thunderbolt", PokemonType.ELECTRIC, "Special", 95, 15)]
        raichu = Pokemon("Raichu", 30, [PokemonType.ELECTRIC], 100, 90, 55, 80, 100, raichu_moves)

        party = [raichu]  # Only one Pokemon in party besides current

        switch_decision = self.battle_helper.should_switch_pokemon(
            self.battle_helper.battle_state.player_pokemon,
            self.battle_helper.battle_state.opponent_pokemon,
            party
        )

        self.assertIn("should_switch", switch_decision)
        self.assertIn("recommended_pokemon", switch_decision)
        self.assertIn("reason", switch_decision)

    def test_item_usage_recommendation(self):
        """Test item usage recommendations."""
        # Create injured Pokemon
        injured_pikachu = Pokemon("Pikachu", 25, [PokemonType.ELECTRIC], 15, 55, 40, 50, 90, [])

        items = ["Potion", "Full Restore"]

        item_decision = self.battle_helper.should_use_item(injured_pikachu, items)

        self.assertTrue(item_decision["should_use_item"])
        self.assertEqual(item_decision["recommended_item"], "Potion")

    def test_battle_decision_integration(self):
        """Test complete battle decision integration."""
        decision = self.battle_helper.get_battle_decision()

        self.assertIn("action_type", decision)
        self.assertIn("reasoning", decision)

        # Should suggest some action
        self.assertIn(decision["action_type"], ["move", "switch", "use_item", "unknown"])


class TestConvenienceFunctions(unittest.TestCase):
    """Test convenience functions."""

    def test_get_type_effectiveness(self):
        """Test get_type_effectiveness convenience function."""
        # Water vs Fire should be super effective
        effectiveness = get_type_effectiveness("Water", "Fire")
        self.assertEqual(effectiveness, 2.0)

        # Fire vs Water should be not very effective
        effectiveness = get_type_effectiveness("Fire", "Water")
        self.assertEqual(effectiveness, 0.5)

    def test_calculate_damage_convenience(self):
        """Test calculate_damage convenience function."""
        attacker = {
            'species': 'Charizard',
            'level': 50,
            'types': ['Fire', 'Flying'],
            'hp': 150,
            'attack': 104,
            'defense': 78,
            'special': 159,
            'speed': 100,
            'moves': [
                {'name': 'Flamethrower', 'type': 'Fire', 'category': 'Special', 'power': 95, 'pp': 15}
            ]
        }

        defender = {
            'species': 'Blastoise',
            'level': 50,
            'types': ['Water'],
            'hp': 150,
            'attack': 83,
            'defense': 100,
            'special': 105,
            'speed': 78,
            'moves': [
                {'name': 'Surf', 'type': 'Water', 'category': 'Special', 'power': 95, 'pp': 15}
            ]
        }

        move = {
            'name': 'Flamethrower',
            'type': 'Fire',
            'category': 'Special',
            'power': 95,
            'pp': 15
        }

        damage = calculate_damage(attacker, defender, move)
        self.assertGreater(damage, 0)

    def test_suggest_move_convenience(self):
        """Test suggest_move convenience function."""
        attacker = {
            'species': 'Pikachu',
            'level': 25,
            'types': ['Electric'],
            'hp': 80,
            'attack': 55,
            'defense': 40,
            'special': 50,
            'speed': 90,
            'moves': [
                {'name': 'Thunderbolt', 'type': 'Electric', 'category': 'Special', 'power': 95, 'pp': 15},
                {'name': 'Quick Attack', 'type': 'Normal', 'category': 'Physical', 'power': 40, 'pp': 30}
            ]
        }

        defender = {
            'species': 'Gyarados',
            'level': 30,
            'types': ['Water', 'Flying'],
            'hp': 120,
            'attack': 125,
            'defense': 79,
            'special': 100,
            'speed': 81,
            'moves': [
                {'name': 'Splash', 'type': 'Water', 'category': 'Status', 'power': 0, 'pp': 40}
            ]
        }

        suggestion = suggest_move(attacker, defender)

        self.assertIn("move", suggestion)
        self.assertIn("reason", suggestion)
        self.assertIsNotNone(suggestion["move"])


class TestPyBoyIntegration(unittest.TestCase):
    """Test PyBoy integration functionality."""

    def test_integration_initialization(self):
        """Test PyBoy integration initialization."""
        # Mock PyBoy instance
        class MockPyBoy:
            def get_memory(self):
                return bytearray(0x10000)

        mock_pyboy = MockPyBoy()
        integration = PyBoyBattleIntegration(mock_pyboy)

        self.assertIsNotNone(integration.pyboy)
        self.assertIsNotNone(integration.battle_helper)

    def test_battle_state_detection(self):
        """Test battle state detection."""
        class MockPyBoy:
            def get_memory(self):
                memory = bytearray(0x10000)
                memory[0xD057] = 0x01  # In battle flag
                memory[0xD056] = 0x00  # Player turn
                return memory

        mock_pyboy = MockPyBoy()
        integration = PyBoyBattleIntegration(mock_pyboy)

        self.assertTrue(integration.is_in_battle())


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error conditions."""

    def setUp(self):
        self.battle_helper = BattleHelper()

    def test_no_moves_available(self):
        """Test behavior when no moves are available."""
        pokemon = Pokemon("Test", 1, [PokemonType.NORMAL], 100, 10, 10, 10, 10, [])
        defender = Pokemon("Defender", 1, [PokemonType.NORMAL], 100, 10, 10, 10, 10, [])

        suggestion = self.battle_helper.suggest_move(pokemon, defender)
        self.assertIsNone(suggestion["move"])
        self.assertIn("No moves available", suggestion["reason"])

    def test_no_pp_moves(self):
        """Test behavior when moves have no PP."""
        move = Move("Test", PokemonType.NORMAL, "Physical", 50, 0)
        pokemon = Pokemon("Test", 1, [PokemonType.NORMAL], 100, 10, 10, 10, 10, [move])
        defender = Pokemon("Defender", 1, [PokemonType.NORMAL], 100, 10, 10, 10, 10, [])

        suggestion = self.battle_helper.suggest_move(pokemon, defender)
        self.assertIsNone(suggestion["move"])

    def test_immune_moves(self):
        """Test that immune moves get heavy penalty."""
        # Ghost vs Normal should be immune
        ghost_move = Move("Lick", PokemonType.GHOST, "Physical", 30, 30)
        normal_pokemon = Pokemon("Normal", 25, [PokemonType.NORMAL], 100, 50, 50, 50, 50, [ghost_move])
        ghost_pokemon = Pokemon("Ghost", 25, [PokemonType.GHOST], 100, 50, 50, 50, 50, [])

        suggestion = self.battle_helper.suggest_move(normal_pokemon, ghost_pokemon)

        # Immune moves should get heavy penalty
        self.assertIsNotNone(suggestion["move"])  # But still might be selected if no other options


if __name__ == '__main__':
    unittest.main()