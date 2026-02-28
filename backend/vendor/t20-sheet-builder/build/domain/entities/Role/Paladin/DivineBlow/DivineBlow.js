"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.DivineBlow = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const DivineBlowEffect_1 = require("./DivineBlowEffect");
class DivineBlow extends RoleAbility_1.RoleAbility {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.divineBlow);
        this.effects = new Ability_1.AbilityEffects({
            triggered: {
                default: new DivineBlowEffect_1.DivineBlowEffect(),
            },
        });
    }
}
exports.DivineBlow = DivineBlow;
