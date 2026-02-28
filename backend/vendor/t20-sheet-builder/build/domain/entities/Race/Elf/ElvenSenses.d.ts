import { AbilityEffects } from '../../Ability';
import { RaceAbility } from '../RaceAbility';
import { ElvenSensesEffect } from './ElvenSensesEffect';
export declare class ElvenSenses extends RaceAbility {
    effects: AbilityEffects<{
        passive: {
            default: ElvenSensesEffect;
        };
    }>;
    constructor();
}
