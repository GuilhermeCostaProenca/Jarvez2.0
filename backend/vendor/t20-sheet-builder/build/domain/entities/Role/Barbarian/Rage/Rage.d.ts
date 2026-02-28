import { AbilityEffects } from '../../../Ability';
import { RoleAbility } from '../../RoleAbility';
import { RageEffect } from './RageEffect';
export declare class Rage extends RoleAbility {
    effects: AbilityEffects<{
        activateable: {
            default: RageEffect;
        };
    }>;
    constructor();
}
