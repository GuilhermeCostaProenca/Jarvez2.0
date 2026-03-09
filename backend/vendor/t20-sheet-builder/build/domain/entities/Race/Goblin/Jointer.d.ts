import { AbilityEffects } from '../../Ability';
import { RaceAbility } from '../RaceAbility';
import { JointerEffect } from './JointerEffect';
export declare class Jointer extends RaceAbility {
    effects: AbilityEffects<{
        passive: {
            default: JointerEffect;
        };
    }>;
    constructor();
}
