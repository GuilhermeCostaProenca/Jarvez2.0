import { AbilityEffects } from '../../Ability';
import { RaceAbility } from '../RaceAbility';
import { HornesEffect } from './HornesEffect';
export declare class Hornes extends RaceAbility {
    effects: AbilityEffects<{
        passive: {
            default: HornesEffect;
        };
    }>;
    constructor();
}
