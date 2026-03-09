import { type AbilityEffectsInterface } from '../../../Ability';
import { RoleAbility } from '../../RoleAbility';
export declare class SneakAttack extends RoleAbility {
    static readonly description: string;
    effects: AbilityEffectsInterface;
    constructor();
}
