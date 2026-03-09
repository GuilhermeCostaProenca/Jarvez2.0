import { AbilityEffects } from '../../../Ability';
import { AbilityEffectsStatic } from '../../../Ability/AbilityEffectsStatic';
import { GrantedPower } from '../GrantedPower';
import { GrantedPowerName } from '../GrantedPowerName';
import { AnalyticMindEffect } from './AnalyticMindEffect';
export declare class AnalyticMind extends GrantedPower {
    static readonly powerName = GrantedPowerName.analyticMind;
    static readonly effects: AbilityEffectsStatic;
    effects: AbilityEffects<{
        passive: {
            default: AnalyticMindEffect;
        };
    }>;
    constructor();
}
