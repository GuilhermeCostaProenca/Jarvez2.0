import { AbilityEffects } from '../../Ability/AbilityEffects';
import { AbilityEffectsStatic } from '../../Ability/AbilityEffectsStatic';
import { type SerializedChurchMember, type SerializedOriginPower } from '../../Origin/OriginBenefit/SerializedOriginBenefit';
import { OriginName } from '../../Origin/OriginName';
import { ChurchMemberEffect } from './ChurchMemberEffect';
import { OriginPower } from './OriginPower';
import { OriginPowerName } from './OriginPowerName';
export declare class ChurchMember extends OriginPower<SerializedChurchMember> {
    static readonly powerName = OriginPowerName.churchMember;
    static readonly effects: AbilityEffectsStatic;
    source: OriginName;
    effects: AbilityEffects<{
        roleplay: {
            default: ChurchMemberEffect;
        };
    }>;
    constructor();
    serialize(): SerializedOriginPower<SerializedChurchMember>;
}
