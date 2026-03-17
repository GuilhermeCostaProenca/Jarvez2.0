import type { AbilityEffectsInterface } from '../../Ability/AbilityEffects';
import { AbilityEffectsStatic } from '../../Ability/AbilityEffectsStatic';
import { type SerializedOriginPower, type SerializedSpecialFriend } from '../../Origin/OriginBenefit/SerializedOriginBenefit';
import { OriginName } from '../../Origin/OriginName';
import { type SkillName } from '../../Skill/SkillName';
import { OriginPower } from './OriginPower';
import { OriginPowerName } from './OriginPowerName';
import { SpecialFriendEffect } from './SpecialFriendEffect';
export declare class SpecialFriend extends OriginPower<SerializedSpecialFriend> {
    static readonly powerName = OriginPowerName.specialFriend;
    static readonly effects: AbilityEffectsStatic;
    source: OriginName;
    effects: AbilityEffectsInterface & {
        passive: {
            default: SpecialFriendEffect;
        };
    };
    constructor(skill: SkillName);
    serialize(): SerializedOriginPower<SerializedSpecialFriend>;
}
