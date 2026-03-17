import { AbilityEffects } from '../../../Ability/AbilityEffects';
import { RaceAbility } from '../../RaceAbility';
import { SlowAndAlwaysEffect } from './SlowAndAlwaysEffect';
export declare class SlowAndAlways extends RaceAbility {
    effects: AbilityEffects<{
        passive: {
            default: SlowAndAlwaysEffect;
        };
    }>;
    constructor();
}
