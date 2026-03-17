import { AbilityEffects } from '../../../Ability/AbilityEffects';
import { RaceAbility } from '../../RaceAbility';
import type { VersatileChoice } from './VersatileChoice';
import { VersatileEffect } from './VersatileEffect';
export declare class Versatile extends RaceAbility {
    effects: AbilityEffects<{
        passive: {
            default: VersatileEffect;
        };
    }>;
    constructor();
    addChoice(choice: VersatileChoice): void;
}
