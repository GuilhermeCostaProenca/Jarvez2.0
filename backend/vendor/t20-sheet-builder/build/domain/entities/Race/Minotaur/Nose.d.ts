import { AbilityEffects } from '../../Ability';
import { RaceAbility } from '../RaceAbility';
import { NoseEffect } from './NoseEffect';
export declare class Nose extends RaceAbility {
    effects: AbilityEffects<{
        passive: {
            default: NoseEffect;
        };
    }>;
    constructor();
}
