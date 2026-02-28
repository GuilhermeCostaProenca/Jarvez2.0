import { AbilityEffects } from '../../../Ability/AbilityEffects';
import { RoleAbility } from '../../RoleAbility';
import { SpecialAttackEffect } from './SpecialAttackEffect';
export declare class SpecialAttack extends RoleAbility {
    effects: AbilityEffects<{
        triggered: {
            default: SpecialAttackEffect;
        };
    }>;
    constructor();
}
