import { AbilityEffects } from '../../../../Ability/AbilityEffects';
import { DodgeEffect } from './DodgeEffect';
import { GeneralPower } from '../../GeneralPower';
import { GeneralPowerName } from '../../GeneralPowerName';
import { GeneralPowerGroup } from '../../GeneralPowerGroup';
import { AbilityEffectsStatic } from '../../../../Ability/AbilityEffectsStatic';
export declare class Dodge extends GeneralPower {
    static readonly powerName = GeneralPowerName.dodge;
    static readonly effects: AbilityEffectsStatic;
    private static readonly requirement;
    group: GeneralPowerGroup;
    effects: AbilityEffects<{
        passive: {
            default: DodgeEffect;
        };
    }>;
    constructor();
}
