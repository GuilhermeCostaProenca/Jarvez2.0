import { AbilityEffects } from '../../../Ability';
import { RoleAbility } from '../../RoleAbility';
import { PrototypeEffect, type PrototypeParams } from './PrototypeEffect';
export declare class Prototype extends RoleAbility {
    effects: AbilityEffects<{
        passive: {
            default: PrototypeEffect;
        };
    }>;
    constructor(params: PrototypeParams);
}
