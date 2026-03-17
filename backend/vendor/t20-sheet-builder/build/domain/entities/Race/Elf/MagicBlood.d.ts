import { AbilityEffects } from '../../Ability';
import { RaceAbility } from '../RaceAbility';
import { MagicBloodEffect } from './MagicBloodEffect';
export declare class MagicBlood extends RaceAbility {
    effects: AbilityEffects<{
        passive: {
            default: MagicBloodEffect;
        };
    }>;
    constructor();
}
