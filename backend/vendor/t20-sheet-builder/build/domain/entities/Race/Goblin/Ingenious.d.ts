import { AbilityEffects } from '../../Ability';
import { RaceAbility } from '../RaceAbility';
import { IngeniousEffect } from './IngeniousEffect';
export declare class Ingenious extends RaceAbility {
    effects: AbilityEffects<{
        passive: {
            default: IngeniousEffect;
        };
    }>;
    constructor();
}
