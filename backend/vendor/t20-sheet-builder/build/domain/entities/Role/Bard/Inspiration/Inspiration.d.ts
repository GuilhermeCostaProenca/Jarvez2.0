import { AbilityEffects } from '../../../Ability';
import { RoleAbility } from '../../RoleAbility';
import { InspirationEffect } from './InspirationEffect';
export declare class Inspiration extends RoleAbility {
    effects: AbilityEffects<{
        activateable: {
            default: InspirationEffect;
        };
    }>;
    constructor();
}
