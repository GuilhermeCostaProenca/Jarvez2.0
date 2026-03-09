import { type SerializedSheetRaceAbility } from '..';
import type { AbilityInterface } from '../Ability/Ability';
import { Ability } from '../Ability/Ability';
import type { RaceAbilityName } from './RaceAbilityName';
export type RaceAbilityInterface = AbilityInterface & {
    name: RaceAbilityName;
};
export declare abstract class RaceAbility extends Ability implements RaceAbilityInterface {
    readonly name: RaceAbilityName;
    constructor(name: RaceAbilityName);
    serialize(): SerializedSheetRaceAbility;
}
