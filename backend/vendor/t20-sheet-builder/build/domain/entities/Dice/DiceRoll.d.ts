import { type RandomInterface } from '../Random';
import type { DiceSides } from './DiceSides';
import { RollResult } from './RollResult';
export type SerializedDiceRoll = {
    diceQuantity: number;
    diceSides: DiceSides;
};
export declare class DiceRoll {
    readonly diceQuantity: number;
    readonly diceSides: DiceSides;
    readonly discardLowestDiceQty: number;
    constructor(diceQuantity: number, diceSides: DiceSides, discardLowestDiceQty?: number);
    serialize(): SerializedDiceRoll;
    roll(random: RandomInterface): RollResult;
    private validateDiceQuantity;
}
