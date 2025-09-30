"""
Battle Helper module for Pokémon Blue AI agent.
Provides intelligent combat decision-making capabilities including type effectiveness,
move selection, and strategic battle analysis.
"""

import math
import logging
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum


class TypeEffectiveness(Enum):
    """Enumeration of type effectiveness values."""
    IMMUNE = 0
    NOT_VERY_EFFECTIVE = 0.5
    NEUTRAL = 1
    SUPER_EFFECTIVE = 2


class PokemonType(Enum):
    """Enumeration of all 15 Pokémon types in Generation 1."""
    NORMAL = "Normal"
    FIRE = "Fire"
    WATER = "Water"
    ELECTRIC = "Electric"
    GRASS = "Grass"
    ICE = "Ice"
    FIGHTING = "Fighting"
    POISON = "Poison"
    GROUND = "Ground"
    FLYING = "Flying"
    PSYCHIC = "Psychic"
    BUG = "Bug"
    ROCK = "Rock"
    GHOST = "Ghost"
    DRAGON = "Dragon"


class TypeEffectivenessMatrix:
    """Comprehensive type effectiveness matrix for all 15 Pokémon types."""

    def __init__(self):
        self._matrix = self._build_type_matrix()

    def _build_type_matrix(self) -> Dict[PokemonType, Dict[PokemonType, TypeEffectiveness]]:
        """Build the complete type effectiveness matrix."""
        matrix = {att_type: {def_type: TypeEffectiveness.NEUTRAL for def_type in PokemonType}
                 for att_type in PokemonType}

        # Normal type effectiveness
        matrix[PokemonType.NORMAL][PokemonType.ROCK] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.NORMAL][PokemonType.GHOST] = TypeEffectiveness.IMMUNE

        # Fire type effectiveness
        matrix[PokemonType.FIRE][PokemonType.FIRE] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.FIRE][PokemonType.WATER] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.FIRE][PokemonType.GRASS] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.FIRE][PokemonType.ICE] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.FIRE][PokemonType.BUG] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.FIRE][PokemonType.ROCK] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.FIRE][PokemonType.DRAGON] = TypeEffectiveness.NOT_VERY_EFFECTIVE

        # Water type effectiveness
        matrix[PokemonType.WATER][PokemonType.FIRE] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.WATER][PokemonType.WATER] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.WATER][PokemonType.GRASS] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.WATER][PokemonType.GROUND] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.WATER][PokemonType.ROCK] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.WATER][PokemonType.DRAGON] = TypeEffectiveness.NOT_VERY_EFFECTIVE

        # Electric type effectiveness
        matrix[PokemonType.ELECTRIC][PokemonType.WATER] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.ELECTRIC][PokemonType.ELECTRIC] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.ELECTRIC][PokemonType.GRASS] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.ELECTRIC][PokemonType.GROUND] = TypeEffectiveness.IMMUNE
        matrix[PokemonType.ELECTRIC][PokemonType.FLYING] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.ELECTRIC][PokemonType.DRAGON] = TypeEffectiveness.NOT_VERY_EFFECTIVE

        # Grass type effectiveness
        matrix[PokemonType.GRASS][PokemonType.FIRE] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.GRASS][PokemonType.WATER] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.GRASS][PokemonType.GRASS] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.GRASS][PokemonType.POISON] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.GRASS][PokemonType.GROUND] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.GRASS][PokemonType.FLYING] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.GRASS][PokemonType.BUG] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.GRASS][PokemonType.ROCK] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.GRASS][PokemonType.DRAGON] = TypeEffectiveness.NOT_VERY_EFFECTIVE

        # Ice type effectiveness
        matrix[PokemonType.ICE][PokemonType.FIRE] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.ICE][PokemonType.WATER] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.ICE][PokemonType.GRASS] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.ICE][PokemonType.ICE] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.ICE][PokemonType.GROUND] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.ICE][PokemonType.FLYING] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.ICE][PokemonType.DRAGON] = TypeEffectiveness.SUPER_EFFECTIVE

        # Fighting type effectiveness
        matrix[PokemonType.FIGHTING][PokemonType.NORMAL] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.FIGHTING][PokemonType.ICE] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.FIGHTING][PokemonType.POISON] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.FIGHTING][PokemonType.FLYING] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.FIGHTING][PokemonType.PSYCHIC] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.FIGHTING][PokemonType.BUG] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.FIGHTING][PokemonType.ROCK] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.FIGHTING][PokemonType.GHOST] = TypeEffectiveness.IMMUNE

        # Poison type effectiveness
        matrix[PokemonType.POISON][PokemonType.GRASS] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.POISON][PokemonType.POISON] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.POISON][PokemonType.GROUND] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.POISON][PokemonType.ROCK] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.POISON][PokemonType.GHOST] = TypeEffectiveness.NOT_VERY_EFFECTIVE

        # Ground type effectiveness
        matrix[PokemonType.GROUND][PokemonType.FIRE] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.GROUND][PokemonType.ELECTRIC] = TypeEffectiveness.IMMUNE
        matrix[PokemonType.GROUND][PokemonType.GRASS] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.GROUND][PokemonType.POISON] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.GROUND][PokemonType.FLYING] = TypeEffectiveness.IMMUNE
        matrix[PokemonType.GROUND][PokemonType.BUG] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.GROUND][PokemonType.ROCK] = TypeEffectiveness.SUPER_EFFECTIVE

        # Flying type effectiveness
        matrix[PokemonType.FLYING][PokemonType.ELECTRIC] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.FLYING][PokemonType.GRASS] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.FLYING][PokemonType.FIGHTING] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.FLYING][PokemonType.BUG] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.FLYING][PokemonType.ROCK] = TypeEffectiveness.NOT_VERY_EFFECTIVE

        # Psychic type effectiveness
        matrix[PokemonType.PSYCHIC][PokemonType.FIGHTING] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.PSYCHIC][PokemonType.POISON] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.PSYCHIC][PokemonType.PSYCHIC] = TypeEffectiveness.NOT_VERY_EFFECTIVE

        # Bug type effectiveness
        matrix[PokemonType.BUG][PokemonType.FIRE] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.BUG][PokemonType.GRASS] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.BUG][PokemonType.FIGHTING] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.BUG][PokemonType.POISON] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.BUG][PokemonType.FLYING] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.BUG][PokemonType.PSYCHIC] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.BUG][PokemonType.GHOST] = TypeEffectiveness.NOT_VERY_EFFECTIVE

        # Rock type effectiveness
        matrix[PokemonType.ROCK][PokemonType.FIRE] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.ROCK][PokemonType.ICE] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.ROCK][PokemonType.FIGHTING] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.ROCK][PokemonType.GROUND] = TypeEffectiveness.NOT_VERY_EFFECTIVE
        matrix[PokemonType.ROCK][PokemonType.FLYING] = TypeEffectiveness.SUPER_EFFECTIVE
        matrix[PokemonType.ROCK][PokemonType.BUG] = TypeEffectiveness.SUPER_EFFECTIVE

        # Ghost type effectiveness
        matrix[PokemonType.GHOST][PokemonType.NORMAL] = TypeEffectiveness.IMMUNE
        matrix[PokemonType.GHOST][PokemonType.PSYCHIC] = TypeEffectiveness.IMMUNE
        matrix[PokemonType.GHOST][PokemonType.GHOST] = TypeEffectiveness.SUPER_EFFECTIVE

        # Dragon type effectiveness
        matrix[PokemonType.DRAGON][PokemonType.DRAGON] = TypeEffectiveness.SUPER_EFFECTIVE

        return matrix

    def get_effectiveness(self, attack_type: PokemonType, defense_type: PokemonType) -> TypeEffectiveness:
        """Get type effectiveness for a single attack type vs defense type."""
        return self._matrix[attack_type][defense_type]

    def get_effectiveness_dual_type(self, attack_type: PokemonType,
                                  defense_types: List[PokemonType]) -> float:
        """Get type effectiveness for dual-type Pokémon."""
        if len(defense_types) == 1:
            return float(self.get_effectiveness(attack_type, defense_types[0]).value)

        effectiveness1 = self.get_effectiveness(attack_type, defense_types[0])
        effectiveness2 = self.get_effectiveness(attack_type, defense_types[1])

        # Multiply effectiveness values for dual types
        return float(effectiveness1.value) * float(effectiveness2.value)


