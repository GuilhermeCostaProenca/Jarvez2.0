"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Ingenuity = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const IngenuityEffect_1 = require("./IngenuityEffect");
class Ingenuity extends RoleAbility_1.RoleAbility {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.ingenuity);
        this.effects = new Ability_1.AbilityEffects({
            triggered: {
                default: new IngenuityEffect_1.IngenuityEffect(),
            },
        });
    }
}
exports.Ingenuity = Ingenuity;
