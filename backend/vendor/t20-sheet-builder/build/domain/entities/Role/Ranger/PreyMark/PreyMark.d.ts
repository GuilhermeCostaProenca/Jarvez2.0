import { AbilityEffects } from '../../../Ability';
import { RoleAbility } from '../../RoleAbility';
import { PreyMarkEffect } from './PreyMarkEffect';
export declare class PreyMark extends RoleAbility {
    effects: AbilityEffects<{
        activateable: {
            default: PreyMarkEffect;
        };
    }>;
    constructor();
}
