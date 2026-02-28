import { type SerializedSheetRoleAbility } from '..';
import type { AbilityInterface } from '../Ability/Ability';
import { Ability } from '../Ability/Ability';
import type { RoleAbilityName } from './RoleAbilityName';
export type RoleAbilityInterface = AbilityInterface & {
    name: RoleAbilityName;
};
export declare abstract class RoleAbility extends Ability implements RoleAbilityInterface {
    readonly name: RoleAbilityName;
    constructor(name: RoleAbilityName);
    serialize(): SerializedSheetRoleAbility;
}
