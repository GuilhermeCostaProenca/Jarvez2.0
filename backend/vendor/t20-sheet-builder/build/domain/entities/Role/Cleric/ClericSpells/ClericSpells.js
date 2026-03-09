"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ClericSpells = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const SpellsAbility_1 = require("../../SpellsAbility");
const ClericSpellsEffect_1 = require("./ClericSpellsEffect");
class ClericSpells extends SpellsAbility_1.SpellsAbility {
    constructor(spells) {
        super(RoleAbilityName_1.RoleAbilityName.clericSpells);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new ClericSpellsEffect_1.ClericSpellsEffect(spells),
            },
        });
    }
}
exports.ClericSpells = ClericSpells;
