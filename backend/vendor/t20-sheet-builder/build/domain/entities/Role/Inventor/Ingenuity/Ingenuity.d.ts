import { AbilityEffects } from '../../../Ability';
import { RoleAbility } from '../../RoleAbility';
import { IngenuityEffect } from './IngenuityEffect';
export declare class Ingenuity extends RoleAbility {
    effects: AbilityEffects<{
        triggered: {
            default: IngenuityEffect;
        };
    }>;
    constructor();
}
