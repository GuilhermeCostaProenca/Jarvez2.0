"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Inspiration = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const InspirationEffect_1 = require("./InspirationEffect");
class Inspiration extends RoleAbility_1.RoleAbility {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.inspiration);
        this.effects = new Ability_1.AbilityEffects({
            activateable: {
                default: new InspirationEffect_1.InspirationEffect(),
            },
        });
    }
}
exports.Inspiration = Inspiration;
