"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Bulwark = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const BulwarkEffect_1 = require("./BulwarkEffect");
class Bulwark extends RoleAbility_1.RoleAbility {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.bulwark);
        this.effects = new Ability_1.AbilityEffects({
            triggered: {
                default: new BulwarkEffect_1.BulwarkEffect(),
            },
        });
    }
}
exports.Bulwark = Bulwark;