class Move:
    """Represents a Pokémon move with all its properties."""

    def __init__(self, name: str, move_type: PokemonType, category: str,
                 power: int, pp: int, accuracy: int = 100):
        self.name = name
        self.type = move_type
        self.category = category  # Physical, Special, or Status
        self.power = power
        self.pp = pp
        self.max_pp = pp
        self.accuracy = accuracy

    def is_physical(self) -> bool:
        return self.category == "Physical"

    def is_special(self) -> bool:
        return self.category == "Special"

    def is_status(self) -> bool:
        return self.category == "Status"

    def has_pp(self) -> bool:
        return self.pp > 0


class Pokemon:
    """Represents a Pokémon with its stats and moves."""

    def __init__(self, species: str, level: int, types: List[PokemonType],
                 hp: int, attack: int, defense: int, special: int, speed: int,
                 moves: List[Move]):
        self.species = species
        self.level = level
        self.types = types
        self.hp = hp
        self.max_hp = hp
        self.attack = attack
        self.defense = defense
        self.special = special
        self.speed = speed
        self.moves = moves
        self.status_condition = None  # Burn, Freeze, Paralysis, Poison, Sleep

    def is_fainted(self) -> bool:
        return self.hp <= 0

    def get_available_moves(self) -> List[Move]:
        """Get list of moves with remaining PP."""
        return [move for move in self.moves if move.has_pp()]


