"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DruidSpells = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const SpellsAbility_1 = require("../../SpellsAbility");
const DruidSpellsEffect_1 = require("./DruidSpellsEffect");
class DruidSpells extends SpellsAbility_1.SpellsAbility {
    constructor(spells, schools) {
        super(RoleAbilityName_1.RoleAbilityName.druidSpells);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new DruidSpellsEffect_1.DruidSpellsEffect(spells, schools),
            },
        });
    }
}
exports.DruidSpells = DruidSpells;
