import type { Cost, CostType } from './Sheet/CharacterSheet/CharacterSheetInterface';
export type SerializedManaCost = {
    type: CostType;
    value: number;
};
export declare class ManaCost implements Cost {
    readonly value: number;
    type: CostType;
    constructor(value: number);
    serialize(): {
        type: CostType;
        value: number;
    };
}
