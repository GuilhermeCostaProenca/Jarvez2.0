import type { AbilityType } from '../Ability/Ability';
import { AbilityEffects } from '../Ability/AbilityEffects';
import type { RoleAbilityInterface } from './RoleAbility';
import { RoleAbilityName } from './RoleAbilityName';
export declare class RoleAbilityFake implements RoleAbilityInterface {
    effects: AbilityEffects<{}>;
    name: RoleAbilityName;
    addToSheet: import("vitest").Mock<any, any>;
    abilityType: AbilityType;
}
