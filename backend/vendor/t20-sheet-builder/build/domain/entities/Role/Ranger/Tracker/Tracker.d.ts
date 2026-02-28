import { AbilityEffects } from '../../../Ability';
import { RoleAbility } from '../../RoleAbility';
import { TrackerEffect } from './TrackerEffect';
export declare class Tracker extends RoleAbility {
    effects: AbilityEffects<{
        passive: {
            default: TrackerEffect;
        };
    }>;
    constructor();
}
