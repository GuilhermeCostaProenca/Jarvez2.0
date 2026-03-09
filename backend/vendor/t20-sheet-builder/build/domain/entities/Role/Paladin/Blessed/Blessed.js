"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Blessed = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const BlessedPassiveEffect_1 = require("./BlessedPassiveEffect");
class Blessed extends RoleAbility_1.RoleAbility {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.blessed);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new BlessedPassiveEffect_1.BlessedPassiveEffect(),
            },
        });
    }
}
exports.Blessed = Blessed;
