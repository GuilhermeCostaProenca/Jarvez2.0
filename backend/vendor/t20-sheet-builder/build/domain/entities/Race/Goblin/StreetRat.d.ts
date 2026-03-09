import { AbilityEffects } from '../../Ability';
import { RaceAbility } from '../RaceAbility';
import { StreetRatEffect } from './StreetRatEffect';
export declare class StreetRat extends RaceAbility {
    effects: AbilityEffects<{
        passive: {
            default: StreetRatEffect;
        };
    }>;
    constructor();
}
