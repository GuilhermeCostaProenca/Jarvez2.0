"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.EmptyMind = void 0;
const Ability_1 = require("../../../Ability");
const AbilityEffectsStatic_1 = require("../../../Ability/AbilityEffectsStatic");
const GrantedPower_1 = require("../GrantedPower");
const GrantedPowerName_1 = require("../GrantedPowerName");
const EmptyMindEffect_1 = require("./EmptyMindEffect");
class EmptyMind extends GrantedPower_1.GrantedPower {
    constructor() {
        super(GrantedPowerName_1.GrantedPowerName.emptyMind);
        this.effects = new Ability_1.AbilityEffects({
            passive: {
                default: new EmptyMindEffect_1.EmptyMindEffect(),
            },
        });
    }
}
exports.EmptyMind = EmptyMind;
EmptyMind.powerName = GrantedPowerName_1.GrantedPowerName.emptyMind;
EmptyMind.effects = new AbilityEffectsStatic_1.AbilityEffectsStatic({
    passive: {
        default: EmptyMindEffect_1.EmptyMindEffect,
    },
});