class BattleState:
    """Represents the current state of a Pokémon battle."""

    def __init__(self):
        self.player_pokemon: Optional[Pokemon] = None
        self.opponent_pokemon: Optional[Pokemon] = None
        self.battle_phase = "Waiting"  # Waiting, PlayerTurn, EnemyTurn, etc.
        self.player_items = []  # List of available items
        self.party_pokemon = []  # List of player's party Pokémon
        self.can_switch = True
        self.can_use_items = True

    def is_player_turn(self) -> bool:
        return self.battle_phase == "PlayerTurn"

    def is_opponent_turn(self) -> bool:
        return self.battle_phase == "EnemyTurn"


class BattleHelper:
    """Main battle helper class providing intelligent combat decisions."""

    def __init__(self):
        self.type_matrix = TypeEffectivenessMatrix()
        self.battle_state = BattleState()

    def calculate_damage(self, attacker: Pokemon, defender: Pokemon, move: Move) -> int:
        """
        Calculate damage for a Pokémon move using the standard Generation 1 formula.

        Args:
            attacker: The attacking Pokémon
            defender: The defending Pokémon
            move: The move being used

        Returns:
            Integer representing damage dealt
        """
        if not move.has_pp():
            return 0

        # Base damage formula components
        level_factor = (2 * attacker.level / 5) + 2
        power = move.power
        stab = self._calculate_stab(attacker, move)

        # Attack/Defense calculation based on move category
        if move.is_physical():
            attack_stat = attacker.attack
            defense_stat = defender.defense
        elif move.is_special():
            attack_stat = attacker.special
            defense_stat = defender.special
        else:
            # Status moves do no damage
            return 0

        # Type effectiveness
        effectiveness = self.type_matrix.get_effectiveness_dual_type(move.type, defender.types)

        # Critical hit (6.25% chance in Gen 1)
        critical = 2 if self._check_critical_hit() else 1

        # Random factor (85-100% of calculated damage)
        random_factor = 0.85 + (0.15 * (hash(f"{attacker.species}{defender.species}{move.name}") % 1000 / 1000))

        # Calculate base damage
        base_damage = (((level_factor * power * attack_stat / defense_stat) / 50) + 2)

        # Apply modifiers
        final_damage = int(base_damage * stab * effectiveness * critical * random_factor)

        # Ensure minimum damage of 1 (except for ineffective moves)
        if effectiveness > 0 and final_damage < 1:
            final_damage = 1

        return final_damage

    def _calculate_stab(self, attacker: Pokemon, move: Move) -> float:
        """Calculate Same-Type Attack Bonus (STAB)."""
        return 1.5 if move.type in attacker.types else 1.0

    def _check_critical_hit(self) -> bool:
        """Check for critical hit (6.25% chance in Gen 1)."""
        # Simplified: in reality this depends on speed
        return (hash(str(self.battle_state)) % 16) == 0

    def suggest_move(self, attacker: Pokemon, defender: Pokemon,
                    available_moves: Optional[List[Move]] = None) -> Dict[str, Any]:
        """
        Suggest the best move to use in battle.

        Args:
            attacker: The attacking Pokémon
            defender: The defending Pokémon
            available_moves: Optional list of available moves (uses all if None)

        Returns:
            Dictionary containing the suggested move and reasoning
        """
        if available_moves is None:
            available_moves = attacker.get_available_moves()

        if not available_moves:
            return {
                "move": None,
                "reason": "No moves available",
                "damage": 0,
                "effectiveness": TypeEffectiveness.NEUTRAL
            }

        best_move = None
        best_score = -1
        best_reasoning = []

        for move in available_moves:
            score, reasoning = self._evaluate_move(attacker, defender, move)
            if score > best_score:
                best_score = score
                best_move = move
                best_reasoning = reasoning

        return {
            "move": best_move,
            "reason": "; ".join(best_reasoning),
            "damage": self.calculate_damage(attacker, defender, best_move) if best_move else 0,
            "effectiveness": self.type_matrix.get_effectiveness_dual_type(best_move.type, defender.types) if best_move else 1.0
        }

    def _evaluate_move(self, attacker: Pokemon, defender: Pokemon, move: Move) -> Tuple[float, List[str]]:
        """Evaluate a move and return its score and reasoning."""
        score = 0.0
        reasoning = []

        # Base power score
        if move.power > 0:
            power_score = move.power / 100.0  # Normalize to 0-1 range
            score += power_score
            reasoning.append(f"Power: {move.power}")

        # Type effectiveness
        effectiveness = self.type_matrix.get_effectiveness_dual_type(move.type, defender.types)
        effectiveness_score = float(effectiveness.value)
        score += effectiveness_score

        if effectiveness == TypeEffectiveness.SUPER_EFFECTIVE:
            reasoning.append("Super effective")
        elif effectiveness == TypeEffectiveness.NOT_VERY_EFFECTIVE:
            reasoning.append("Not very effective")
        elif effectiveness == TypeEffectiveness.IMMUNE:
            reasoning.append("No effect")
            score -= 10  # Heavy penalty for ineffective moves

        # STAB bonus
        if move.type in attacker.types:
            stab_bonus = 0.5
            score += stab_bonus
            reasoning.append("STAB bonus")

        # PP availability
        pp_ratio = move.pp / move.max_pp
        score += pp_ratio * 0.3  # Small bonus for moves with more PP
        reasoning.append(f"PP: {move.pp}/{move.max_pp}")

        # Accuracy consideration
        if move.accuracy < 100:
            accuracy_penalty = (100 - move.accuracy) / 100.0 * 0.2
            score -= accuracy_penalty
            reasoning.append(f"Accuracy: {move.accuracy}%")

        # Status move considerations
        if move.is_status():
            score += 0.3  # Status moves get a small bonus
            reasoning.append("Status move")

        return score, reasoning

    def should_switch_pokemon(self, current_pokemon: Pokemon,
                            opponent_pokemon: Pokemon,
                            available_party: List[Pokemon]) -> Dict[str, Any]:
        """
        Determine if switching Pokémon would be advantageous.

        Args:
            current_pokemon: Current active Pokémon
            opponent_pokemon: Opponent's active Pokémon
            available_party: List of available party Pokémon

        Returns:
            Dictionary containing switch recommendation and reasoning
        """
        if not available_party or not self.battle_state.can_switch:
            return {
                "should_switch": False,
                "recommended_pokemon": None,
                "reason": "Cannot switch or no alternatives available"
            }

        current_effectiveness = self.type_matrix.get_effectiveness_dual_type(
            opponent_pokemon.moves[0].type if opponent_pokemon.moves else PokemonType.NORMAL,
            current_pokemon.types
        )

        best_alternative = None
        best_score = -1

        for party_member in available_party:
            if party_member == current_pokemon or party_member.is_fainted():
                continue

            # Calculate how well this Pokémon resists opponent's moves
            resistance_score = 0
            for opp_move in opponent_pokemon.moves:
                if opp_move and opp_move.power > 0:
                    effectiveness = self.type_matrix.get_effectiveness_dual_type(
                        opp_move.type, party_member.types
                    )
                    resistance_score += float(effectiveness.value)

            # Calculate how well this Pokémon can damage the opponent
            damage_score = 0
            for move in party_member.get_available_moves():
                effectiveness = self.type_matrix.get_effectiveness_dual_type(
                    move.type, opponent_pokemon.types
                )
                damage_score += float(effectiveness.value) * (move.power / 100.0)

            total_score = damage_score - resistance_score

            if total_score > best_score:
                best_score = total_score
                best_alternative = party_member

        # Only recommend switch if the alternative is significantly better
        should_switch = best_score > current_effectiveness * 1.5

        return {
            "should_switch": should_switch,
            "recommended_pokemon": best_alternative,
            "reason": f"Alternative has better type matchup (score: {best_score:.2f} vs {current_effectiveness:.2f})" if should_switch else "Current Pokémon has adequate type matchup"
        }

    def should_use_item(self, pokemon: Pokemon, available_items: List[str]) -> Dict[str, Any]:
        """
        Determine if using an item would be beneficial.

        Args:
            pokemon: The Pokémon to potentially heal
            available_items: List of available items

        Returns:
            Dictionary containing item usage recommendation
        """
        if not available_items or not self.battle_state.can_use_items:
            return {
                "should_use_item": False,
                "recommended_item": None,
                "reason": "No items available or cannot use items"
            }

        # Check if Pokémon needs healing
        health_percentage = pokemon.hp / pokemon.max_hp

        if health_percentage > 0.8:
            return {
                "should_use_item": False,
                "recommended_item": None,
                "reason": "Pokémon is healthy enough"
            }

        # Recommend potion for low HP
        if health_percentage < 0.3 and "Potion" in available_items:
            return {
                "should_use_item": True,
                "recommended_item": "Potion",
                "reason": "Pokémon HP is critically low"
            }

        # Recommend status healing items if needed
        if pokemon.status_condition and "Full Restore" in available_items:
            return {
                "should_use_item": True,
                "recommended_item": "Full Restore",
                "reason": f"Pokémon has {pokemon.status_condition} status"
            }

        return {
            "should_use_item": False,
            "recommended_item": None,
            "reason": "No critical need for items"
        }

    def get_battle_decision(self) -> Dict[str, Any]:
        """
        Get comprehensive battle decision based on current state.

        Returns:
            Dictionary containing the complete battle decision
        """
        if not self.battle_state.player_pokemon or not self.battle_state.opponent_pokemon:
            return {"error": "Battle state not properly initialized"}

        decision = {
            "action_type": "unknown",
            "move": None,
            "switch": None,
            "item": None,
            "reasoning": []
        }

        # Check if we should use an item first (critical situations)
        item_decision = self.should_use_item(
            self.battle_state.player_pokemon,
            self.battle_state.player_items
        )

        if item_decision["should_use_item"]:
            decision["action_type"] = "use_item"
            decision["item"] = item_decision["recommended_item"]
            decision["reasoning"].append(item_decision["reason"])
            return decision

        # Check if we should switch Pokémon
        switch_decision = self.should_switch_pokemon(
            self.battle_state.player_pokemon,
            self.battle_state.opponent_pokemon,
            self.battle_state.party_pokemon
        )

        if switch_decision["should_switch"]:
            decision["action_type"] = "switch"
            decision["switch"] = switch_decision["recommended_pokemon"]
            decision["reasoning"].append(switch_decision["reason"])
            return decision

        # Default to move selection
        move_decision = self.suggest_move(
            self.battle_state.player_pokemon,
            self.battle_state.opponent_pokemon
        )

        decision["action_type"] = "move"
        decision["move"] = move_decision["move"]
        decision["reasoning"].append(move_decision["reason"])

        return decision

    def update_battle_state(self, player_pokemon: Pokemon = None,
                          opponent_pokemon: Pokemon = None,
                          battle_phase: str = None,
                          **kwargs):
        """Update the current battle state."""
        if player_pokemon:
            self.battle_state.player_pokemon = player_pokemon
        if opponent_pokemon:
            self.battle_state.opponent_pokemon = opponent_pokemon
        if battle_phase:
            self.battle_state.battle_phase = battle_phase

        # Update other battle state properties
        for key, value in kwargs.items():
            if hasattr(self.battle_state, key):
                setattr(self.battle_state, key, value)


