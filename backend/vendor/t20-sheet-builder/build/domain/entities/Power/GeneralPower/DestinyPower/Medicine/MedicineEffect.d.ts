import { ActivateableAbilityEffect } from '../../../../Ability/ActivateableAbilityEffect';
import type { Cost } from '../../../../Sheet/CharacterSheet/CharacterSheetInterface';
export declare class MedicineEffect extends ActivateableAbilityEffect {
    static readonly description: string;
    description: string;
    baseCosts: Cost[];
    constructor();
}
