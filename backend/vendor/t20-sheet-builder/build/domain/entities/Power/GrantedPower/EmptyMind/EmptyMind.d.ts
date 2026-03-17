import { AbilityEffects } from '../../../Ability';
import { AbilityEffectsStatic } from '../../../Ability/AbilityEffectsStatic';
import { GrantedPower } from '../GrantedPower';
import { GrantedPowerName } from '../GrantedPowerName';
import { EmptyMindEffect } from './EmptyMindEffect';
export declare class EmptyMind extends GrantedPower {
    static readonly powerName = GrantedPowerName.emptyMind;
    static readonly effects: AbilityEffectsStatic;
    effects: AbilityEffects<{
        passive: {
            default: EmptyMindEffect;
        };
    }>;
    constructor();
}
