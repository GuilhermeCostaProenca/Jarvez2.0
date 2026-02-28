import { AbilityEffects } from '../../../Ability';
import { RoleAbility } from '../../RoleAbility';
import { AudacityEffect } from './AudacityEffect';
export declare class Audacity extends RoleAbility {
    effects: AbilityEffects<{
        triggered: {
            default: AudacityEffect;
        };
    }>;
    constructor();
}
