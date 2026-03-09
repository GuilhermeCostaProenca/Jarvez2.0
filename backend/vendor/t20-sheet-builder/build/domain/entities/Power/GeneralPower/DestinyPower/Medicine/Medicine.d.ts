import { AbilityEffects } from '../../../../Ability/AbilityEffects';
import { AbilityEffectsStatic } from '../../../../Ability/AbilityEffectsStatic';
import { GeneralPower } from '../../GeneralPower';
import { GeneralPowerGroup } from '../../GeneralPowerGroup';
import { GeneralPowerName } from '../../GeneralPowerName';
import { MedicineEffect } from './MedicineEffect';
export declare class Medicine extends GeneralPower {
    static readonly powerName = GeneralPowerName.medicine;
    static readonly effects: AbilityEffectsStatic;
    private static readonly wisdomRequirement;
    private static readonly cureRequirement;
    group: GeneralPowerGroup;
    effects: AbilityEffects<{
        activateable: {
            default: MedicineEffect;
        };
    }>;
    constructor();
}
