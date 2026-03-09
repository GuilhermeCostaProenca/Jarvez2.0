import { type RaceAbilityMap, type RoleAbilityMap } from '../Map';
import { type RaceAbilityInterface } from '../Race/RaceAbility';
import { type RoleAbilityInterface } from '../Role/RoleAbility';
import { type TranslatableName } from '../Translator';
import { type SheetAbilitiesInterface } from './SheetAbilitiesInterface';
import { type TransactionInterface } from './TransactionInterface';
export declare class SheetAbilities implements SheetAbilitiesInterface {
    private readonly roleAbility;
    private readonly raceAbility;
    constructor(roleAbility?: RoleAbilityMap, raceAbility?: RaceAbilityMap);
    applyRoleAbility(ability: RoleAbilityInterface, transaction: TransactionInterface, source: TranslatableName): void;
    applyRaceAbility(ability: RaceAbilityInterface, transaction: TransactionInterface, source: TranslatableName): void;
    getRoleAbilities(): RoleAbilityMap;
    getRaceAbilities(): RaceAbilityMap;
}
