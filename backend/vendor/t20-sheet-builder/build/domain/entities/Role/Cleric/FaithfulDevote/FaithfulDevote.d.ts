import { AbilityEffects } from '../../../Ability';
import { RoleAbility } from '../../RoleAbility';
import { RoleAbilityName } from '../../RoleAbilityName';
import { FaithfulDevoteEffect } from './FaithfulDevoteEffect';
export declare class FaithfulDevote extends RoleAbility {
    static readonly abilityName: {
        readonly cleric: RoleAbilityName.clericFaithfulDevote;
        readonly druid: RoleAbilityName.druidFaithfulDevote;
    };
    effects: AbilityEffects<{
        passive: {
            default: FaithfulDevoteEffect;
        };
    }>;
    constructor(role: 'cleric' | 'druid');
}
