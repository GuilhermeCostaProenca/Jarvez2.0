"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.FaithfulDevote = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const FaithfulDevoteEffect_1 = require("./FaithfulDevoteEffect");
class FaithfulDevote extends RoleAbility_1.RoleAbility {
    constructor(role) {
        const name = FaithfulDevote.abilityName[role];
        super(name);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new FaithfulDevoteEffect_1.FaithfulDevoteEffect(role, name),
            },
        });
    }
}
exports.FaithfulDevote = FaithfulDevote;
FaithfulDevote.abilityName = {
    cleric: RoleAbilityName_1.RoleAbilityName.clericFaithfulDevote,
    druid: RoleAbilityName_1.RoleAbilityName.druidFaithfulDevote,
};
