import { AbilityEffects } from '../../../Ability';
import { RoleAbility } from '../../RoleAbility';
import { BulwarkEffect } from './BulwarkEffect';
export declare class Bulwark extends RoleAbility {
    effects: AbilityEffects<{
        triggered: {
            default: BulwarkEffect;
        };
    }>;
    constructor();
}
