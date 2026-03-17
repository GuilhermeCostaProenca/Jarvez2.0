import { ActivateableAbilityEffect } from '../../../../Ability/ActivateableAbilityEffect';
import { type Character } from '../../../../Character';
import { type Cost } from '../../../../Sheet/CharacterSheet/CharacterSheetInterface';
import { type GeneralPowerName } from '../../GeneralPowerName';
export declare abstract class FightStyleEffect extends ActivateableAbilityEffect {
    baseCosts: Cost[];
    constructor(source: GeneralPowerName);
    abstract canApply(character: Character): boolean;
}
