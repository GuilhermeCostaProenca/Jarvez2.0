import { AbilityEffects } from '../../../Ability';
import { RaceAbility } from '../../RaceAbility';
import { SonOfTormentaEffect } from './SonOfTormentaEffect';
export declare class SonOfTormenta extends RaceAbility {
    effects: AbilityEffects<{
        passive: {
            default: SonOfTormentaEffect;
        };
    }>;
    constructor();
}
