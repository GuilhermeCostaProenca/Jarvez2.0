"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.SpecialFriend = void 0;
const AbilityEffects_1 = require("../../Ability/AbilityEffects");
const AbilityEffectsStatic_1 = require("../../Ability/AbilityEffectsStatic");
const OriginName_1 = require("../../Origin/OriginName");
const OriginPower_1 = require("./OriginPower");
const OriginPowerName_1 = require("./OriginPowerName");
const SpecialFriendEffect_1 = require("./SpecialFriendEffect");
class SpecialFriend extends OriginPower_1.OriginPower {
    constructor(skill) {
        super(SpecialFriend.powerName);
        this.source = OriginName_1.OriginName.animalsFriend;
        this.effects = new AbilityEffects_1.AbilityEffects({
            passive: {
                default: new SpecialFriendEffect_1.SpecialFriendEffect(this.name, skill),
            },
        });
    }
    serialize() {
        return {
            name: SpecialFriend.powerName,
            skill: this.effects.passive.default.skill,
            type: 'originPower',
            abilityType: 'power',
            effects: this.effects.serialize(),
        };
    }
}
exports.SpecialFriend = SpecialFriend;
SpecialFriend.powerName = OriginPowerName_1.OriginPowerName.specialFriend;
SpecialFriend.effects = new AbilityEffectsStatic_1.AbilityEffectsStatic({
    passive: {
        default: SpecialFriendEffect_1.SpecialFriendEffect,
    },
});
