import sys
import unittest
from pathlib import Path

try:
    from rpg_engine.character.service import generate_character_sheet
    from rpg_engine.threat.service import generate_threat_sheet
except ModuleNotFoundError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from rpg_engine.character.service import generate_character_sheet
    from rpg_engine.threat.service import generate_threat_sheet


class RPGEngineTests(unittest.TestCase):
    def test_character_strict_requires_explicit_bridge_choices(self):
        with self.assertRaises(ValueError):
            generate_character_sheet(
                {
                    "name": "StrictSemEscolhas",
                    "world": "tormenta20",
                    "race": "humano",
                    "class_name": "guerreiro",
                    "origin": "acolyte",
                    "generation_mode": "strict",
                }
            )

    def test_character_bridge_accepts_explicit_choices(self):
        result = generate_character_sheet(
            {
                "name": "StrictCompleto",
                "world": "tormenta20",
                "race": "humano",
                "class_name": "guerreiro",
                "origin": "acolyte",
                "generation_mode": "strict",
                "attributes": {
                    "forca": 14,
                    "destreza": 12,
                    "constituicao": 14,
                    "inteligencia": 10,
                    "sabedoria": 12,
                    "carisma": 8,
                },
                "build_choices": {
                    "role_skill_choices": [["fight"], ["initiative", "reflexes"]],
                    "race_choices": {
                        "attributes": ["strength", "constitution", "dexterity"],
                        "versatile_skill": "perception",
                        "versatile_power": "ironWill",
                    },
                    "origin_choices": {
                        "skill": "cure",
                        "general_power": "ironWill",
                    },
                    "equipment_choices": {
                        "simple_weapon": "dagger",
                        "martial_weapon": "longSword",
                        "armor": "leatherArmor",
                        "money": 30,
                    },
                },
            }
        )
        self.assertEqual(result.source, "t20-sheet-builder")
        self.assertEqual(result.status, "success")
        self.assertEqual(result.applied_choices["equipment_choices"]["armor"], "leatherArmor")
        self.assertEqual(result.applied_choices["origin_choices"]["skill"], "cure")

    def test_inventor_auto_build_uses_bridge_with_default_prototype(self):
        result = generate_character_sheet(
            {
                "name": "InventorAuto",
                "world": "tormenta20",
                "race": "humano",
                "class_name": "inventor",
                "origin": "animals_friend",
                "build_choices": {
                    "role_skill_choices": [["knowledge", "cure", "diplomacy", "initiative"]],
                },
            }
        )
        self.assertEqual(result.source, "t20-sheet-builder")
        self.assertEqual(result.status, "success")
        self.assertEqual(result.applied_choices["role_options"]["prototype_choice"], "superiorItem")
        self.assertTrue(result.warnings)

    def test_inventor_strict_requires_role_options(self):
        with self.assertRaises(ValueError):
            generate_character_sheet(
                {
                    "name": "InventorStrict",
                    "world": "tormenta20",
                    "race": "humano",
                    "class_name": "inventor",
                    "origin": "animals_friend",
                    "generation_mode": "strict",
                    "build_choices": {
                        "role_skill_choices": [["knowledge", "cure", "diplomacy", "initiative"]],
                        "race_choices": {
                            "attributes": ["intelligence", "constitution", "dexterity"],
                            "versatile_skill": "perception",
                            "versatile_power": "ironWill",
                        },
                        "origin_choices": {
                            "skill": "animalHandling",
                            "animal": "dog",
                        },
                        "equipment_choices": {
                            "simple_weapon": "dagger",
                            "martial_weapon": "longSword",
                            "armor": "leatherArmor",
                            "money": 20,
                        },
                    },
                }
            )

    def test_inventor_strict_accepts_explicit_alchemic_prototype(self):
        result = generate_character_sheet(
            {
                "name": "InventorStrictOk",
                "world": "tormenta20",
                "race": "humano",
                "class_name": "inventor",
                "origin": "animals_friend",
                "generation_mode": "strict",
                "attributes": {
                    "forca": 10,
                    "destreza": 12,
                    "constituicao": 10,
                    "inteligencia": 10,
                    "sabedoria": 10,
                    "carisma": 10,
                },
                "build_choices": {
                    "role_skill_choices": [["knowledge", "cure", "diplomacy", "initiative"]],
                    "role_options": {
                        "prototype_choice": "alchemicItems",
                        "prototype_alchemic": "acid",
                        "prototype_quantity": 10,
                    },
                    "race_choices": {
                        "attributes": ["intelligence", "constitution", "dexterity"],
                        "versatile_skill": "acrobatics",
                        "versatile_power": "dodge",
                    },
                    "origin_choices": {
                        "skill": "animalHandling",
                        "companion_skill": "acrobatics",
                        "animal": "dog",
                    },
                    "equipment_choices": {
                        "simple_weapon": "dagger",
                        "armor": "leatherArmor",
                        "money": 20,
                    },
                },
            }
        )
        self.assertEqual(result.source, "t20-sheet-builder")
        self.assertEqual(result.status, "success")
        self.assertEqual(result.applied_choices["role_options"]["prototype_choice"], "alchemicItems")
        self.assertEqual(result.applied_choices["role_options"]["prototype_quantity"], 10)

    def test_rogue_auto_build_uses_specialist_defaults(self):
        result = generate_character_sheet(
            {
                "name": "LadinoAuto",
                "world": "tormenta20",
                "race": "humano",
                "class_name": "ladino",
            }
        )
        self.assertEqual(result.source, "t20-sheet-builder")
        self.assertEqual(result.status, "success")
        self.assertTrue(result.applied_choices["role_options"]["specialist_skills"])
        self.assertTrue(result.warnings)

    def test_character_level_gt_one_falls_back_with_partial_status(self):
        result = generate_character_sheet(
            {
                "name": "Nivel5",
                "world": "tormenta20",
                "race": "humano",
                "class_name": "guerreiro",
                "level": 5,
            }
        )
        self.assertEqual(result.source, "fallback")
        self.assertEqual(result.status, "partial")
        self.assertEqual(result.normalized_sheet["level"], 5)
        self.assertTrue(result.warnings)

    def test_character_invalid_acolyte_requirement_raises(self):
        with self.assertRaises(ValueError):
            generate_character_sheet(
                {
                    "name": "SemSabedoria",
                    "world": "tormenta20",
                    "race": "humano",
                    "class_name": "guerreiro",
                    "origin": "acolyte",
                    "attributes": {
                        "forca": 14,
                        "destreza": 12,
                        "constituicao": 14,
                        "inteligencia": 10,
                        "sabedoria": 10,
                        "carisma": 8,
                    },
                }
            )

    def test_threat_overrides_replace_generated_sections(self):
        result = generate_threat_sheet(
            {
                "name": "Custom Boss",
                "challenge_level": "5",
                "attacks_override": [
                    {"name": "Mordida", "attack_bonus": 10, "damage": "20 dano", "action_type": "Padrao"}
                ],
                "abilities_override": [
                    {"name": "Salto", "summary": "Move 12m", "category": "mobilidade"}
                ],
            }
        )
        self.assertEqual(result.source, "jarvez-threat-generator")
        self.assertEqual(result.status, "success")
        self.assertEqual(result.normalized_threat["attacks"][0]["name"], "Mordida")
        self.assertEqual(result.normalized_threat["abilities"][0]["name"], "Salto")
        self.assertTrue(result.warnings)

    def test_threat_output_is_v2_schema(self):
        result = generate_threat_sheet({"name": "Schema", "challenge_level": "1"})
        data = result.normalized_threat
        self.assertEqual(data["schema_version"], 2)
        self.assertIn("special_qualities", data)
        self.assertIn("abilities", data)
        self.assertIn("boss_features", data)


if __name__ == "__main__":
    unittest.main()
