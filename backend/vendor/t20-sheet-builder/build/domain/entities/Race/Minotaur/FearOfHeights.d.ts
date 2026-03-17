import { AbilityEffects } from '../../Ability';
import { RaceAbility } from '../RaceAbility';
import { FearOfHeightsEffect } from './FearOfHeightsEffect';
export declare class FearOfHeights extends RaceAbility {
    effects: AbilityEffects<{
        passive: {
            default: FearOfHeightsEffect;
        };
    }>;
    constructor();
}
