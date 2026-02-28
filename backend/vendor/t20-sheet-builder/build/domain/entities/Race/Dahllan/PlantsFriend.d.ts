import { AbilityEffects } from '../../Ability';
import { RaceAbility } from '../RaceAbility';
import { PlantsFriendEffect } from './PlantsFriendEffect';
export declare class PlantsFriend extends RaceAbility {
    effects: AbilityEffects<{
        passive: {
            default: PlantsFriendEffect;
        };
    }>;
    constructor();
}