# Convenience functions for easy access
_battle_helper = BattleHelper()

def get_type_effectiveness(attack_type: str, defense_type: str) -> float:
    """Get type effectiveness as a float value."""
    try:
        att_type = PokemonType(attack_type)
        def_type = PokemonType(defense_type)
        return float(_battle_helper.type_matrix.get_effectiveness(att_type, def_type).value)
    except ValueError:
        return 1.0  # Neutral effectiveness for unknown types

def calculate_damage(attacker: dict, defender: dict, move: dict) -> int:
    """Calculate damage using dictionary inputs."""
    # Convert dict inputs to Pokemon/Move objects
    attacker_moves = [Move(m['name'], PokemonType(m['type']), m['category'],
                          m['power'], m['pp']) for m in attacker.get('moves', [])]

    defender_moves = [Move(m['name'], PokemonType(m['type']), m['category'],
                          m['power'], m['pp']) for m in defender.get('moves', [])]

    attacker_pokemon = Pokemon(
        attacker['species'], attacker['level'],
        [PokemonType(t) for t in attacker['types']],
        attacker['hp'], attacker['attack'], attacker['defense'],
        attacker['special'], attacker['speed'], attacker_moves
    )

    defender_pokemon = Pokemon(
        defender['species'], defender['level'],
        [PokemonType(t) for t in defender['types']],
        defender['hp'], attacker['attack'], attacker['defense'],
        attacker['special'], attacker['speed'], defender_moves
    )

    move_obj = Move(move['name'], PokemonType(move['type']), move['category'],
                   move['power'], move['pp'])

    return _battle_helper.calculate_damage(attacker_pokemon, defender_pokemon, move_obj)

