import { AbilityEffects } from '../../../../Ability/AbilityEffects';
import { AbilityEffectsStatic } from '../../../../Ability/AbilityEffectsStatic';
import { GeneralPowerName } from '../../GeneralPowerName';
import { TormentaPower } from '../TormentaPower';
import { ShellEffect } from './ShellEffect';
export declare class Shell extends TormentaPower {
    static powerName: GeneralPowerName;
    static effects: AbilityEffectsStatic;
    effects: AbilityEffects<{
        passive: {
            default: ShellEffect;
        };
    }>;
    constructor();
}
