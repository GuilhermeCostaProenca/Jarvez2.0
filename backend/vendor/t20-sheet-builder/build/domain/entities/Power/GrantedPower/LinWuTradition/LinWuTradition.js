"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.LiWuTradition = void 0;
const Ability_1 = require("../../../Ability");
const AbilityEffectsStatic_1 = require("../../../Ability/AbilityEffectsStatic");
const GrantedPower_1 = require("../GrantedPower");
const GrantedPowerName_1 = require("../GrantedPowerName");
const LinWuTraditionEffect_1 = require("./LinWuTraditionEffect");
class LiWuTradition extends GrantedPower_1.GrantedPower {
    constructor() {
        super(GrantedPowerName_1.GrantedPowerName.linWuTradition);
        this.effects = new Ability_1.AbilityEffects({
            roleplay: {
                default: new LinWuTraditionEffect_1.LinWuTraditionEffect(),
            },
        });
    }
}
exports.LiWuTradition = LiWuTradition;
LiWuTradition.powerName = GrantedPowerName_1.GrantedPowerName.linWuTradition;
LiWuTradition.effects = new AbilityEffectsStatic_1.AbilityEffectsStatic({
    roleplay: {
        default: LinWuTraditionEffect_1.LinWuTraditionEffect,
    },
});
