import { AbilityEffects, RolePlayEffect } from '../../../Ability';
import { RoleAbility } from '../../RoleAbility';
export declare class WildEmpathy extends RoleAbility {
    static description: string;
    effects: AbilityEffects<{
        roleplay: {
            default: RolePlayEffect;
        };
    }>;
    constructor();
}
