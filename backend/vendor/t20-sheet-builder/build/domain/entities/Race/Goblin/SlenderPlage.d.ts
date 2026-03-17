import { AbilityEffects } from '../../Ability/AbilityEffects';
import { RaceAbility } from '../RaceAbility';
import { SlenderPlageEffect } from './SlenderPlageEffect';
export declare class SlenderPlage extends RaceAbility {
    effects: AbilityEffects<{
        passive: {
            default: SlenderPlageEffect;
        };
    }>;
    constructor();
}