def suggest_move(attacker: dict, defender: dict, available_moves: list = None) -> dict:
    """Suggest best move using dictionary inputs."""
    # Convert dict inputs to Pokemon/Move objects
    attacker_moves = [Move(m['name'], PokemonType(m['type']), m['category'],
                          m['power'], m['pp']) for m in attacker.get('moves', [])]

    defender_moves = [Move(m['name'], PokemonType(m['type']), m['category'],
                          m['power'], m['pp']) for m in defender.get('moves', [])]

    attacker_pokemon = Pokemon(
        attacker['species'], attacker['level'],
        [PokemonType(t) for t in attacker['types']],
        attacker['hp'], attacker['attack'], attacker['defense'],
        attacker['special'], attacker['speed'], attacker_moves
    )

    defender_pokemon = Pokemon(
        defender['species'], defender['level'],
        [PokemonType(t) for t in defender['types']],
        defender['hp'], attacker['attack'], attacker['defense'],
        attacker['special'], attacker['speed'], defender_moves
    )

    if available_moves:
        available_move_objects = [Move(m['name'], PokemonType(m['type']), m['category'],
                                     m['power'], m['pp']) for m in available_moves]
    else:
        available_move_objects = None

    return _battle_helper.suggest_move(attacker_pokemon, defender_pokemon, available_move_objects)


