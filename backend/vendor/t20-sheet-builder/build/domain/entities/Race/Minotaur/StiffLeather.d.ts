import { AbilityEffects } from '../../Ability';
import { RaceAbility } from '../RaceAbility';
import { StiffLeatherEffect } from './StiffLeatherEffect';
export declare class StiffLeather extends RaceAbility {
    effects: AbilityEffects<{
        passive: {
            default: StiffLeatherEffect;
        };
    }>;
    constructor();
}
