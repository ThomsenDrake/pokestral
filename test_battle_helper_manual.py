#!/usr/bin/env python3
"""
Manual testing script for battle helper functionality.
Tests core components without running the full test suite.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_move_name_resolution():
    """Test that move names are properly resolved and displayed."""
    print("Testing move name resolution...")

    try:
        from tools.battle_helper import Move, PokemonType

        # Create test moves with proper names
        thunderbolt = Move("Thunderbolt", PokemonType.ELECTRIC, "Special", 95, 15)
        water_gun = Move("Water Gun", PokemonType.WATER, "Special", 40, 25)
        tackle = Move("Tackle", PokemonType.NORMAL, "Physical", 35, 35)

        # Test that move names are correctly stored and accessible
        assert thunderbolt.name == "Thunderbolt", f"Expected 'Thunderbolt', got '{thunderbolt.name}'"
        assert water_gun.name == "Water Gun", f"Expected 'Water Gun', got '{water_gun.name}'"
        assert tackle.name == "Tackle", f"Expected 'Tackle', got '{tackle.name}'"

        print("✓ Move names are correctly resolved and accessible")
        return True

    except Exception as e:
        print(f"✗ Move name resolution test failed: {e}")
        return False

def test_type_effectiveness():
    """Test type effectiveness calculations."""
    print("Testing type effectiveness calculations...")

    try:
        from tools.battle_helper import TypeEffectivenessMatrix, PokemonType, TypeEffectiveness

        matrix = TypeEffectivenessMatrix()

        # Test basic type effectiveness
        water_vs_fire = matrix.get_effectiveness(PokemonType.WATER, PokemonType.FIRE)
        fire_vs_water = matrix.get_effectiveness(PokemonType.FIRE, PokemonType.WATER)
        electric_vs_ground = matrix.get_effectiveness(PokemonType.GROUND, PokemonType.ELECTRIC)

        assert water_vs_fire == TypeEffectiveness.SUPER_EFFECTIVE, "Water should be super effective against Fire"
        assert fire_vs_water == TypeEffectiveness.NOT_VERY_EFFECTIVE, "Fire should not be very effective against Water"
        assert electric_vs_ground == TypeEffectiveness.IMMUNE, "Ground should be immune to Electric"

        print("✓ Type effectiveness calculations are working correctly")
        return True

    except Exception as e:
        print(f"✗ Type effectiveness test failed: {e}")
        return False

def test_pokemon_creation():
    """Test Pokemon object creation and properties."""
    print("Testing Pokemon object creation...")

    try:
        from tools.battle_helper import Pokemon, Move, PokemonType

        # Create test Pokemon
        pikachu_moves = [
            Move("Thunderbolt", PokemonType.ELECTRIC, "Special", 95, 15),
            Move("Quick Attack", PokemonType.NORMAL, "Physical", 40, 30)
        ]

        pikachu = Pokemon(
            "Pikachu", 25, [PokemonType.ELECTRIC],
            80, 55, 40, 50, 90, pikachu_moves
        )

        assert pikachu.species == "Pikachu", f"Expected species 'Pikachu', got '{pikachu.species}'"
        assert pikachu.level == 25, f"Expected level 25, got {pikachu.level}"
        assert len(pikachu.types) == 1, f"Expected 1 type, got {len(pikachu.types)}"
        assert pikachu.types[0] == PokemonType.ELECTRIC, "Pikachu should be Electric type"
        assert len(pikachu.moves) == 2, f"Expected 2 moves, got {len(pikachu.moves)}"
        assert not pikachu.is_fainted(), "Pikachu should not be fainted"

        # Test available moves
        available_moves = pikachu.get_available_moves()
        assert len(available_moves) == 2, f"Expected 2 available moves, got {len(available_moves)}"

        print("✓ Pokemon object creation and properties are working correctly")
        return True

    except Exception as e:
        print(f"✗ Pokemon creation test failed: {e}")
        return False

def test_damage_calculation():
    """Test damage calculation logic."""
    print("Testing damage calculation...")

    try:
        from tools.battle_helper import Pokemon, Move, PokemonType, BattleHelper

        # Create test Pokemon
        charmander_moves = [Move("Ember", PokemonType.FIRE, "Special", 40, 25)]
        squirtle_moves = [Move("Water Gun", PokemonType.WATER, "Special", 40, 25)]

        charmander = Pokemon("Charmander", 10, [PokemonType.FIRE], 39, 52, 43, 50, 65, charmander_moves)
        squirtle = Pokemon("Squirtle", 10, [PokemonType.WATER], 44, 48, 65, 50, 43, squirtle_moves)

        battle_helper = BattleHelper()

        # Test STAB calculation
        ember_move = charmander.moves[0]
        stab = battle_helper._calculate_stab(charmander, ember_move)
        assert stab == 1.5, f"Expected STAB 1.5 for Fire move on Fire Pokemon, got {stab}"

        # Test damage calculation
        damage = battle_helper.calculate_damage(charmander, squirtle, ember_move)
        assert damage > 0, "Damage should be greater than 0"
        assert damage < 50, "Damage should be reduced due to type effectiveness"

        print("✓ Damage calculation is working correctly")
        return True

    except Exception as e:
        print(f"✗ Damage calculation test failed: {e}")
        return False

def test_move_suggestion():
    """Test move suggestion logic."""
    print("Testing move suggestion logic...")

    try:
        from tools.battle_helper import Pokemon, Move, PokemonType, BattleHelper

        # Create test Pokemon with varied moves
        pikachu_moves = [
            Move("Thunderbolt", PokemonType.ELECTRIC, "Special", 95, 15),
            Move("Quick Attack", PokemonType.NORMAL, "Physical", 40, 30)
        ]

        gyarados_moves = [Move("Splash", PokemonType.WATER, "Status", 0, 40)]

        pikachu = Pokemon("Pikachu", 25, [PokemonType.ELECTRIC], 80, 55, 40, 50, 90, pikachu_moves)
        gyarados = Pokemon("Gyarados", 30, [PokemonType.WATER, PokemonType.FLYING], 120, 125, 79, 100, 81, gyarados_moves)

        battle_helper = BattleHelper()

        # Test move suggestion
        suggestion = battle_helper.suggest_move(pikachu, gyarados)

        assert "move" in suggestion, "Suggestion should contain 'move' key"
        assert "reason" in suggestion, "Suggestion should contain 'reason' key"
        assert "damage" in suggestion, "Suggestion should contain 'damage' key"
        assert "effectiveness" in suggestion, "Suggestion should contain 'effectiveness' key"

        # Electric should be super effective against Water/Flying
        assert suggestion["move"] is not None, "Should suggest a move"
        assert suggestion["move"].name == "Thunderbolt", f"Should suggest Thunderbolt, got {suggestion['move'].name}"

        print("✓ Move suggestion logic is working correctly")
        return True

    except Exception as e:
        print(f"✗ Move suggestion test failed: {e}")
        return False

def test_mock_pyboy_integration():
    """Test PyBoy integration with mock interface."""
    print("Testing PyBoy integration with mock interface...")

    try:
        from tools.battle_helper import PyBoyBattleIntegration

        # Create mock PyBoy instance
        class MockPyBoy:
            def get_memory(self):
                memory = bytearray(0x10000)
                memory[0xD057] = 0x01  # In battle flag
                memory[0xD056] = 0x00  # Player turn
                return memory

        mock_pyboy = MockPyBoy()
        integration = PyBoyBattleIntegration(mock_pyboy)

        # Test battle state detection
        assert integration.is_in_battle(), "Should detect being in battle"

        # Test battle decision from memory
        decision = integration.get_battle_decision_from_memory()
        assert "error" not in decision, f"Should not have error in decision: {decision}"

        # Test decision execution
        success = integration.execute_battle_decision(decision)
        assert success, "Decision execution should succeed"

        print("✓ PyBoy integration with mock interface is working correctly")
        return True

    except Exception as e:
        print(f"✗ PyBoy integration test failed: {e}")
        return False

def test_error_handling():
    """Test error handling for edge cases."""
    print("Testing error handling for edge cases...")

    try:
        from tools.battle_helper import Pokemon, Move, PokemonType, BattleHelper

        battle_helper = BattleHelper()

        # Test Pokemon with no moves
        pokemon_no_moves = Pokemon("Test", 1, [PokemonType.NORMAL], 100, 10, 10, 10, 10, [])
        defender = Pokemon("Defender", 1, [PokemonType.NORMAL], 100, 10, 10, 10, 10, [])

        suggestion = battle_helper.suggest_move(pokemon_no_moves, defender)
        assert suggestion["move"] is None, "Should return None move for Pokemon with no moves"
        assert "No moves available" in suggestion["reason"], "Should indicate no moves available"

        # Test Pokemon with no PP
        no_pp_move = Move("Test", PokemonType.NORMAL, "Physical", 50, 0)
        pokemon_no_pp = Pokemon("Test", 1, [PokemonType.NORMAL], 100, 10, 10, 10, 10, [no_pp_move])

        suggestion = battle_helper.suggest_move(pokemon_no_pp, defender)
        assert suggestion["move"] is None, "Should return None move for moves with no PP"

        print("✓ Error handling for edge cases is working correctly")
        return True

    except Exception as e:
        print(f"✗ Error handling test failed: {e}")
        return False

def run_all_tests():
    """Run all manual tests."""
    print("=== Battle Helper Enhancement Validation Tests ===\n")

    tests = [
        ("Move Name Resolution", test_move_name_resolution),
        ("Type Effectiveness", test_type_effectiveness),
        ("Pokemon Creation", test_pokemon_creation),
        ("Damage Calculation", test_damage_calculation),
        ("Move Suggestion", test_move_suggestion),
        ("Mock PyBoy Integration", test_mock_pyboy_integration),
        ("Error Handling", test_error_handling),
    ]

    results = []
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"✗ {test_name} crashed: {e}")
            results.append((test_name, False))

    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY:")
    print("="*50)

    passed = 0
    failed = 0

    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name"<25"} {status}")
        if result:
            passed += 1
        else:
            failed += 1

    print("-" * 50)
    print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")

    if failed == 0:
        print("\n🎉 All tests passed! Battle helper enhancements are working correctly.")
        return True
    else:
        print(f"\n❌ {failed} test(s) failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)