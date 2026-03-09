"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.BardSpells = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const BardSpellsEffect_1 = require("./BardSpellsEffect");
class BardSpells extends RoleAbility_1.RoleAbility {
    constructor(schools, spells) {
        super(RoleAbilityName_1.RoleAbilityName.bardSpells);
        this.schools = schools;
        this.spells = spells;
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new BardSpellsEffect_1.BardSpellsEffect(schools, spells),
            },
        });
    }
}
exports.BardSpells = BardSpells;
