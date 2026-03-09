"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.Fight = void 0;
const Ability_1 = require("../../../Ability");
const RoleAbility_1 = require("../../RoleAbility");
const RoleAbilityName_1 = require("../../RoleAbilityName");
const FightEffect_1 = require("./FightEffect");
class Fight extends RoleAbility_1.RoleAbility {
    constructor() {
        super(RoleAbilityName_1.RoleAbilityName.fight);
        this.effects = new Ability_1.AbilityEffects({
            roleplay: {
                default: new FightEffect_1.FightEffect(),
            },
        });
    }
}
exports.Fight = Fight;
