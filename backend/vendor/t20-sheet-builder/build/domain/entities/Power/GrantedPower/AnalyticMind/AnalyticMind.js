"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.AnalyticMind = void 0;
const Ability_1 = require("../../../Ability");
const AbilityEffectsStatic_1 = require("../../../Ability/AbilityEffectsStatic");
const GrantedPower_1 = require("../GrantedPower");
const GrantedPowerName_1 = require("../GrantedPowerName");
const AnalyticMindEffect_1 = require("./AnalyticMindEffect");
class AnalyticMind extends GrantedPower_1.GrantedPower {
    constructor() {
        super(GrantedPowerName_1.GrantedPowerName.analyticMind);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new AnalyticMindEffect_1.AnalyticMindEffect(),
            },
        });
    }
}
exports.AnalyticMind = AnalyticMind;
AnalyticMind.powerName = GrantedPowerName_1.GrantedPowerName.analyticMind;
AnalyticMind.effects = new AbilityEffectsStatic_1.AbilityEffectsStatic({
    passive: {
        default: AnalyticMindEffect_1.AnalyticMindEffect,
    },
});