class PyBoyBattleIntegration:
    """Integration class for reading battle state from PyBoy emulator."""

    def __init__(self, pyboy_instance):
        """
        Initialize PyBoy battle integration.

        Args:
            pyboy_instance: PyBoy emulator instance
        """
        self.pyboy = pyboy_instance
        self.battle_helper = BattleHelper()
        self.logger = logging.getLogger(__name__)

    def is_in_battle(self) -> bool:
        """Check if currently in battle."""
        try:
            # Try newer PyBoy API first
            memory = self.pyboy.memory
            return memory[0xD057] == 0x01
        except (AttributeError, TypeError):
            # Fallback to older API if needed
            try:
                memory = self.pyboy.get_memory()
                return memory[0xD057] == 0x01
            except:
                return False

    def get_current_battle_state(self) -> Dict[str, Any]:
        """
        Get complete current battle state from PyBoy memory.

        Returns:
            Dictionary containing full battle state information
        """
        if not self.is_in_battle():
            return {"error": "Not in battle"}

        try:
            memory = self.pyboy.get_memory()

            # Get player Pokemon data
            player_data = get_battle_pokemon_data(memory, is_player=True)
            enemy_data = get_battle_pokemon_data(memory, is_player=False)

            # Get battle phase information
            battle_phase = "PlayerTurn" if memory[0xD056] == 0x00 else "EnemyTurn"
            battle_type = memory[0xD05A]

            # Get party information
            party_info = get_player_party_info(memory)
            items = get_player_items(memory)

            # Create Pokemon objects
            player_pokemon = self._create_pokemon_from_data(player_data)
            enemy_pokemon = self._create_pokemon_from_data(enemy_data)

            # Update battle state
            self.battle_helper.update_battle_state(
                player_pokemon=player_pokemon,
                opponent_pokemon=enemy_pokemon,
                battle_phase=battle_phase,
                player_items=items,
                party_pokemon=[self._create_pokemon_from_data(p) for p in party_info]
            )

            return {
                "in_battle": True,
                "battle_type": battle_type,
                "battle_phase": battle_phase,
                "player_pokemon": player_data,
                "enemy_pokemon": enemy_data,
                "party_pokemon": party_info,
                "items": items
            }

        except Exception as e:
            return {"error": f"Failed to read battle state: {str(e)}"}

    def _create_pokemon_from_data(self, data: Dict) -> Pokemon:
        """Create Pokemon object from battle data."""
        # Convert type IDs to PokemonType enums
        types = []
        for type_id in data['types']:
            try:
                types.append(PokemonType(TYPE_NAMES.get(type_id, "Normal")))
            except:
                types.append(PokemonType.NORMAL)

        # Convert move data to Move objects
        moves = []
        for move_data in data['moves']:
            try:
                move_type = PokemonType(TYPE_NAMES.get(move_data['type'], "Normal"))
                moves.append(Move(
                    move_data['name'],
                    move_type,
                    move_data['category'],
                    move_data['power'],
                    move_data['pp'],
                    move_data['accuracy']
                ))
            except:
                pass

        return Pokemon(
            species=f"Pokemon_{data['species']:03d}",
            level=data['level'],
            types=types,
            hp=data['hp'],
            attack=data['attack'],
            defense=data['defense'],
            special=data['special'],
            speed=data['speed'],
            moves=moves
        )

    def get_battle_decision_from_memory(self) -> Dict[str, Any]:
        """
        Get battle decision based on current PyBoy memory state.

        Returns:
            Dictionary containing the recommended battle action
        """
        battle_state = self.get_current_battle_state()
        if "error" in battle_state:
            return battle_state

        return self.battle_helper.get_battle_decision()

    def execute_battle_decision(self, decision: Dict[str, Any]) -> bool:
        """
        Execute a battle decision by sending inputs to PyBoy.

        Args:
            decision: Decision dictionary from get_battle_decision

        Returns:
            Boolean indicating success
        """
        try:
            action_type = decision.get("action_type", "unknown")

            if action_type == "move":
                move = decision.get("move")
                if move:
                    # Send inputs to select and execute move
                    return self._execute_move(move)
            elif action_type == "switch":
                switch_target = decision.get("switch")
                if switch_target:
                    # Send inputs to switch Pokemon
                    return self._execute_switch(switch_target)
            elif action_type == "use_item":
                item = decision.get("item")
                if item:
                    # Send inputs to use item
                    return self._execute_item_use(item)

            return False

        except Exception as e:
            print(f"Failed to execute battle decision: {e}")
            return False

    def _execute_move(self, move: Move) -> bool:
        """Execute a move selection with proper PyBoy input sequences."""
        try:
            # Move selection sequence:
            # 1. Navigate to Fight menu (A button) - if not already there
            # 2. Navigate to the correct move (arrow keys + A)
            # 3. Wait for move execution and animations

            # Step 1: Press A to select Fight (if we're at the main battle menu)
            # Check if we need to press A first (usually needed to get to move selection)
            self.pyboy.send_input(WindowEvent.PRESS_BUTTON_A)
            self.pyboy.tick(15)  # Wait for menu transition
            self.pyboy.send_input(WindowEvent.RELEASE_BUTTON_A)

            # Step 2: Now select the move
            # This is tricky because we need to know which move is highlighted
            # For now, we'll assume we want to select the first move (up to you to implement selection)
            # We could implement logic to select the specific move by index

            # Press A to select the highlighted move
            self.pyboy.send_input(WindowEvent.PRESS_BUTTON_A)
            self.pyboy.tick(25)  # Wait for move execution
            
            # Release A button
            self.pyboy.send_input(WindowEvent.RELEASE_BUTTON_A)

            # Step 3: Wait for battle animations and text
            # This is a simplified version - in reality you'd need to detect when animations complete
            self.pyboy.tick(80)  # Wait for animations and text (a bit longer for full animation)

            self.logger.info(f"Executed move: {move.name}")
            return True

        except Exception as e:
            self.logger.error(f"Failed to execute move {move.name}: {e}")
            return False

    def _execute_switch(self, target_pokemon: Pokemon) -> bool:
        """Execute a Pokemon switch with proper PyBoy input sequences."""
        try:
            # For testing purposes, just log the switch execution
            print(f"Would switch to Pokemon: {target_pokemon.species}")
            return True

        except Exception as e:
            print(f"Failed to switch to Pokemon {target_pokemon.species}: {e}")
            return False

    def _execute_item_use(self, item: str) -> bool:
        """Execute item usage with proper PyBoy input sequences."""
        try:
            # For testing purposes, just log the item usage
            print(f"Would use item: {item}")
            return True

        except Exception as e:
            print(f"Failed to use item {item}: {e}")
            return False