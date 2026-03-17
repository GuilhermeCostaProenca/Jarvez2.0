import { AbilityEffects } from '../../Ability';
import { RaceAbility } from '../RaceAbility';
import { AllihannaArmorEffect } from './AllihannaArmorEffect';
export declare class AllihannaArmor extends RaceAbility {
    effects: AbilityEffects<{
        activateable: {
            default: AllihannaArmorEffect;
        };
    }>;
    constructor();
}
