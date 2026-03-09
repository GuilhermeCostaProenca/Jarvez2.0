import { AbilityEffects } from '../../Ability';
import { RaceAbility } from '../RaceAbility';
import { GloriennGraceEffect } from './GloriennGraceEffect';
export declare class GloriennGrace extends RaceAbility {
    effects: AbilityEffects<{
        passive: {
            default: GloriennGraceEffect;
        };
    }>;
    constructor();
}
