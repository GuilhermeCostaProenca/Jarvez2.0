import type { Attribute } from '../Sheet/Attributes';
import type { CharacterSheetInterface } from '../Sheet/CharacterSheet/CharacterSheetInterface';
export declare class SpellResistanceDifficultyCalculator {
    static get baseResistanceDifficulty(): number;
    static calculate(sheet: CharacterSheetInterface, spellsAttribute: Attribute): number;
}
