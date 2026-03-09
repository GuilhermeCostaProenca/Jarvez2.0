"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Prototype = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const PrototypeEffect_1 = require("./PrototypeEffect");
class Prototype extends RoleAbility_1.RoleAbility {
    constructor(params) {
        super(RoleAbilityName_1.RoleAbilityName.prototype);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new PrototypeEffect_1.PrototypeEffect(params),
            },
        });
    }
}
exports.Prototype = Prototype;
