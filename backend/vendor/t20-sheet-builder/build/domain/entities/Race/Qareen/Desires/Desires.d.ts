import { AbilityEffects, RolePlayEffect } from '../../../Ability';
import { RaceAbility } from '../../RaceAbility';
export declare class Desires extends RaceAbility {
    static effectDescription: string;
    effects: AbilityEffects<{
        roleplay: {
            default: RolePlayEffect;
        };
    }>;
    constructor();
}
