import type { AbilityType } from '../Ability/Ability';
import { AbilityEffects } from '../Ability/AbilityEffects';
import type { RaceAbilityInterface } from './RaceAbility';
import { RaceAbilityName } from './RaceAbilityName';
export declare class RaceAbilityFake implements RaceAbilityInterface {
    effects: AbilityEffects<{}>;
    name: RaceAbilityName;
    addToSheet: import("vitest").Mock<any, any>;
    abilityType: AbilityType;
}
