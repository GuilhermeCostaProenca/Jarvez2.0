import { AbilityEffects } from '../../../../Ability/AbilityEffects';
import { GeneralPower } from '../../GeneralPower';
import { GeneralPowerName } from '../../GeneralPowerName';
import { IronWillEffect } from './IronWillEffect';
import { GeneralPowerGroup } from '../../GeneralPowerGroup';
import { AbilityEffectsStatic } from '../../../../Ability/AbilityEffectsStatic';
export declare class IronWill extends GeneralPower {
    static readonly powerName = GeneralPowerName.ironWill;
    static readonly effects: AbilityEffectsStatic;
    group: GeneralPowerGroup;
    effects: AbilityEffects<{
        passive: {
            default: IronWillEffect;
        };
    }>;
    constructor();
}
