"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.PreyMark = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const PreyMarkEffect_1 = require("./PreyMarkEffect");
class PreyMark extends RoleAbility_1.RoleAbility {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.preyMark);
        this.effects = new Ability_1.AbilityEffects({
            activateable: {
                default: new PreyMarkEffect_1.PreyMarkEffect(),
            },
        });
    }
}
exports.PreyMark = PreyMark;
