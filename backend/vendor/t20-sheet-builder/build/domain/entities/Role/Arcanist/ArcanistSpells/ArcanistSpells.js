"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ArcanistSpells = void 0;
const AbilityEffects_1 = require("../../../Ability/AbilityEffects");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const SpellsAbility_1 = require("../../SpellsAbility");
const ArcanistSpellsEffect_1 = require("./ArcanistSpellsEffect");
class ArcanistSpells extends SpellsAbility_1.SpellsAbility {
    constructor(spells, learnFrequency, attribute) {
        super(RoleAbilityName_1.RoleAbilityName.arcanistSpells);
        this.effects = new AbilityEffects_1.AbilityEffects({
            passive: {
                default: new ArcanistSpellsEffect_1.ArcanistSpellsEffect(spells, learnFrequency, attribute),
            },
        });
    }
}
exports.ArcanistSpells = ArcanistSpells;
