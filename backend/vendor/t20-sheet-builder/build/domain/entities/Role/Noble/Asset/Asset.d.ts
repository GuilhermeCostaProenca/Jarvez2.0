import { type AbilityEffectsInterface } from '../../../Ability';
import { RoleAbility } from '../../RoleAbility';
export declare class Asset extends RoleAbility {
    static readonly description: string;
    effects: AbilityEffectsInterface;
    constructor();
}
