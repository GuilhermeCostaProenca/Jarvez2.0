"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SpecialAttack = void 0;
const AbilityEffects_1 = require("../../../Ability/AbilityEffects");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const SpecialAttackEffect_1 = require("./SpecialAttackEffect");
class SpecialAttack extends RoleAbility_1.RoleAbility {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.specialAttack);
        this.effects = new AbilityEffects_1.AbilityEffects({
            triggered: {
                default: new SpecialAttackEffect_1.SpecialAttackEffect(),
            },
        });
    }
}
exports.SpecialAttack = SpecialAttack;
