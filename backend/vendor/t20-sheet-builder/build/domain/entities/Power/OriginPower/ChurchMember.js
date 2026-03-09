"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.ChurchMember = void 0;
const AbilityEffects_1 = require("../../Ability/AbilityEffects");
const AbilityEffectsStatic_1 = require("../../Ability/AbilityEffectsStatic");
const OriginName_1 = require("../../Origin/OriginName");
const ChurchMemberEffect_1 = require("./ChurchMemberEffect");
const OriginPower_1 = require("./OriginPower");
const OriginPowerName_1 = require("./OriginPowerName");
class ChurchMember extends OriginPower_1.OriginPower {
    constructor() {
        super(OriginPowerName_1.OriginPowerName.churchMember);
        this.source = OriginName_1.OriginName.acolyte;
        this.effects = new AbilityEffects_1.AbilityEffects({
            roleplay: {
                default: new ChurchMemberEffect_1.ChurchMemberEffect(),
            },
        });
    }
    serialize() {
        return {
            name: OriginPowerName_1.OriginPowerName.churchMember,
            type: 'originPower',
            abilityType: 'power',
            effects: this.effects.serialize(),
        };
    }
}
exports.ChurchMember = ChurchMember;
ChurchMember.powerName = OriginPowerName_1.OriginPowerName.churchMember;
ChurchMember.effects = new AbilityEffectsStatic_1.AbilityEffectsStatic({
    roleplay: {
        default: ChurchMemberEffect_1.ChurchMemberEffect,
    },
});
